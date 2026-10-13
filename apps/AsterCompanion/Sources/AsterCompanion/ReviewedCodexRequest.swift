import Foundation

/// One explicitly reviewed, tool-free question for the supervised local pilot.
struct ReviewedCodexRequest: Encodable {
    let requestId: String
    let text: String
    let cloudConsent = true
    let localOnly = false

    init(text: String, id: UUID = UUID()) throws {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              text.utf8.count <= 16000, !text.contains("\0") else {
            throw AsterClientError.malformedResponse
        }
        self.text = text
        self.requestId = id.uuidString.lowercased()
    }

    var jobID: String { "request-" + requestId }
}
