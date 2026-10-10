import SwiftUI

/// Disabled-by-default native manual candidate. No gateway, tools or automatic routing.
struct LocalCodexManualView: View {
    static let launchFlag = "--aster-local-codex-manual"
    // The bundled bridge checks this exact metadata-only configuration before a send.
    static let approvedManifest = "483062186349703ee472b51323c88fb4ffa1f780ae9ff6f351d4046da4973392"

    @Environment(\.dismiss) private var dismiss
    @State private var pendingID = ""
    @State private var draft = ""
    @State private var reviewed: ReviewedCodexRequest?
    @State private var consent = false
    @State private var preparing = true
    @State private var ready = false
    @State private var running = false
    @State private var canRecover = false
    @State private var canReconcile = false
    @State private var answer: String?
    @State private var message = "Checking local Codex configuration. Nothing is being sent."

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Ask Codex manually").font(.title2)
            Text(verbatim: message)
            Text("One reviewed question at a time. Codex has no Aster tools or chat history here. Your question and answer may remain in your ChatGPT account.")
                .font(.caption)
            if !pendingID.isEmpty {
                Text("Recorded request ID: \(pendingID). This ID will never be sent again automatically.")
                    .font(.caption)
                if let answer {
                    Text("Original answer").font(.headline)
                    ScrollView { Text(verbatim: answer).textSelection(.enabled) }
                        .frame(minHeight: 120, maxHeight: 240)
                    Text("Copy the answer privately if you want to keep it; Aster does not retain its text.")
                        .font(.caption)
                    Button("I have recorded the answer; allow a new question") { acknowledge() }
                        .disabled(running)
                } else if canRecover && !running {
                    Button("Recover original answer") { Task { await recover() } }
                } else if canReconcile && !running {
                    Button("Check original Codex turn") { Task { await reconcile() } }
                }
            } else if let reviewed {
                Text("This is the complete text that will be sent:")
                ScrollView { Text(verbatim: reviewed.text).textSelection(.enabled) }
                    .frame(minHeight: 120, maxHeight: 240)
                Toggle("I reviewed this exact text and agree to send it through my ChatGPT subscription.",
                       isOn: $consent)
                HStack {
                    Button("Edit") { self.reviewed = nil; consent = false }.disabled(running)
                    Button("Send this one reviewed question") { Task { await send(reviewed) } }
                        .disabled(!ready || preparing || !consent || running)
                }
            } else {
                TextEditor(text: $draft).frame(minHeight: 150)
                Text("Do not include passwords, tokens or private material you do not want sent to ChatGPT.")
                    .font(.caption)
                Button("Review question") {
                    do {
                        reviewed = try ReviewedCodexRequest(text: draft)
                        consent = false
                        message = "Review the exact question and cloud destination before sending."
                    } catch {
                        message = "Enter a question of at most 16,000 UTF-8 bytes. Nothing was sent."
                    }
                }.disabled(!ready || preparing)
            }
            Button("Close") { dismiss() }.disabled(running)
        }
        .padding().frame(minWidth: 580, minHeight: 450)
        .task { await preflight() }
    }

    @MainActor private func preflight() async {
        guard ProcessInfo.processInfo.arguments.contains(Self.launchFlag) else {
            message = "Manual Codex is disabled. Nothing can be sent."
            preparing = false
            return
        }
        let state: URL
        do {
            state = try LocalCodexBridgeProcess.privateStateDirectory()
            pendingID = try LocalCodexManualPending.load(in: state) ?? ""
        } catch {
            message = "Private manual record unavailable. New questions are blocked."
            preparing = false
            return
        }
        let savedID = pendingID
        let result = await Task.detached(priority: .userInitiated) {
            savedID.isEmpty ? (try? LocalCodexBridgeProcess.inspectBundled(prepare: true))
                : (try? LocalCodexBridgeProcess.inspectRecoveryBundled())
        }.value
        preparing = false
        guard let result,
              let object = try? JSONSerialization.jsonObject(with: result) as? [String: Any],
              object["inference"] as? Bool == false else {
            message = "Local Codex is unavailable. Nothing was sent or recovered."
            return
        }
        if savedID.isEmpty {
            ready = object["manifest_sha256"] as? String == Self.approvedManifest
            message = ready ? "Enter one question to review." :
                "Local Codex configuration changed. New questions are blocked."
            return
        }
        guard object["recovery_ready"] as? Bool == true else {
            message = "The prior request cannot be reconciled. Do not resend it."
            return
        }
        let raw = await Task.detached(priority: .userInitiated) { () -> Data? in
            try? LocalCodexBridgeProcess.recordedStatus(
                requestID: savedID, stateDirectory: state)
        }.value
        guard pendingID == savedID, let raw,
              let status = try? JSONSerialization.jsonObject(with: raw) as? [String: Any],
              status["id"] as? String == savedID,
              status["recorded"] as? Bool == true else {
            message = "The prior request cannot be reconciled. Do not resend it."
            return
        }
        canRecover = status["state"] as? String == "completed" &&
            status["turn_recorded"] as? Bool == true
        canReconcile = ["running", "unknown", "cancel_requested"]
            .contains(status["state"] as? String ?? "") &&
            status["turn_recorded"] as? Bool == true
        message = canRecover ? "The recorded turn completed. Recover its original answer." :
            canReconcile ? "Outcome uncertain. Check only the original turn; do not resend." :
            "The prior request is unresolved. Do not resend or clear its ID."
    }

    @MainActor private func send(_ request: ReviewedCodexRequest) async {
        guard ready, !preparing, !running, consent, pendingID.isEmpty,
              reviewed?.jobID == request.jobID else { return }
        let state: URL
        do { state = try LocalCodexBridgeProcess.privateStateDirectory() }
        catch {
            message = "Private dispatch journal unavailable. Nothing was sent."
            return
        }
        do {
            try LocalCodexManualPending.claim(in: state, requestID: request.jobID,
                                              manifestSHA256: Self.approvedManifest)
        } catch {
            message = "A private request record could not be saved. Nothing was sent."
            return
        }
        running = true
        consent = false
        pendingID = request.jobID // The private record is durable before helper start.
        message = "Waiting for the original Codex answer. Do not resend this request."
        let approvedHash = Self.approvedManifest
        let raw = await Task.detached(priority: .userInitiated) { () -> Data? in
            try? LocalCodexBridgeProcess.submitBundled(request,
                approvedHash: approvedHash, stateDirectory: state)
        }.value
        running = false
        guard pendingID == request.jobID, let raw,
              let object = try? JSONSerialization.jsonObject(with: raw) as? [String: Any],
              object["id"] as? String == request.jobID,
              object["state"] as? String == "completed",
              object["automatic_retry"] as? Bool == false,
              let text = object["answer"] as? String, !text.isEmpty else {
            message = "Outcome uncertain or unavailable. The request ID is retained; do not resend."
            return
        }
        answer = text
        message = "One Codex turn completed. Record the answer before asking another question."
    }

    @MainActor private func recover() async {
        guard canRecover, !running, !pendingID.isEmpty else { return }
        let id = pendingID
        guard let state = try? LocalCodexBridgeProcess.privateStateDirectory() else {
            message = "Private journal unavailable. Nothing was resent."
            return
        }
        running = true
        let raw = await Task.detached(priority: .userInitiated) { () -> Data? in
            try? LocalCodexBridgeProcess.recoverBundled(requestID: id, stateDirectory: state)
        }.value
        running = false
        guard pendingID == id, let raw,
              let object = try? JSONSerialization.jsonObject(with: raw) as? [String: Any],
              object["id"] as? String == id,
              object["state"] as? String == "completed",
              object["inference"] as? Bool == false,
              object["automatic_retry"] as? Bool == false,
              let text = object["answer"] as? String, !text.isEmpty else {
            message = "Original answer unavailable. Nothing was resent; stop and reconcile."
            return
        }
        answer = text
        canRecover = false
        message = "Original answer recovered from the recorded turn."
    }

    @MainActor private func reconcile() async {
        guard canReconcile, !running, !pendingID.isEmpty else { return }
        let id = pendingID
        guard let state = try? LocalCodexBridgeProcess.privateStateDirectory() else {
            message = "Private journal unavailable. Nothing was resent."
            return
        }
        running = true
        let raw = await Task.detached(priority: .userInitiated) { () -> Data? in
            try? LocalCodexBridgeProcess.reconcileBundled(requestID: id, stateDirectory: state)
        }.value
        running = false
        guard pendingID == id, let raw,
              let object = try? JSONSerialization.jsonObject(with: raw) as? [String: Any],
              object["id"] as? String == id,
              object["state"] as? String == "completed",
              object["inference"] as? Bool == false,
              object["automatic_retry"] as? Bool == false,
              let text = object["answer"] as? String, !text.isEmpty else {
            message = "Original turn is not yet verifiably complete. Nothing was resent."
            return
        }
        answer = text
        canReconcile = false
        message = "Original completed turn verified and reconciled. No new question was sent."
    }

    @MainActor private func acknowledge() {
        guard !running, !pendingID.isEmpty, answer != nil else { return }
        do {
            let state = try LocalCodexBridgeProcess.privateStateDirectory()
            try LocalCodexManualPending.clearCompleted(in: state, requestID: pendingID)
        } catch {
            message = "The completed request could not be cleared. Do not send another."
            return
        }
        pendingID = ""
        answer = nil
        reviewed = nil
        draft = ""
        consent = false
        canRecover = false
        canReconcile = false
        ready = false
        preparing = true
        message = "Checking configuration before another question."
        Task { await preflight() }
    }
}
