import XCTest
@testable import AsterCompanion

@MainActor
final class AuthManagerTests: XCTestCase {
    private func expired() -> StoredSession {
        StoredSession(accessToken: "synthetic-old", refreshToken: "synthetic-refresh", expiresAt: .distantPast)
    }
    private func response(_ status: Int = 200, _ body: String = "{\"access_token\":\"synthetic-new\",\"refresh_token\":\"synthetic-rotated\",\"expires_in\":600}") -> (Data, URLResponse) {
        (Data(body.utf8), HTTPURLResponse(url: AsterConfig.tokenEndpoint, statusCode: status, httpVersion: nil, headerFields: nil)!)
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
}
