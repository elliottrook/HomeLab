import XCTest
import Security
@testable import AsterCompanion

@MainActor
final class AuthManagerTests: XCTestCase {
    private func expired() -> StoredSession {
        StoredSession(accessToken: "synthetic-old", refreshToken: "synthetic-refresh", expiresAt: .distantPast)
    }
    private func response(_ status: Int = 200, _ body: String = "{\"access_token\":\"synthetic-new\",\"refresh_token\":\"synthetic-rotated\",\"expires_in\":600}") -> (Data, URLResponse) {
        (Data(body.utf8), HTTPURLResponse(url: AsterConfig.tokenEndpoint, statusCode: status, httpVersion: nil, headerFields: nil)!)
    }

    func testNormalSignInExchangesAndPersistsWithoutCompletionCallback() async {
        var calls = 0
        var saved: StoredSession?
        let auth = AuthManager(storage: SessionStorage(load: { nil }, save: { saved = $0; return true }, clear: {}), request: { request in
            calls += 1
            XCTAssertEqual(request.httpMethod, "POST")
            XCTAssertTrue(String(data: request.httpBody!, encoding: .utf8)!.contains("grant_type=authorization_code"))
            return self.response()
        })
        await auth.finishSignIn("synthetic-code", verifier: "synthetic-verifier", attempt: 0)
        XCTAssertEqual(calls, 1)
        XCTAssertTrue(auth.isAuthenticated)
        XCTAssertFalse(auth.isSigningIn)
        XCTAssertEqual(saved?.accessToken, "synthetic-new")
    }

    func testSignInFailureNotifiesOptionalCallerWithoutAuthenticating() async {
        var result: Bool?
        let auth = AuthManager(storage: SessionStorage(load: { nil }, save: { _ in XCTFail("Must not persist rejected login"); return false }, clear: {}), request: { _ in self.response(400, "{}") })
        await auth.finishSignIn("synthetic-code", verifier: "synthetic-verifier", attempt: 0) { result = $0 }
        XCTAssertEqual(result, false)
        XCTAssertFalse(auth.isAuthenticated)
        XCTAssertNotNil(auth.lastError)
    }

    func testConcurrentRequestsRefreshOnlyOnceAndPersistOneCompleteRecord() async {
        var saved = expired()
        var calls = 0
        let auth = AuthManager(storage: SessionStorage(load: { saved }, save: { saved = $0; return true }, clear: {}), request: { _ in
            calls += 1
            try await Task.sleep(for: .milliseconds(30))
            return self.response()
        })
        async let a = auth.validAccessToken()
        async let b = auth.validAccessToken()
        let values = await [a, b]
        XCTAssertEqual(values, ["synthetic-new", "synthetic-new"])
        XCTAssertEqual(calls, 1)
        XCTAssertEqual(saved.refreshToken, "synthetic-rotated")
        XCTAssertGreaterThan(saved.expiresAt, Date())
    }

    func testFailedKeychainWriteKeepsNewSessionAndReportsNonpersistentLogin() async {
        let auth = AuthManager(storage: SessionStorage(load: { self.expired() }, save: { _ in false }, clear: {}), request: { _ in self.response() })
        let first = await auth.validAccessToken()
        let second = await auth.validAccessToken()
        XCTAssertEqual(first, "synthetic-new")
        XCTAssertEqual(second, "synthetic-new")
        XCTAssertTrue(auth.isAuthenticated)
        XCTAssertTrue(auth.lastError?.contains("session only") == true)
    }

    func testTemporaryFailureDoesNotEraseSavedLogin() async {
        var cleared = false
        let auth = AuthManager(storage: SessionStorage(load: { self.expired() }, save: { _ in true }, clear: { cleared = true }), request: { _ in self.response(503, "{}") })
        let token = await auth.validAccessToken()
        XCTAssertNil(token)
        XCTAssertFalse(cleared)
        XCTAssertTrue(auth.isAuthenticated)
    }

    func testRevokedRefreshTokenRequiresLoginOnce() async {
        var cleared = 0
        let auth = AuthManager(storage: SessionStorage(load: { self.expired() }, save: { _ in true }, clear: { cleared += 1 }), request: { _ in self.response(400, "{\"error\":\"invalid_grant\"}") })
        let first = await auth.validAccessToken()
        let second = await auth.validAccessToken()
        XCTAssertNil(first); XCTAssertNil(second)
        XCTAssertFalse(auth.isAuthenticated)
        XCTAssertEqual(cleared, 1)
    }

    func testLogoutDuringRefreshCannotResurrectSession() async {
        var started = false
        var saved = false
        let auth = AuthManager(storage: SessionStorage(load: { self.expired() }, save: { _ in saved = true; return true }, clear: {}), request: { _ in
            started = true
            try? await Task.sleep(for: .milliseconds(100))
            return self.response()
        })
        let task = Task { await auth.validAccessToken() }
        while !started { await Task.yield() }
        auth.logout()
        let result = await task.value
        XCTAssertNil(result)
        XCTAssertFalse(saved)
        XCTAssertFalse(auth.isAuthenticated)
    }

    func testReopeningRestoresValidSessionWithoutNetworkOrBrowser() async {
        let stored = StoredSession(accessToken: "synthetic-valid", refreshToken: "synthetic-refresh", expiresAt: Date().addingTimeInterval(600))
        var calls = 0
        let auth = AuthManager(storage: SessionStorage(load: { stored }, save: { _ in true }, clear: {}), request: { _ in calls += 1; return self.response() })
        let token = await auth.validAccessToken()
        XCTAssertEqual(token, "synthetic-valid")
        XCTAssertEqual(calls, 0)
        XCTAssertTrue(auth.isAuthenticated)
    }

    func testLegacySessionMigrationCreatesNewItemAndKeepsRollback() throws {
        let legacy = StoredSession(accessToken: "synthetic-valid", refreshToken: "synthetic-refresh", expiresAt: .distantFuture)
        let legacyText = String(data: try JSONEncoder().encode(legacy), encoding: .utf8)!
        var items = ["oidc_session_v2": legacyText]
        let storage = SessionStorage.migratingKeychain(
            read: { key in items[key].map(KeychainStore.ReadResult.value) ?? .missing },
            write: { key, value in items[key] = value; return true },
            remove: { _ = items.removeValue(forKey: $0) }
        )
        XCTAssertEqual(storage.load()?.accessToken, "synthetic-valid")
        XCTAssertEqual(items["oidc_session_v3"], legacyText)
        XCTAssertEqual(items["oidc_session_v2"], legacyText)
        storage.clear()
        XCTAssertTrue(items.isEmpty)
    }

    func testActiveSessionReadDoesNotTouchLegacyItem() throws {
        let active = StoredSession(accessToken: "synthetic-active", refreshToken: nil, expiresAt: .distantFuture)
        let text = String(data: try JSONEncoder().encode(active), encoding: .utf8)!
        var reads = [String]()
        let storage = SessionStorage.migratingKeychain(
            read: { key in reads.append(key); return key == "oidc_session_v3" ? .value(text) : .missing },
            write: { _, _ in XCTFail("No migration write after active read"); return false },
            remove: { _ in }
        )
        XCTAssertEqual(storage.load()?.accessToken, "synthetic-active")
        XCTAssertEqual(reads, ["oidc_session_v3"])
    }

    func testDeniedActiveSessionDoesNotFallBackToLegacy() {
        var reads = [String]()
        let storage = SessionStorage.migratingKeychain(
            read: { key in reads.append(key); return .unavailable(errSecAuthFailed) },
            write: { _, _ in XCTFail("No write after denied read"); return false },
            remove: { _ in }
        )
        XCTAssertNil(storage.load())
        XCTAssertEqual(reads, ["oidc_session_v3"])
    }

    func testFreshAuthorizationRequiresMaxAgeZeroWithoutPromptLogin() {
        let fresh = AuthManager.authorizationURL(verifier: "verifier", state: "state", fresh: true)
        let normal = AuthManager.authorizationURL(verifier: "verifier", state: "state", fresh: false)
        let freshItems = URLComponents(url: fresh, resolvingAgainstBaseURL: false)!.queryItems!
        XCTAssertEqual(freshItems.first(where: { $0.name == "max_age" })?.value, "0")
        XCTAssertNil(freshItems.first(where: { $0.name == "prompt" }))
        XCTAssertNil(URLComponents(url: normal, resolvingAgainstBaseURL: false)!.queryItems!.first(where: { $0.name == "max_age" }))
    }

    func testOnlyFreshAuthorizationUsesEphemeralBrowserSession() {
        XCTAssertTrue(AuthManager.prefersEphemeralSession(fresh: true))
        XCTAssertFalse(AuthManager.prefersEphemeralSession(fresh: false))
    }
}
