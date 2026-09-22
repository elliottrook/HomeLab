import Foundation

/// Mirrors aster_agent.py's GET /v1/personas response. The client never
/// hardcodes persona IDs or tool names beyond the "sysadmin" fallback used
/// before the first successful fetch - the backend's PERSONAS registry is
/// the single source of truth for what personas exist and what each one
/// is allowed to use.
struct ToolDescriptor: Decodable, Identifiable, Equatable {
    let name: String
    let description: String
    var id: String { name }
}

struct Persona: Decodable, Identifiable, Equatable {
    let id: String
    let label: String
    let tools: [ToolDescriptor]
}

struct PersonasResponse: Decodable {
    let `default`: String
    let personas: [Persona]
}
