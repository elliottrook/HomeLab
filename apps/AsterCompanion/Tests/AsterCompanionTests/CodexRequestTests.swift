import XCTest
@testable import AsterCompanion

final class CodexRequestTests: XCTestCase {
    func testClosedAndUnsupportedCapabilitiesNeverPermitSubmission() throws {
        for (enabled, tools) in [(false, false), (true, true)] {
            let raw = "{\"submission_enabled\":\(enabled),\"model\":\"fixture\",\"mode\":\"supervised\",\"tools\":\(tools),\"maximum_utf8_bytes\":16000}"
            let value = try AIPAMCoding.decoder.decode(CodexCapabilities.self, from: Data(raw.utf8))
            XCTAssertFalse(value.supported)
            XCTAssertFalse(value.canRecover)
        }
    }
    func testRecoveryFlagIndependentOfClosedSubmission() throws {
        let raw = #"{"submission_enabled":false,"recovery_enabled":true,"model":"","mode":"supervised","tools":false,"maximum_utf8_bytes":16000}"#
        let value = try AIPAMCoding.decoder.decode(CodexCapabilities.self, from: Data(raw.utf8))
        XCTAssertFalse(value.supported)
        XCTAssertTrue(value.canRecover)
    }
    func testEnabledIntakeDoesNotClaimWorkerReadiness() throws {
        let raw = #"{"submission_enabled":true,"model":"fixture","mode":"supervised","tools":false,"maximum_utf8_bytes":16000,"worker_status":"unknown"}"#
        let value = try AIPAMCoding.decoder.decode(CodexCapabilities.self, from: Data(raw.utf8))
        XCTAssertTrue(value.supported)
        XCTAssertTrue(value.availabilityMessage.contains("not verified"))
    }

    func testOnlyReviewedTextAndConsentAreEncoded() throws {
        let text = "  A question with intentional spacing.\n"
        let request = try ReviewedCodexRequest(text: text)
        let body = try XCTUnwrap(JSONSerialization.jsonObject(with: AIPAMCoding.encoder.encode(request)) as? [String: Any])
        XCTAssertEqual(Set(body.keys), ["request_id", "text", "cloud_consent", "local_only"])
        XCTAssertEqual(body["text"] as? String, text)
        XCTAssertEqual(body["cloud_consent"] as? Bool, true)
        XCTAssertEqual(body["local_only"] as? Bool, false)
        XCTAssertEqual(request.jobID, "request-" + request.requestId)
    }
    func testRejectsEmptyAndOversizeUnicode() {
        XCTAssertThrowsError(try ReviewedCodexRequest(text: " \n"))
        XCTAssertThrowsError(try ReviewedCodexRequest(text: String(repeating: "é", count: 8001)))
        XCTAssertThrowsError(try ReviewedCodexRequest(text: "a\0b"))
    }
}
