import Foundation

struct ChatMessage: Identifiable, Equatable {
    enum Role: String { case user, assistant }
    let id = UUID()
    let role: Role
    let content: String
}

enum AsterClientError: Error, LocalizedError {
    case notAuthenticated
    case server(status: Int, body: String)
    case malformedResponse

    var errorDescription: String? {
        switch self {
        case .notAuthenticated:
            return "Not signed in."
        case .server(let status, let body):
            return "Aster returned \(status): \(body)"
        case .malformedResponse:
            return "Aster's response wasn't in the expected shape."
        }
    }
}

/// Talks to Aster's existing OpenAI-compatible /v1/chat/completions
/// endpoint (services/aster-agent/aster_agent.py), authenticated with an
/// Authentik access token instead of the legacy static bearer key.
struct AsterClient {
    let authManager: AuthManager

    func send(history: [ChatMessage]) async throws -> String {
        guard let token = await authManager.validAccessToken() else {
            throw AsterClientError.notAuthenticated
        }

        var request = URLRequest(url: AsterConfig.asterBaseURL.appendingPathComponent("v1/chat/completions"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        // The default 60s URLSession timeout is too tight: a grounded query
        // with preloaded context can legitimately take longer than that on
        // this single-slot backend (docs/reference/Aster-Operations.md cites
        // ~24s for a grounded retrieval baseline, with real headroom above
        // that under load), and a cold/just-started backend can be slower
        // still. Give it real room rather than fail a slow-but-honest answer.
        request.timeoutInterval = 120

        let payload: [String: Any] = [
            "messages": history.map { ["role": $0.role.rawValue, "content": $0.content] },
            "stream": false,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw AsterClientError.malformedResponse
        }
        guard http.statusCode == 200 else {
            throw AsterClientError.server(status: http.statusCode, body: String(data: data, encoding: .utf8) ?? "")
        }

        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let choices = json["choices"] as? [[String: Any]],
            let message = choices.first?["message"] as? [String: Any],
            let content = message["content"] as? String
        else {
            throw AsterClientError.malformedResponse
        }
        return content
    }
}
