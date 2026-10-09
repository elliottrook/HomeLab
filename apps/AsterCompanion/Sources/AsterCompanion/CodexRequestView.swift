import SwiftUI

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

struct CodexCapabilities: Decodable {
    let submissionEnabled: Bool
    let model: String
    let mode: String
    let tools: Bool
    let maximumUtf8Bytes: Int
    var supported: Bool {
        submissionEnabled && mode == "supervised" && !tools && maximumUtf8Bytes == 16000
    }
}

struct CodexRequestReceipt: Decodable {
    let id: String
    let state: String
    let message: String
    let automaticRetry: Bool
    let contentAvailable: Bool
}

struct CodexRequestView: View {
    @EnvironmentObject private var auth: AuthManager
    @Environment(\.dismiss) private var dismiss
    @AppStorage("aster.codex.pendingRequestID") private var pendingID = ""
    @State private var text = ""
    @State private var reviewed: ReviewedCodexRequest?
    @State private var consent = false
    @State private var capabilities: CodexCapabilities?
    @State private var sending = false
    @State private var error: String?
    let onSubmitted: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Ask Codex through Aster").font(.title2)
            if let error { Text(verbatim: error).foregroundStyle(.red) }
            if !pendingID.isEmpty {
                Text("A request is already recorded. Check its status before sending another.")
                Button("View recorded request") { onSubmitted(pendingID); dismiss() }
            } else if let reviewed {
                Text("This is the complete text that will be sent:")
                ScrollView { Text(verbatim: reviewed.text).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading) }
                Text("No chat history or local system data is added. Codex has no tools in this mode. This question and its answer may remain in Codex history and your account records.").font(.caption)
                Toggle("I agree to send this text to Codex through my ChatGPT account.", isOn: $consent)
                Text("A supervised session must be started before the request can run. Unclaimed requests expire after four minutes.").font(.caption)
                HStack {
                    Button("Edit") { self.reviewed = nil; consent = false }.disabled(sending)
                    Button("Send reviewed request") { Task { await submit(reviewed) } }
                        .disabled(!consent || sending || capabilities?.supported != true)
                }
            } else {
                TextEditor(text: $text).frame(minHeight: 180)
                Text("Type the question you want Codex to answer. Do not include passwords or access tokens.").font(.caption)
                Button("Review request") {
                    do { reviewed = try ReviewedCodexRequest(text: text); consent = false; error = nil }
                    catch { self.error = "Enter a question of at most 16,000 UTF-8 bytes." }
                }.disabled(capabilities?.supported != true)
            }
            if capabilities?.supported != true { Text("New Codex requests are not enabled on Aster.").font(.caption) }
            Button("Close") { dismiss() }.disabled(sending)
        }
        .padding().frame(minWidth: 560, minHeight: 400)
        .task {
            do { capabilities = try await AsterClient(authManager: auth).fetchCodexCapabilities() }
            catch { self.error = "Cannot confirm Codex availability. Nothing has been sent." }
        }
    }

    @MainActor private func submit(_ request: ReviewedCodexRequest) async {
        guard consent, !sending, pendingID.isEmpty, capabilities?.supported == true else { return }
        sending = true
        // Metadata only, saved before network I/O. Never automatically resend.
        pendingID = request.jobID
        do {
            let receipt = try await AsterClient(authManager: auth).submitCodexRequest(request)
            guard receipt.id == request.jobID, !receipt.automaticRetry else { throw AsterClientError.malformedResponse }
            onSubmitted(receipt.id); dismiss()
        } catch {
            self.error = "Submission could not be confirmed. Check the recorded request; do not resend it."
        }
        sending = false
    }
}
