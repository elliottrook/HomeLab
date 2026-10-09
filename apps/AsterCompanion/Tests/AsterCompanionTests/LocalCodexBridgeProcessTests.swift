import Foundation
import XCTest
@testable import AsterCompanion

final class LocalCodexBridgeProcessTests: XCTestCase {
    func testInertAndMetadataModesUseFixedPythonArguments() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
        defer { try? FileManager.default.removeItem(at: directory) }
        let script = directory.appendingPathComponent("fixture.py")
        try "import json,sys\nprint(json.dumps({'arguments':sys.argv[1:],'inference':False}))\n"
            .write(to: script, atomically: true, encoding: .utf8)

        let inert = try JSONSerialization.jsonObject(with: LocalCodexBridgeProcess.inspect(script: script)) as? [String: Any]
        XCTAssertEqual(inert?["arguments"] as? [String], [])
        XCTAssertEqual(inert?["inference"] as? Bool, false)
        let prepared = try JSONSerialization.jsonObject(with: LocalCodexBridgeProcess.inspect(script: script, prepare: true)) as? [String: Any]
        XCTAssertEqual(prepared?["arguments"] as? [String], ["--prepare"])
        XCTAssertEqual(prepared?["inference"] as? Bool, false)
    }

    func testMissingScriptFailsBeforeProcessLaunch() {
        let missing = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        XCTAssertThrowsError(try LocalCodexBridgeProcess.inspect(script: missing))
    }

    func testReviewedTextTravelsOnlyInPrivateStdinFrame() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
        defer { try? FileManager.default.removeItem(at: directory) }
        let script = directory.appendingPathComponent("fixture.py")
        try "import json,os,sys\nframe=json.load(sys.stdin)\nprint(json.dumps({'arguments':sys.argv[1:],'frame':frame,'environment_contains_text':any(frame['text'] in v for v in os.environ.values())}))\n"
            .write(to: script, atomically: true, encoding: .utf8)
        let request = try ReviewedCodexRequest(text: "synthetic-private-fixture")
        let state = directory.appendingPathComponent("private-state")
        let raw = try LocalCodexBridgeProcess.submit(script: script, request: request,
                                                     approvedHash: String(repeating: "a", count: 64),
                                                     stateDirectory: state)
        let result = try XCTUnwrap(JSONSerialization.jsonObject(with: raw) as? [String: Any])
        let arguments = try XCTUnwrap(result["arguments"] as? [String])
        XCTAssertTrue(arguments.contains("--run"))
        XCTAssertFalse(arguments.contains(request.text))
        XCTAssertEqual((result["frame"] as? [String: Any])?["text"] as? String, request.text)
        XCTAssertEqual(result["environment_contains_text"] as? Bool, false)
    }

    func testInvalidManifestHashFailsBeforeLaunch() throws {
        let request = try ReviewedCodexRequest(text: "synthetic")
        let script = FileManager.default.temporaryDirectory.appendingPathComponent("does-not-matter.py")
        let state = FileManager.default.temporaryDirectory.appendingPathComponent("private-state")
        XCTAssertThrowsError(try LocalCodexBridgeProcess.submit(script: script, request: request,
                                                                  approvedHash: "invalid", stateDirectory: state))
    }

    func testOversizedChildOutputIsDrainedAndRejected() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
        defer { try? FileManager.default.removeItem(at: directory) }
        let script = directory.appendingPathComponent("fixture.py")
        try "print('x'*70000)\n".write(to: script, atomically: true, encoding: .utf8)
        XCTAssertThrowsError(try LocalCodexBridgeProcess.inspect(script: script)) { error in
            guard case LocalCodexBridgeProcess.BridgeError.oversized = error else {
                return XCTFail("Expected bounded-output rejection")
            }
        }
    }

    func testHungChildTimesOut() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: false)
        defer { try? FileManager.default.removeItem(at: directory) }
        let script = directory.appendingPathComponent("fixture.py")
        try "import time\ntime.sleep(3)\n".write(to: script, atomically: true, encoding: .utf8)
        XCTAssertThrowsError(try LocalCodexBridgeProcess.inspect(script: script, timeout: 0.1)) { error in
            guard case LocalCodexBridgeProcess.BridgeError.timeout = error else {
                return XCTFail("Expected timeout")
            }
        }
    }

    func testPrivateJournalDirectoryUsesOwnerOnlyPermissions() throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString).resolvingSymlinksInPath()
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false,
                                                attributes: [.posixPermissions: 0o700])
        defer { try? FileManager.default.removeItem(at: root) }
        let state = try LocalCodexBridgeProcess.privateStateDirectory(base: root)
        XCTAssertEqual(state.lastPathComponent, "LocalCodexPilot")
        for directory in [state.deletingLastPathComponent(), state] {
            let attrs = try FileManager.default.attributesOfItem(atPath: directory.path)
            XCTAssertEqual((attrs[.posixPermissions] as? NSNumber)?.intValue, 0o700)
        }
    }

    func testSymlinkedJournalRootIsRejected() throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString).resolvingSymlinksInPath()
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false)
        defer { try? FileManager.default.removeItem(at: root) }
        let link = root.appendingPathComponent("link")
        try FileManager.default.createSymbolicLink(at: link, withDestinationURL: root)
        XCTAssertThrowsError(try LocalCodexBridgeProcess.privateStateDirectory(base: link))
    }
}
