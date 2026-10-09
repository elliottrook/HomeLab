import XCTest
@testable import AsterCompanion

final class CodexRequestTests: XCTestCase {
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
