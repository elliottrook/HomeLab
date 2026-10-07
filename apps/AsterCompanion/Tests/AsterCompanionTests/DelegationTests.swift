import XCTest
@testable import AsterCompanion

final class DelegationTests: XCTestCase {
    func testUnknownNeverDisplaysUnconfirmedAnswer() throws {
        let raw = #"{"id":"j","state":"unknown","reply":"unconfirmed","message":"Unknown","usage":{"status":"unknown"},"can_request_cancel":false,"recovery_required":false}"#
        let value = try AIPAMCoding.decoder.decode(DelegationSnapshot.self, from: Data(raw.utf8))
        XCTAssertNil(value.visibleAnswer)
        XCTAssertEqual(value.usageText,"Token usage is unavailable.")
    }

    func testCompletedAnswerPreservedAndUsageNotClaimedAsCost() throws {
        let raw = #"{"id":"j","state":"completed","reply":"<b>Literal answer</b>","message":"Done","usage":{"status":"reported","provider_snapshots":{"total":{"totalTokens":12}}},"can_request_cancel":false,"recovery_required":false}"#
        let value = try AIPAMCoding.decoder.decode(DelegationSnapshot.self, from: Data(raw.utf8))
        XCTAssertEqual(value.visibleAnswer,"<b>Literal answer</b>")
        XCTAssertTrue(value.usageText.contains("12 tokens"))
        XCTAssertTrue(value.usageText.contains("not a charge"))
    }
}
