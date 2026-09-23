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

    /// - Parameters:
    ///   - persona: One of the IDs from `fetchPersonas()` (defaults to the
    ///     server's own "sysadmin" default if never fetched).
    ///   - enabledTools: A further restriction on the persona's own tool
    ///     set, or nil for "every tool the persona allows" - this can only
    ///     narrow, never widen, matching the backend's own enforcement.
    func send(history: [ChatMessage], persona: String = "sysadmin", enabledTools: [String]? = nil) async throws -> String {
        guard let token = await authManager.validAccessToken() else {
            throw AsterClientError.notAuthenticated
        }

        var request = URLRequest(url: AsterConfig.asterBaseURL.appendingPathComponent("v1/chat/completions"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.timeoutInterval = 120

        var payload: [String: Any] = [
            "messages": history.map { ["role": $0.role.rawValue, "content": $0.content] },
            // Streamed (SSE) rather than one non-streamed response: a query
            // that pulls broad knowledge-search context into the prompt
            // (e.g. Sysadmin Aster's search_knowledge tool) can legitimately
            // run well past a minute on this single-slot backend, and a
            // plain JSON response delivers zero bytes until the whole
            // answer is ready - URLSession's timeout can fire waiting for
            // that first byte even while the backend is still working fine.
            // Live-caught 2026-09-22: "tell me about home assistant" under
            // Sysadmin Aster timed out in the app while the narrowly-scoped
            // Home Assistant persona (no tools triggered by that message)
            // answered instantly - not a persona bug, the same class of
            // problem the web client already hit and fixed the same way.
            "stream": true,
            "persona": persona,
        ]
        if let enabledTools {
            payload["enabled_tools"] = enabledTools
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (bytes, response) = try await URLSession.shared.bytes(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw AsterClientError.malformedResponse
        }
        guard http.statusCode == 200 else {
            var body = Data()
            for try await byte in bytes { body.append(byte) }
            throw AsterClientError.server(status: http.statusCode, body: String(data: body, encoding: .utf8) ?? "")
        }

        var replyText = ""
        for try await line in bytes.lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard trimmed.hasPrefix("data:") else { continue }
            let dataText = trimmed.dropFirst(5).trimmingCharacters(in: .whitespaces)
            if dataText == "[DONE]" || dataText.isEmpty { continue }
            guard
                let jsonData = dataText.data(using: .utf8),
                let json = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
                let choices = json["choices"] as? [[String: Any]],
                let delta = choices.first?["delta"] as? [String: Any],
                let content = delta["content"] as? String
            else { continue }
            replyText += content
        }
        return replyText
    }

    /// Fetches the backend's live persona/tool registry (GET
    /// /v1/personas) so the picker and tool checklist never hardcode a
    /// list of their own that could drift from aster_agent.py's PERSONAS.
    func fetchPersonas() async throws -> PersonasResponse {
        guard let token = await authManager.validAccessToken() else {
            throw AsterClientError.notAuthenticated
        }

        var request = URLRequest(url: AsterConfig.asterBaseURL.appendingPathComponent("v1/personas"))
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw AsterClientError.malformedResponse
        }
        guard http.statusCode == 200 else {
            throw AsterClientError.server(status: http.statusCode, body: String(data: data, encoding: .utf8) ?? "")
        }
        return try JSONDecoder().decode(PersonasResponse.self, from: data)
    }

    /// M5's one wired gated action: read-only proposal check (GET
    /// /v1/arr-repair/proposal), independent of any chat turn.
    func fetchArrRepairProposal() async throws -> ArrRepairProposal {
        guard let token = await authManager.validAccessToken() else {
            throw AsterClientError.notAuthenticated
        }

        var request = URLRequest(url: AsterConfig.asterBaseURL.appendingPathComponent("v1/arr-repair/proposal"))
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw AsterClientError.malformedResponse
        }
        guard http.statusCode == 200 else {
            throw AsterClientError.server(status: http.statusCode, body: String(data: data, encoding: .utf8) ?? "")
        }
        return try JSONDecoder().decode(ArrRepairProposal.self, from: data)
    }

    /// Structured execution of exactly the reviewed candidate - never
    /// derived from chat, matching the backend's own separation between
    /// this route and natural-language tool selection.
    func executeArrRepair(candidateRef: String) async throws -> ArrRepairExecutionResult {
        guard let token = await authManager.validAccessToken() else {
            throw AsterClientError.notAuthenticated
        }

        var request = URLRequest(url: AsterConfig.asterBaseURL.appendingPathComponent("v1/arr-repair/execute"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["candidate_ref": candidateRef])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw AsterClientError.malformedResponse
        }
        guard http.statusCode == 200 else {
            throw AsterClientError.server(status: http.statusCode, body: String(data: data, encoding: .utf8) ?? "")
        }
        return try JSONDecoder().decode(ArrRepairExecutionResult.self, from: data)
    }

    /// M6: speech-to-text via the same Authentik token already used for
    /// chat - services/aster-speech/aster_speech.py accepts it directly,
    /// no separate voice login. `audioData` is a raw recorded audio file
    /// (any format ffmpeg/faster-whisper can decode - AVAudioRecorder's
    /// default .m4a is fine).
    func transcribe(audioData: Data) async throws -> String {
        guard let token = await authManager.validAccessToken() else {
            throw AsterClientError.notAuthenticated
        }

        let boundary = "AsterCompanion-\(UUID().uuidString)"
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"voice.m4a\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/m4a\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        var request = URLRequest(url: AsterConfig.asterBaseURL.appendingPathComponent("voice/v1/stt"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw AsterClientError.malformedResponse
        }
        guard http.statusCode == 200 else {
            throw AsterClientError.server(status: http.statusCode, body: String(data: data, encoding: .utf8) ?? "")
        }
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let text = json["text"] as? String
        else {
            throw AsterClientError.malformedResponse
        }
        return text
    }

    /// M6: text-to-speech, returning raw WAV bytes ready for AVAudioPlayer.
    func synthesize(text: String) async throws -> Data {
        guard let token = await authManager.validAccessToken() else {
            throw AsterClientError.notAuthenticated
        }

        var request = URLRequest(url: AsterConfig.asterBaseURL.appendingPathComponent("voice/v1/tts"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["text": text])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw AsterClientError.malformedResponse
        }
        guard http.statusCode == 200 else {
            throw AsterClientError.server(status: http.statusCode, body: String(data: data, encoding: .utf8) ?? "")
        }
        return data
    }
}
