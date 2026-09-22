import XCTest
@testable import AsterCompanion

final class ArrRepairModelsTests: XCTestCase {
    /// Matches the real broker's dry-run shape
    /// (services/aster-arr-broker/proposal.py create_dry_run) as passed
    /// through GET /v1/arr-repair/proposal unchanged.
    func testDecodesRealBrokerDryRunShape() throws {
        let json = """
        {
          "status": "proposal",
          "dry_run": {
            "mode": "dry_run",
            "execution_enabled": false,
            "operation": "dismiss_stale_radarr_queue_record",
            "service": "radarr",
            "candidate_ref": "radarr-q-abcdefghijklmnop",
            "preconditions": [
              "A fresh validated report produced this broker-issued candidate reference."
            ],
            "effect_if_later_enabled": "Remove only the mapped Radarr queue record.",
            "validation": "Re-read the mapped record through the broker.",
            "rollback": "Not reversible.",
            "next_step": "Operator review and a separately approved broker implementation."
          }
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(ArrRepairProposal.self, from: json)
        XCTAssertTrue(decoded.isAvailable)
        XCTAssertEqual(decoded.dryRun?.candidateRef, "radarr-q-abcdefghijklmnop")
        XCTAssertEqual(decoded.dryRun?.preconditions?.count, 1)
        XCTAssertEqual(decoded.dryRun?.rollback, "Not reversible.")
    }

    func testUnavailableProposalIsNotAvailable() throws {
        let json = """
        {"status": "unavailable", "error": "No fresh, report-issued repair candidate is available"}
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(ArrRepairProposal.self, from: json)
        XCTAssertFalse(decoded.isAvailable)
        XCTAssertNil(decoded.dryRun)
    }

    func testDecodesExecutionResult() throws {
        let json = """
        {"status": "completed", "audit": {"result": "dismissed"}}
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(ArrRepairExecutionResult.self, from: json)
        XCTAssertEqual(decoded.status, "completed")
    }
}
