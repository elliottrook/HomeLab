import XCTest
@testable import AsterCompanion

final class DelegationTests: XCTestCase {
    func testCompletedMissingAnswerDoesNotSuggestRepeatingWork() throws {
        let raw = #"{"id":"j","state":"completed","reply":null,"message":"Answer needs recovery","usage":{"status":"unknown"},"can_request_cancel":false,"recovery_required":true}"#
        let value = try AIPAMCoding.decoder.decode(DelegationSnapshot.self, from: Data(raw.utf8))
        XCTAssertEqual(value.state, "completed")
        XCTAssertNil(value.visibleAnswer)
        XCTAssertTrue(value.statusMessage.contains("supervised read"))
        XCTAssertTrue(value.statusMessage.contains("Do not resend"))
    }

    func testRecoveryReceiptAndStatusDecodeWithoutAnswerContent() throws {
        let receipt = try AIPAMCoding.decoder.decode(DelegationRecoveryReceipt.self,
            from: Data(#"{"ticket_id":"0123456789abcdef0123456789abcdef","state":"requested","automatic_retry":false}"#.utf8))
        XCTAssertFalse(receipt.automaticRetry)
        let status = try AIPAMCoding.decoder.decode(DelegationRecoveryStatus.self,
            from: Data(#"{"job_id":"j","state":"claimed","expires_at":1234,"automatic_retry":false}"#.utf8))
        XCTAssertEqual(status.jobId, "j")
        XCTAssertEqual(status.state, "claimed")
    }

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
