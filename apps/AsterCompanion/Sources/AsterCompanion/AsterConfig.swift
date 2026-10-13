import Foundation

/// Real values for the live "aster-companion" Authentik application and
/// Aster's production API, matching docs/projects/Aster-Companion-App.md.
/// Not build-time secrets: this is a public OAuth2 client (PKCE, no
/// client secret), so the client_id and endpoints are meant to ship in
/// the app binary.
enum AsterConfig {
    // The composite candidate keeps Codex hidden in normal Companion use.
    // This flag exposes only the reviewed pilot surface for supervised tests.
    static var delegationEnabled: Bool {
        ProcessInfo.processInfo.arguments.contains("--aster-local-codex-manual")
    }
    static let clientID = "aster-companion"
    static let authorizationEndpoint = URL(string: "https://auth.elliottrook.com/application/o/authorize/")!
    static let tokenEndpoint = URL(string: "https://auth.elliottrook.com/application/o/token/")!
    static let redirectURI = "aster-companion://callback"
    static let scope = "openid email profile offline_access"
    static let asterBaseURL = URL(string: "https://aster.elliottrook.com")!
}
