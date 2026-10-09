import SwiftUI

struct DelegationJob: Decodable, Identifiable {
    let id: String
    let state: String
}

struct DelegationSnapshot: Decodable {
    struct Usage: Decodable {
        struct Snapshots: Decodable {
            struct Counts: Decodable { let totalTokens: Int }
            let total: Counts
        }
        let status: String
        let providerSnapshots: Snapshots?
    }
    let id: String
    let state: String
    let reply: String?
    let message: String
    let usage: Usage
    let canRequestCancel: Bool
    let recoveryRequired: Bool
    var statusMessage: String {
        if state == "completed" && (recoveryRequired || reply == nil) {
            return "This request completed, but its temporary answer is no longer available in Aster. This pilot cannot restore it here. Do not resend it to recover the answer."
        }
        return message
    }
    var visibleAnswer: String? { state == "completed" ? reply : nil }
    var usageText: String {
        if usage.status == "reported", let total = usage.providerSnapshots?.total.totalTokens, total >= 0 {
            return "Reported thread usage: \(total) tokens. This is not a charge or remaining allowance."
        }
        return "Token usage is unavailable."
    }
}

struct DelegationStopResult: Decodable {
    let stopRequested: Bool
    let state: String
}

/// Owner-scoped status and explicit reviewed submission; never automatic retry.
struct DelegationView: View {
    @EnvironmentObject private var auth: AuthManager
    @Environment(\.dismiss) private var dismiss
    @State private var capabilities: CodexCapabilities?
    @State private var hasLoadedJobs = false
    @State private var jobs: [DelegationJob] = []
    @State private var selected: String?
    @State private var snapshot: DelegationSnapshot?
    @State private var errorText: String?
    @State private var stopPending = false
    @State private var showingRequest = false
    @AppStorage("aster.codex.pendingRequestID") private var pendingID = ""
    private var client: AsterClient { AsterClient(authManager: auth) }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Codex requests").font(.title2)
                Button("Ask Codex") { showingRequest = true }.disabled(capabilities?.supported != true)
                Spacer()
                Button("Done") { dismiss() }
            }
            if let errorText { Text(verbatim: errorText).foregroundStyle(.red) }
            Text(capabilities?.availabilityMessage ?? "Cannot confirm Codex availability. New requests are blocked; recorded status may still be available.").font(.caption)
            if hasLoadedJobs && jobs.isEmpty { Text("No assigned requests.") }
            ForEach(jobs) { job in
                Button("Request \(job.id.prefix(12)) — \(job.state)") {
                    selected = job.id; snapshot = nil; stopPending = false
                    Task { await refresh() }
                }
            }
            if let snapshot {
                Text(verbatim: snapshot.statusMessage)
                if let answer = snapshot.visibleAnswer {
                    ScrollView { Text(verbatim: answer).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading) }
                }
                Text(verbatim: snapshot.usageText).font(.caption)
                if snapshot.canRequestCancel {
                    Button("Request stop") { Task { await stop() } }.disabled(stopPending)
                }
                if stopPending { Text("Stop requested; waiting for confirmation.").font(.caption) }
            }
        }
        .padding().frame(minWidth: 560, minHeight: 380)
        .sheet(isPresented: $showingRequest) {
            CodexRequestView { id in selected = id; snapshot = nil }.environmentObject(auth)
        }
        .task {
            if !pendingID.isEmpty { selected = pendingID }
            while !Task.isCancelled {
                await refresh()
                do { try await Task.sleep(for: .seconds(2)) } catch { break }
            }
        }
        .onDisappear { snapshot = nil; jobs = []; selected = nil }
    }

    @MainActor private func refresh() async {
        capabilities = try? await client.fetchCodexCapabilities()
        guard !Task.isCancelled else { return }
        do {
            let list = try await client.fetchDelegationJobs()
            guard !Task.isCancelled else { return }
            jobs = list
            hasLoadedJobs = true
            if let id = selected {
                let value = try await client.fetchDelegationJob(id)
                guard !Task.isCancelled, selected == id else { return }
                snapshot = value
                if pendingID == id && ["completed", "failed", "interrupted", "expired"].contains(value.state) {
                    pendingID = ""
                }
                if ["completed", "failed", "interrupted", "expired"].contains(value.state) { stopPending = false }
            }
            errorText = nil
        } catch {
            snapshot = nil
            errorText = "Request status is unavailable. Do not resend uncertain work."
        }
    }

    @MainActor private func stop() async {
        guard let id = selected, !stopPending else { return }
        stopPending = true
        do {
            _ = try await client.stopDelegationJob(id)
            await refresh()
        } catch {
            errorText = "The stop request could not be confirmed. Check the request status."
        }
    }
}
