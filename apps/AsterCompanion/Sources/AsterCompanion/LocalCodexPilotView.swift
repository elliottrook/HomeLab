import SwiftUI

/// Uninstalled, fixed-fixture comparison candidate. Requires an explicit
/// launch argument; no normal Companion screen exposes this by default.
struct LocalCodexPilotView: View {
    static let launchFlag = "--aster-local-codex-pilot"
    static let approvedManifest = "f5f072f6d7395d0b9b77775155239d87e913c38f2adb6acb6b0e1122c5101cd0"
    static let fixture = "Fictional exercise only. Service Orion returned HTTP 503 once. A later health check returned HTTP 200. No logs, dependency checks or user-path checks have been performed. Explain what is known, what remains unknown, and the next read-only checks. Do not claim you inspected or repaired anything. Use only this supplied information. Do not use tools."

    @Environment(\.dismiss) private var dismiss
    @AppStorage("aster.codex.localPilot.pendingRequestID") private var pendingID = ""
    @State private var ready = false
    @State private var preparing = true
    @State private var consent = false
    @State private var running = false
    @State private var answer: String?
    @State private var message = "Checking local Codex configuration. No question is being sent."

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Local Codex comparison pilot").font(.title2)
            Text(verbatim: message)
            Text("Only this fictional question can be sent. Codex has no Aster infrastructure tools in this pilot; its own account may retain the question and answer.").font(.caption)
            ScrollView { Text(verbatim: Self.fixture).textSelection(.enabled) }
                .frame(maxHeight: 170)
            if let answer {
                Text("Original answer").font(.headline)
                ScrollView { Text(verbatim: answer).textSelection(.enabled) }
                    .frame(maxHeight: 220)
                Text("Copy this answer now if you want to keep it. Aster stores only the request ID; it does not retain the answer.").font(.caption)
            }
            if !pendingID.isEmpty {
                Text("A local pilot request is already recorded. Its ID is \(pendingID). It will not be resent automatically.").font(.caption)
            } else {
                Toggle("I agree to send this fictional question through my ChatGPT subscription.", isOn: $consent)
                Button("Send one reviewed test question") { Task { await send() } }
                    .disabled(!ready || !consent || running || preparing)
            }
            Button("Close") { dismiss() }.disabled(running)
        }
        .padding().frame(minWidth: 570, minHeight: 420)
        .task { await preflight() }
    }

    @MainActor private func preflight() async {
        guard ProcessInfo.processInfo.arguments.contains(Self.launchFlag) else {
            message = "Local pilot is disabled."
            preparing = false
            return
        }
        let result = await Task.detached(priority: .userInitiated) {
            try? LocalCodexBridgeProcess.inspectBundled(prepare: true)
        }.value
        defer { preparing = false }
        guard let result,
              let object = try? JSONSerialization.jsonObject(with: result) as? [String: Any],
              object["inference"] as? Bool == false,
              object["manifest_sha256"] as? String == Self.approvedManifest
        else {
            message = "Local Codex configuration could not be verified. Nothing can be sent."
            return
        }
        ready = true
        message = "Ready for one fictional question. You must review and consent before sending."
    }

    @MainActor private func send() async {
        guard ready, consent, !running, pendingID.isEmpty else { return }
        guard let request = try? ReviewedCodexRequest(text: Self.fixture) else { return }
        let state: URL
        do { state = try LocalCodexBridgeProcess.privateStateDirectory() }
        catch {
            message = "Private local journal is unavailable. Nothing was sent."
            return
        }
        running = true
        consent = false
        pendingID = request.jobID // Saved before any process start; no auto retry.
        message = "Waiting for the original Codex answer. Do not resend this request."
        let approvedHash = Self.approvedManifest
        let result = await Task.detached(priority: .userInitiated) { () -> Data? in
            do {
                return try LocalCodexBridgeProcess.submitBundled(request,
                    approvedHash: approvedHash, stateDirectory: state)
            } catch { return nil }
        }.value
        running = false
        guard let result,
              let object = try? JSONSerialization.jsonObject(with: result) as? [String: Any],
              object["id"] as? String == request.jobID,
              object["automatic_retry"] as? Bool == false,
              object["state"] as? String == "completed",
              let text = object["answer"] as? String, !text.isEmpty
        else {
            message = "Outcome uncertain or unavailable. The request ID is retained; do not resend it."
            return
        }
        answer = text
        message = "One local Codex turn completed."
    }
}
