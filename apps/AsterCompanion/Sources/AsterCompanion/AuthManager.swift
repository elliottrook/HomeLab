import AuthenticationServices
import AppKit
import CryptoKit
import Foundation

@MainActor
final class AuthManager: NSObject, ObservableObject, ASWebAuthenticationPresentationContextProviding {
    @Published var isAuthenticated = false
    @Published var lastError: String?

    private let accessTokenKey = "access_token"
    private let refreshTokenKey = "refresh_token"
    private let accessTokenExpiryKey = "access_token_expiry"

    private var session: ASWebAuthenticationSession?

    override init() {
        super.init()
        isAuthenticated = KeychainStore.get(accessTokenKey) != nil
    }

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        NSApplication.shared.windows.first ?? ASPresentationAnchor()
    }

    // MARK: - Login

    func login() {
        let verifier = Self.randomURLSafeString(length: 64)
        let challenge = Self.codeChallenge(for: verifier)
        let state = Self.randomURLSafeString(length: 24)

        var components = URLComponents(url: AsterConfig.authorizationEndpoint, resolvingAgainstBaseURL: false)!
        components.queryItems = [
            URLQueryItem(name: "client_id", value: AsterConfig.clientID),
            URLQueryItem(name: "response_type", value: "code"),
            URLQueryItem(name: "redirect_uri", value: AsterConfig.redirectURI),
            URLQueryItem(name: "scope", value: AsterConfig.scope),
            URLQueryItem(name: "code_challenge", value: challenge),
            URLQueryItem(name: "code_challenge_method", value: "S256"),
            URLQueryItem(name: "state", value: state),
        ]

        let session = ASWebAuthenticationSession(
            url: components.url!,
            callbackURLScheme: "aster-companion"
        ) { [weak self] callbackURL, error in
            Task { @MainActor in
                self?.handleCallback(callbackURL: callbackURL, error: error, expectedState: state, verifier: verifier)
            }
        }
        session.presentationContextProvider = self
        session.prefersEphemeralWebBrowserSession = false
        self.session = session
        session.start()
    }

    private func handleCallback(callbackURL: URL?, error: Error?, expectedState: String, verifier: String) {
        if let error {
            lastError = "Login failed: \(error.localizedDescription)"
            return
        }
        guard let callbackURL,
              let components = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false),
              let code = components.queryItems?.first(where: { $0.name == "code" })?.value,
              let returnedState = components.queryItems?.first(where: { $0.name == "state" })?.value
        else {
            lastError = "Login failed: no authorization code returned."
            return
        }
        guard returnedState == expectedState else {
            lastError = "Login failed: state mismatch (possible interception)."
            return
        }
        Task { await exchangeCode(code, verifier: verifier) }
    }

    private func exchangeCode(_ code: String, verifier: String) async {
        var request = URLRequest(url: AsterConfig.tokenEndpoint)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        let body = [
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": AsterConfig.redirectURI,
            "client_id": AsterConfig.clientID,
            "code_verifier": verifier,
        ]
        request.httpBody = Self.formEncode(body).data(using: .utf8)

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
                let text = String(data: data, encoding: .utf8) ?? "(no body)"
                lastError = "Token exchange failed: \(text)"
                return
            }
            let tokens = try JSONDecoder().decode(TokenResponse.self, from: data)
            store(tokens)
            isAuthenticated = true
            lastError = nil
        } catch {
            lastError = "Token exchange failed: \(error.localizedDescription)"
        }
    }

    private func store(_ tokens: TokenResponse) {
        KeychainStore.set(tokens.accessToken, for: accessTokenKey)
        if let refreshToken = tokens.refreshToken {
            KeychainStore.set(refreshToken, for: refreshTokenKey)
        }
        let expiry = Date().addingTimeInterval(TimeInterval(tokens.expiresIn))
        KeychainStore.set(ISO8601DateFormatter().string(from: expiry), for: accessTokenExpiryKey)
    }

    // MARK: - Token access (with silent refresh)

    /// Returns a currently-valid access token, refreshing via the refresh
    /// token first if the stored one has expired. Nil means the caller
    /// needs to prompt for a fresh interactive login.
    func validAccessToken() async -> String? {
        guard let token = KeychainStore.get(accessTokenKey) else { return nil }
        if let expiryString = KeychainStore.get(accessTokenExpiryKey),
           let expiry = ISO8601DateFormatter().date(from: expiryString),
           expiry > Date().addingTimeInterval(30) {
            return token
        }
        return await refresh()
    }

    private func refresh() async -> String? {
        guard let refreshToken = KeychainStore.get(refreshTokenKey) else {
            logout()
            return nil
        }
        var request = URLRequest(url: AsterConfig.tokenEndpoint)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        let body = [
            "grant_type": "refresh_token",
            "refresh_token": refreshToken,
            "client_id": AsterConfig.clientID,
        ]
        request.httpBody = Self.formEncode(body).data(using: .utf8)

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
                logout()
                return nil
            }
            let tokens = try JSONDecoder().decode(TokenResponse.self, from: data)
            store(tokens)
            return tokens.accessToken
        } catch {
            logout()
            return nil
        }
    }

    func logout() {
        KeychainStore.remove(accessTokenKey)
        KeychainStore.remove(refreshTokenKey)
        KeychainStore.remove(accessTokenExpiryKey)
        isAuthenticated = false
    }

    // MARK: - PKCE helpers

    private static func randomURLSafeString(length: Int) -> String {
        var bytes = [UInt8](repeating: 0, count: length)
        _ = SecRandomCopyBytes(kSecRandomDefault, length, &bytes)
        return Data(bytes).base64URLEncodedString()
    }

    private static func codeChallenge(for verifier: String) -> String {
        let digest = SHA256.hash(data: Data(verifier.utf8))
        return Data(digest).base64URLEncodedString()
    }

    private static func formEncode(_ params: [String: String]) -> String {
        params.map { key, value in
            let allowed = CharacterSet.urlQueryAllowed.subtracting(.init(charactersIn: "+&="))
            let encodedValue = value.addingPercentEncoding(withAllowedCharacters: allowed) ?? value
            return "\(key)=\(encodedValue)"
        }.joined(separator: "&")
    }
}

private struct TokenResponse: Decodable {
    let accessToken: String
    let refreshToken: String?
    let expiresIn: Int

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
    }
}

private extension Data {
    func base64URLEncodedString() -> String {
        base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
}
