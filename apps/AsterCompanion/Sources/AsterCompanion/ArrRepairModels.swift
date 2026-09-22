import Foundation

/// Mirrors aster_agent.py's ARR-repair shape (GET /v1/arr-repair/proposal,
/// POST /v1/arr-repair/execute) - the one gated action wired into the app
/// per M5. The broker's own dry-run fields (preconditions, rollback, etc.)
/// are surfaced verbatim rather than re-described, so review here matches
/// what's actually enforced server-side.
struct ArrRepairDryRun: Decodable {
    let operation: String?
    let service: String?
    let candidateRef: String?
    let preconditions: [String]?
    let effectIfLaterEnabled: String?
    let rollback: String?

    enum CodingKeys: String, CodingKey {
        case operation, service, preconditions, rollback
        case candidateRef = "candidate_ref"
        case effectIfLaterEnabled = "effect_if_later_enabled"
    }
}

struct ArrRepairProposal: Decodable {
    let status: String
    let dryRun: ArrRepairDryRun?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case status, error
        case dryRun = "dry_run"
    }

    var isAvailable: Bool { status == "proposal" && dryRun != nil }
}

struct ArrRepairExecutionResult: Decodable {
    let status: String
}
