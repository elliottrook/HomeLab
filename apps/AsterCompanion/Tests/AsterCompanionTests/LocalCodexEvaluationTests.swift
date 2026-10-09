import XCTest
import Foundation
@testable import AsterCompanion

final class LocalCodexEvaluationTests: XCTestCase {
    func testFiniteFictionalCorpusAndPinnedManifest() {
        let items = LocalCodexEvaluationView.questions
        XCTAssertEqual(items.count, 12)
        XCTAssertEqual(Set(items.map(\.kind)).count, 12)
        XCTAssertTrue(items.allSatisfy { !$0.text.isEmpty && $0.text.utf8.count <= 16_000 })
        XCTAssertEqual(LocalCodexEvaluationView.approvedManifest.count, 64)
        XCTAssertNotEqual(LocalCodexEvaluationView.launchFlag, LocalCodexPilotView.launchFlag)
    }

    func testPrivateEvaluationLogStoresMetadataOnly() throws {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString).resolvingSymlinksInPath()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false,
                                                attributes: [.posixPermissions: 0o700])
        defer { try? FileManager.default.removeItem(at: directory) }
        let id = "request-12345678-1234-1234-1234-123456789abc"
        try LocalCodexEvaluationLog.append(in: directory, requestID: id, caseIndex: 0,
            event: "submitted", manifestSHA256: LocalCodexEvaluationView.approvedManifest)
        try LocalCodexEvaluationLog.append(in: directory, requestID: id, caseIndex: 0,
            event: "completed", manifestSHA256: LocalCodexEvaluationView.approvedManifest,
            totalSeconds: 4.2, turnSeconds: 3.1)
        let file = directory.appendingPathComponent("evaluation-events.jsonl")
        let raw = try String(contentsOf: file, encoding: .utf8)
        let rows = try raw.split(separator: "\n").map {
            try JSONSerialization.jsonObject(with: Data($0.utf8)) as! [String: Any]
        }
        XCTAssertEqual(rows.map { $0["event"] as? String }, ["submitted", "completed"])
        XCTAssertEqual(rows[1]["totalSeconds"] as? Double, 4.2)
        XCTAssertFalse(raw.contains("answer"))
        XCTAssertFalse(raw.contains("question"))
        let mode = try FileManager.default.attributesOfItem(atPath: file.path)[.posixPermissions] as? NSNumber
        XCTAssertEqual(mode?.intValue, 0o600)
    }

    func testEvaluationLogRefusesSymlinkDirectory() throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString).resolvingSymlinksInPath()
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false,
                                                attributes: [.posixPermissions: 0o700])
        defer { try? FileManager.default.removeItem(at: root) }
        let link = root.appendingPathComponent("alias")
        try FileManager.default.createSymbolicLink(at: link, withDestinationURL: root)
        XCTAssertThrowsError(try LocalCodexEvaluationLog.append(in: link,
            requestID: "request-12345678-1234-1234-1234-123456789abc", caseIndex: 0,
            event: "submitted", manifestSHA256: LocalCodexEvaluationView.approvedManifest))
    }
}
