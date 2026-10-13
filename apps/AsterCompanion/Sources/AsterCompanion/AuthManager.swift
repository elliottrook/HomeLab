import AuthenticationServices
import AppKit
import Foundation
import OSLog

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
    private let logger = Logger(subsystem: "com.elliottrook.aster-companion", category: "authentication")
    @Published var isAuthenticated = false
    @Published private(set) var isSigningIn = false
    @Published var lastError: String?

    private let storage: SessionStorage
    private let request: (URLRequest) async throws -> (Data, URLResponse)
    private var tokens: StoredSession?
    private var session: ASWebAuthenticationSession?
    private var refreshTask: Task<String?, Never>?
    private var generation = 0
    private var pendingVerifier: String?
    private var pendingState: String?
    private var pendingAttempt: Int?
    private var signInTimeoutWorkItem: DispatchWorkItem?

    init(storage: SessionStorage? = nil,
         request: @escaping (URLRequest) async throws -> (Data, URLResponse) = {
             let configuration = URLSessionConfiguration.ephemeral
             configuration.waitsForConnectivity = false
             configuration.timeoutIntervalForRequest = 15
             configuration.timeoutIntervalForResource = 20
             return try await URLSession(configuration: configuration).data(for: $0)
         }) {
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
        pendingVerifier = verifier
        pendingState = state
        pendingAttempt = attempt
        signInTimeoutWorkItem?.cancel()
        let timeout = DispatchWorkItem { [weak self] in
            guard let self,
                  self.generation == attempt, self.pendingAttempt == attempt,
                  self.isSigningIn else { return }
            self.session?.cancel()
            self.session = nil
            self.pendingVerifier = nil
            self.pendingState = nil
            self.pendingAttempt = nil
            self.isSigningIn = false
            self.lastError = "No sign-in callback was received. Try again, keeping Aster in the foreground."
        }
        signInTimeoutWorkItem = timeout
        DispatchQueue.main.asyncAfter(deadline: .now() + 45, execute: timeout)
        let authorizationURL = Self.authorizationURL(verifier: verifier, state: state, fresh: fresh)
        logger.info("sign-in started fresh=\(fresh, privacy: .public)")
        let session = ASWebAuthenticationSession(url: authorizationURL, callbackURLScheme: "aster-companion") { [weak self] url, error in
            DispatchQueue.main.async { [weak self] in
                guard let self, self.generation == attempt else { return }
                guard self.pendingAttempt == attempt else { return }
                let errorStatus = error == nil ? "none" : "present"
                self.logger.info("ASWeb callback received url=\(self.callbackDescription(url), privacy: .public) error=\(errorStatus, privacy: .public)")
                self.completeCallback(url: url, error: error, verifier: verifier, state: state, attempt: attempt, completion: completion)
            }
        }
        session.presentationContextProvider = self
        // A privileged AI-PAM action must not inherit Authentik's existing
        // browser cookie. Authentik can otherwise return immediately with a
        // token carrying the old auth_time, which the broker correctly rejects
        // as stale. Normal sign-in keeps the shared session for convenience.
        session.prefersEphemeralWebBrowserSession = Self.prefersEphemeralSession(fresh: fresh)
        self.session = session
        if !session.start() {
            self.session = nil
            isSigningIn = false
            lastError = "The system sign-in window could not start. Try again with Aster in the foreground."
            completion?(false)
        }
    }

    /// macOS can route a custom URL through SwiftUI's scene layer instead of
    /// delivering it to ASWebAuthenticationSession's closure, especially when
    /// an ad-hoc signed bundle has just been moved into /Applications. Keep a
    /// single guarded completion path so either delivery mechanism is safe.
    func handleOpenURL(_ url: URL) {
        logger.info("application URL received \(self.callbackDescription(url), privacy: .public)")
        guard let verifier = pendingVerifier,
              let state = pendingState,
              let attempt = pendingAttempt,
              generation == attempt else { return }
        completeCallback(url: url, error: nil, verifier: verifier, state: state, attempt: attempt, completion: nil)
    }

    private func completeCallback(
        url: URL?, error: Error?, verifier: String, state: String, attempt: Int,
        completion: (@MainActor (Bool) -> Void)?
    ) {
        guard pendingAttempt == attempt else { return }
        signInTimeoutWorkItem?.cancel()
        signInTimeoutWorkItem = nil
        pendingVerifier = nil
        pendingState = nil
        pendingAttempt = nil
        session = nil
        guard error == nil else {
            logger.error("sign-in callback returned an authentication error")
            isSigningIn = false
            lastError = "Sign-in was cancelled or could not finish. Try again."
            completion?(false)
            return
        }
        guard let url, url.scheme == "aster-companion", url.host == "callback",
              let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems,
              items.first(where: { $0.name == "state" })?.value == state,
              let code = items.first(where: { $0.name == "code" })?.value else {
            logger.error("sign-in callback failed validation url=\(self.callbackDescription(url), privacy: .public)")
            isSigningIn = false
            lastError = "Sign-in returned an invalid callback. Please try again."
            completion?(false)
            return
        }
        Task { @MainActor in
            self.logger.info("sign-in callback validated; exchanging authorization code")
            await self.finishSignIn(code: code, verifier: verifier, attempt: attempt, completion: completion)
        }
    }

    func finishSignIn(code: String, verifier: String, attempt: Int,
                      completion: (@MainActor (Bool) -> Void)? = nil) async {
        let success = await exchangeCode(code, verifier: verifier, attempt: attempt)
        completion?(success)
    }

    private func callbackDescription(_ url: URL?) -> String {
        guard let url else { return "nil" }
        let names = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems?.map(\.name).sorted().joined(separator: ",") ?? ""
        let scheme = url.scheme ?? ""
        let host = url.host ?? ""
        return "scheme=\(scheme) host=\(host) path=\(url.path) queryNames=[\(names)]"
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

    static func prefersEphemeralSession(fresh: Bool) -> Bool { fresh }

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
            logger.info("token exchange request started")
            let (data, response) = try await request(tokenRequest([
                "grant_type": "authorization_code", "code": code, "redirect_uri": AsterConfig.redirectURI,
                "client_id": AsterConfig.clientID, "code_verifier": verifier,
            ]))
            guard generation == attempt else { return false }
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
            logger.info("token exchange response status=\(statusCode, privacy: .public) bytes=\(data.count, privacy: .public)")
            guard statusCode == 200 else {
                lastError = "Sign-in could not be completed by the identity service. Please try again."
                return false
            }
            logger.info("token response decoded; saving session")
            try accept(JSONDecoder().decode(TokenResponse.self, from: data), previousRefresh: nil)
            logger.info("session save completed")
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
        let saved = storage.save(value)
        logger.info("keychain save result=\(saved, privacy: .public)")
        lastError = saved ? nil : "Signed in for this session only: Keychain could not save your login. Allow Aster access if macOS asks."
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
        pendingVerifier = nil
        pendingState = nil
        pendingAttempt = nil
        refreshTask?.cancel()
        refreshTask = nil
        signInTimeoutWorkItem?.cancel()
        signInTimeoutWorkItem = nil
        storage.clear()
        tokens = nil
        isAuthenticated = false
        isSigningIn = false
        lastError = nil
    }

    func cancelLogin() {
        guard isSigningIn else { return }
        generation += 1
        session?.cancel()
        session = nil
        pendingVerifier = nil
        pendingState = nil
        pendingAttempt = nil
        signInTimeoutWorkItem?.cancel()
        signInTimeoutWorkItem = nil
        isSigningIn = false
        lastError = "Sign-in cancelled."
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
