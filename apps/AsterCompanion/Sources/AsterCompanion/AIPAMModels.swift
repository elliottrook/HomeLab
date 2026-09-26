import Foundation

struct AIPAMDisplay: Codable, Equatable {
    let reason: String?
    let target: String?
    let effect: String?
    let rollback: String?
}

struct AIPAMPendingApproval: Codable, Identifiable, Equatable {
    let requestId: String
    let agentId: String
    let capability: String
    let riskClass: String
    let payloadHash: String
    let createdAt: Double
    let expiresAt: Double
    let display: AIPAMDisplay

    var id: String { requestId }
    var requiresFreshAuthentication: Bool { riskClass == "red" }
}

struct AIPAMCapability: Codable, Identifiable, Equatable {
    let capability: String
    let riskClass: String
    let serviceId: String
    var id: String { capability }
}

struct AIPAMAgent: Codable, Identifiable, Equatable {
    let agentId: String
    let unixUid: Int
    let state: String
    let createdAt: Double
    let capabilityCount: Int
    let capabilities: [AIPAMCapability]
    var id: String { agentId }
}

struct AIPAMService: Codable, Identifiable, Equatable {
    let serviceId: String
    let executionMode: String
    let enabled: Int
    let createdAt: Double
    let credentialType: String
    let custodyIdentifier: String
    let credentialScope: String
    let rotationDue: String
    let revocationMethod: String
    let health: String
    let capabilityCount: Int
    var id: String { serviceId }
    var isEnabled: Bool { enabled != 0 }
}

struct AIPAMActiveRequest: Codable, Identifiable, Equatable {
    let requestId: String
    let agentId: String
    let capability: String
    let riskClass: String
    let status: String
    let createdAt: Double
    let expiresAt: Double
    var id: String { requestId }
}

struct AIPAMSnapshot: Codable, Equatable {
    let globalEnabled: Bool
    let agents: [AIPAMAgent]
    let services: [AIPAMService]
    let activeRequests: [AIPAMActiveRequest]
}

struct AIPAMHistoryItem: Codable, Identifiable, Equatable {
    let requestId: String
    let agentId: String
    let capability: String
    let riskClass: String
    let payloadHash: String
    let status: String
    let createdAt: Double
    let expiresAt: Double
    let approvedAt: Double?
    let consumedAt: Double?
    let revokedAt: Double?
    let approvalActor: String?
    let approvalAuthTime: Int?
    let approvalAssurance: String?
    let display: AIPAMDisplay
    var id: String { requestId }
}

struct AIPAMAuditItem: Codable, Identifiable, Equatable {
    let sequence: Int
    let occurredAt: Double
    let event: String
    let actor: String
    let outcome: String
    let requestId: String?
    let capability: String?
    let riskClass: String?
    let payloadHash: String?
    var id: Int { sequence }
}

struct AIPAMManagementAction: Encodable, Equatable {
    let action: String
    var target: String? = nil
    var state: String? = nil
    var enabled: Bool? = nil
}

struct AIPAMActionResult: Decodable, Equatable {
    let status: String?
    let enabled: Bool?
}

enum AIPAMCoding {
    static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return encoder
    }()
}
