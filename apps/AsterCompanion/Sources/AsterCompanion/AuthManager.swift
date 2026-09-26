import AuthenticationServices
import AppKit
import Foundation

struct StoredSession: Codable {
    let accessToken: String
    let refreshToken: String?
    let expiresAt: Date
}

@MainActor
struct SessionStorage {
    var load: () -> StoredSession?
    var save: (StoredSession) -> Bool
    var clear: () -> Void

    static let keychain = SessionStorage(
        load: {
            guard let text = KeychainStore.get("oidc_session_v2"), let data = text.data(using: .utf8) else { return nil }
            return try? JSONDecoder().decode(StoredSession.self, from: data)
        },
        save: { session in
            guard let data = try? JSONEncoder().encode(session), let text = String(data: data, encoding: .utf8),
                  KeychainStore.set(text, for: "oidc_session_v2") else { return false }
            return KeychainStore.get("oidc_session_v2") == text
        },
        clear: { KeychainStore.remove("oidc_session_v2") }
    )
}

@MainActor
final class AuthManager: NSObject, ObservableObject, ASWebAuthenticationPresentationContextProviding {
    @Published var isAuthenticated = false
    @Published private(set) var isSigningIn = false
    @Published var lastError: String?

    private let storage: SessionStorage
    private let request: (URLRequest) async throws -> (Data, URLResponse)
    private var tokens: StoredSession?
    private var session: ASWebAuthenticationSession?
    private var refreshTask: Task<String?, Never>?
    private var generation = 0

    init(storage: SessionStorage? = nil,
         request: @escaping (URLRequest) async throws -> (Data, URLResponse) = { try await URLSession.shared.data(for: $0) }) {
        self.storage = storage ?? .keychain
        self.request = request
        super.init()
        tokens = self.storage.load()
        isAuthenticated = tokens != nil
    }

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        NSApplication.shared.windows.first ?? ASPresentationAnchor()
    }

    func login(fresh: Bool = false, completion: (@MainActor (Bool) -> Void)? = nil) {
        guard !isSigningIn else { return }
        generation += 1
        let attempt = generation
        refreshTask?.cancel()
        refreshTask = nil
        isSigningIn = true
        lastError = nil
        let verifier = PKCE.randomURLSafeString(length: 64)
        let state = PKCE.randomURLSafeString(length: 24)
        let authorizationURL = Self.authorizationURL(verifier: verifier, state: state, fresh: fresh)
        let session = ASWebAuthenticationSession(url: authorizationURL, callbackURLScheme: "aster-companion") { [weak self] url, error in
            Task { @MainActor in
                guard let self, self.generation == attempt else { return }
                self.session = nil
                guard error == nil else {
                    self.isSigningIn = false
                    self.lastError = "Sign-in was cancelled or could not finish. Try again."
                    completion?(false)
                    return
                }
                guard let url, url.scheme == "aster-companion", url.host == "callback",
                      let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems,
                      items.first(where: { $0.name == "state" })?.value == state,
                      let code = items.first(where: { $0.name == "code" })?.value else {
                    self.isSigningIn = false
                    self.lastError = "Sign-in returned an invalid callback. Please try again."
                    completion?(false)
                    return
                }
                completion?(await self.exchangeCode(code, verifier: verifier, attempt: attempt))
            }
        }
        session.presentationContextProvider = self
        session.prefersEphemeralWebBrowserSession = false
        self.session = session
        if !session.start() {
            self.session = nil
            isSigningIn = false
            lastError = "The system sign-in window could not start. Try again with Aster in the foreground."
            completion?(false)
        }
    }

    static func authorizationURL(verifier: String, state: String, fresh: Bool) -> URL {
        var components = URLComponents(url: AsterConfig.authorizationEndpoint, resolvingAgainstBaseURL: false)!
        components.queryItems = [
            URLQueryItem(name: "client_id", value: AsterConfig.clientID),
            URLQueryItem(name: "response_type", value: "code"),
            URLQueryItem(name: "redirect_uri", value: AsterConfig.redirectURI),
            URLQueryItem(name: "scope", value: AsterConfig.scope),
            URLQueryItem(name: "code_challenge", value: PKCE.codeChallenge(for: verifier)),
            URLQueryItem(name: "code_challenge_method", value: "S256"),
            URLQueryItem(name: "state", value: state),
        ]
        if fresh { components.queryItems?.append(URLQueryItem(name: "max_age", value: "0")) }
        return components.url!
    }

    private func tokenRequest(_ parameters: [String: String]) -> URLRequest {
        var result = URLRequest(url: AsterConfig.tokenEndpoint)
        result.httpMethod = "POST"
        result.timeoutInterval = 30
        result.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        result.httpBody = Self.formEncode(parameters).data(using: .utf8)
        return result
    }

    private func exchangeCode(_ code: String, verifier: String, attempt: Int) async -> Bool {
        defer { if generation == attempt { isSigningIn = false } }
        do {
            let (data, response) = try await request(tokenRequest([
                "grant_type": "authorization_code", "code": code, "redirect_uri": AsterConfig.redirectURI,
                "client_id": AsterConfig.clientID, "code_verifier": verifier,
            ]))
            guard generation == attempt else { return false }
            guard (response as? HTTPURLResponse)?.statusCode == 200 else {
                lastError = "Sign-in could not be completed by the identity service. Please try again."
                return false
            }
            try accept(JSONDecoder().decode(TokenResponse.self, from: data), previousRefresh: nil)
            return true
        } catch {
            if generation == attempt { lastError = "Sign-in could not finish. Check the connection and try again." }
            return false
        }
    }

    private func accept(_ response: TokenResponse, previousRefresh: String?) throws {
        guard !response.accessToken.isEmpty, response.expiresIn > 0 else { throw URLError(.badServerResponse) }
        let value = StoredSession(accessToken: response.accessToken, refreshToken: response.refreshToken ?? previousRefresh,
                                  expiresAt: Date().addingTimeInterval(TimeInterval(response.expiresIn)))
        // Use the just-issued token in memory; never reread an older partial set.
        // Persist all fields atomically and explicitly report a storage failure.
        tokens = value
        isAuthenticated = true
        lastError = storage.save(value) ? nil : "Signed in for this session only: Keychain could not save your login. Allow Aster access if macOS asks."
    }

    func validAccessToken() async -> String? {
        guard let tokens else { return nil }
        if tokens.expiresAt > Date().addingTimeInterval(30) { return tokens.accessToken }
        if let refreshTask { return await refreshTask.value }
        let attempt = generation
        let task = Task { await self.refresh(attempt: attempt) }
        refreshTask = task
        let result = await task.value
        if generation == attempt { refreshTask = nil }
        return result
    }

    private func refresh(attempt: Int) async -> String? {
        guard let refreshToken = tokens?.refreshToken else {
            logout()
            lastError = "Your session expired. Sign in again with your passkey."
            return nil
        }
        do {
            let (data, response) = try await request(tokenRequest([
                "grant_type": "refresh_token", "refresh_token": refreshToken, "client_id": AsterConfig.clientID,
            ]))
            guard generation == attempt, !Task.isCancelled else { return nil }
            guard let http = response as? HTTPURLResponse else { return nil }
            guard http.statusCode == 200 else {
                let errorCode = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["error"] as? String
                if (http.statusCode == 400 || http.statusCode == 401) && errorCode == "invalid_grant" {
                    logout()
                    lastError = "Your session expired or was revoked. Sign in again with your passkey."
                } else {
                    lastError = "Could not renew your session. Your saved login is retained; try again shortly."
                }
                return nil
            }
            try accept(JSONDecoder().decode(TokenResponse.self, from: data), previousRefresh: refreshToken)
            return tokens?.accessToken
        } catch {
            if generation == attempt { lastError = "Could not reach the sign-in service. Your saved login is retained." }
            return nil
        }
    }

    func logout() {
        generation += 1
        session?.cancel()
        session = nil
        refreshTask?.cancel()
        refreshTask = nil
        storage.clear()
        tokens = nil
        isAuthenticated = false
        isSigningIn = false
        lastError = nil
    }

    private static func formEncode(_ params: [String: String]) -> String {
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-._~"))
        return params.map { key, value in
            "\(key)=\(value.addingPercentEncoding(withAllowedCharacters: allowed) ?? "")"
        }.joined(separator: "&")
    }
}

private struct TokenResponse: Decodable {
    let accessToken: String
    let refreshToken: String?
    let expiresIn: Int
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token", refreshToken = "refresh_token", expiresIn = "expires_in"
    }
}
