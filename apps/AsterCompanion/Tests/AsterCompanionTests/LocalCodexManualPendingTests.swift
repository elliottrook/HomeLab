import Foundation
import XCTest
@testable import AsterCompanion

final class LocalCodexManualPendingTests: XCTestCase {
    private let requestID = "request-12345678-1234-1234-1234-123456789abc"
    private let manifest = String(repeating: "a", count: 64)

    func testClaimSurvivesReopenAndBlocksSecondSendUntilCompletedAcknowledgement() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false,
                                                attributes: [.posixPermissions: 0o700])
        defer { try? FileManager.default.removeItem(at: root) }
        XCTAssertNil(try LocalCodexManualPending.load(in: root))
        try LocalCodexManualPending.claim(in: root, requestID: requestID,
                                         manifestSHA256: manifest)
        XCTAssertEqual(try LocalCodexManualPending.load(in: root), requestID)
        XCTAssertThrowsError(try LocalCodexManualPending.claim(in: root,
            requestID: "request-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            manifestSHA256: manifest))
        XCTAssertThrowsError(try LocalCodexManualPending.clearAcknowledgedTerminal(in: root,
            requestID: "request-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        try LocalCodexManualPending.clearAcknowledgedTerminal(in: root, requestID: requestID)
        XCTAssertNil(try LocalCodexManualPending.load(in: root))
    }

    func testMalformedOrSymlinkedPendingRecordFailsClosed() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false,
                                                attributes: [.posixPermissions: 0o700])
        defer { try? FileManager.default.removeItem(at: root) }
        let record = root.appendingPathComponent("manual-pending.json")
        try "bad".write(to: record, atomically: true, encoding: .utf8)
        XCTAssertThrowsError(try LocalCodexManualPending.load(in: root))
        try FileManager.default.removeItem(at: record)
        let target = root.appendingPathComponent("other")
        try "bad".write(to: target, atomically: true, encoding: .utf8)
        try FileManager.default.createSymbolicLink(at: record, withDestinationURL: target)
        XCTAssertThrowsError(try LocalCodexManualPending.load(in: root))
        XCTAssertThrowsError(try LocalCodexManualPending.claim(in: root,
            requestID: requestID, manifestSHA256: manifest))
    }

    func testOnlyRecordedBoundTerminalFailureCanBeAcknowledged() {
        let base: [String: Any] = ["id": requestID, "recorded": true,
                                   "turn_recorded": true, "state": "failed"]
        XCTAssertEqual(LocalCodexManualView.confirmedFailure(base, requestID: requestID), "failed")
        var stopped = base
        stopped["state"] = "interrupted"
        XCTAssertEqual(LocalCodexManualView.confirmedFailure(stopped, requestID: requestID), "interrupted")
        for state in ["unknown", "running", "completed", "dispatch_unknown"] {
            var unresolved = base
            unresolved["state"] = state
            XCTAssertNil(LocalCodexManualView.confirmedFailure(unresolved, requestID: requestID))
        }
        var noTurn = base
        noTurn["turn_recorded"] = false
        XCTAssertNil(LocalCodexManualView.confirmedFailure(noTurn, requestID: requestID))
        XCTAssertNil(LocalCodexManualView.confirmedFailure(base,
            requestID: "request-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    }

    func testFailureMessageRequiresBoundFinalRecordAndUsesOnlyKnownCategories() {
        let base: [String: Any] = ["id": requestID, "recorded": true,
                                   "turn_recorded": true, "state": "failed",
                                   "failure_class": "subscription_limit"]
        XCTAssertTrue(LocalCodexManualView.confirmedFailureMessage(base,
            requestID: requestID).contains("subscription limit"))
        var unexpected = base
        unexpected["failure_class"] = "private provider error"
        XCTAssertEqual(LocalCodexManualView.confirmedFailureMessage(unexpected,
            requestID: requestID),
            "Codex recorded a final failure. Nothing will be retried automatically.")
        XCTAssertEqual(LocalCodexManualView.confirmedFailureMessage(base,
            requestID: "request-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            "A final failure cannot be verified. Do not resend this request.")
    }
}
