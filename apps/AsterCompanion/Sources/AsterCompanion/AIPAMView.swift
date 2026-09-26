import SwiftUI

@MainActor
final class AIPAMViewModel: ObservableObject {
    @Published var pending: [AIPAMPendingApproval] = []
    @Published var snapshot: AIPAMSnapshot?
    @Published var history: [AIPAMHistoryItem] = []
    @Published var audit: [AIPAMAuditItem] = []
    @Published var loading = false
    @Published var errorText: String?
    @Published var auditEvent = ""

    let states = ["probation", "observer", "operator", "specialist", "orchestrator", "suspended", "retired"]
    private let client: AsterClient

    init(auth: AuthManager) { client = AsterClient(authManager: auth) }

    func refresh() async {
        loading = true
        defer { loading = false }
        do {
            async let pending = client.fetchAIPAMPending()
            async let snapshot = client.fetchAIPAMSnapshot()
            async let history = client.fetchAIPAMHistory()
            async let audit = client.fetchAIPAMAudit(event: auditEvent.isEmpty ? nil : auditEvent)
            (self.pending, self.snapshot, self.history, self.audit) = try await (pending, snapshot, history, audit)
            errorText = nil
        } catch { errorText = error.localizedDescription }
    }

    func approval(_ item: AIPAMPendingApproval, approve: Bool) async {
        do {
            _ = try await client.actOnAIPAMApproval(item, approve: approve)
            await refresh()
        } catch { errorText = error.localizedDescription }
    }

    func management(_ action: AIPAMManagementAction) async {
        do {
            _ = try await client.performAIPAMManagement(action)
            await refresh()
        } catch { errorText = error.localizedDescription }
    }
}

struct AIPAMView: View {
    @EnvironmentObject private var auth: AuthManager
    @Environment(\.dismiss) private var dismiss
    @StateObject private var model: AIPAMViewModel
    @State private var selectedStates: [String: String] = [:]

    init(auth: AuthManager) { _model = StateObject(wrappedValue: AIPAMViewModel(auth: auth)) }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("AI-PAM").font(.title2).bold()
                if model.loading { ProgressView().controlSize(.small) }
                Spacer()
                Button("Refresh") { Task { await model.refresh() } }
                Button("Done") { dismiss() }
            }.padding()

            if let error = model.errorText {
                Text(error).foregroundStyle(.red).font(.caption).padding(.horizontal)
            }

            TabView {
                approvals.tabItem { Label("Approvals", systemImage: "checkmark.shield") }
                management.tabItem { Label("Management", systemImage: "switch.2") }
                records.tabItem { Label("History", systemImage: "clock.arrow.circlepath") }
            }
        }
        .frame(minWidth: 760, minHeight: 620)
        .task { await model.refresh() }
    }

    private var approvals: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 12) {
                if model.pending.isEmpty { ContentUnavailableView("No pending approvals", systemImage: "checkmark.circle") }
                ForEach(model.pending) { item in
                    GroupBox("\(item.riskClass.uppercased()): \(item.capability)") {
                        VStack(alignment: .leading, spacing: 6) {
                            display("Reason", item.display.reason)
                            display("Target", item.display.target)
                            display("Effect", item.display.effect)
                            display("Rollback", item.display.rollback)
                            Text("Expires: \(Date(timeIntervalSince1970: item.expiresAt).formatted())")
                            Text("Payload SHA-256: \(item.payloadHash)").font(.caption.monospaced())
                            HStack {
                                Button(item.requiresFreshAuthentication ? "Re-authenticate & approve" : "Approve") {
                                    if item.requiresFreshAuthentication {
                                        fresh { Task { await model.approval(item, approve: true) } }
                                    } else { Task { await model.approval(item, approve: true) } }
                                }.buttonStyle(.borderedProminent)
                                Button("Deny", role: .destructive) { Task { await model.approval(item, approve: false) } }
                            }
                        }.frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }.padding()
        }
    }

    private var management: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 12) {
                if let snapshot = model.snapshot {
                    GroupBox("Emergency controls") {
                        HStack {
                            Text("Global AI access: \(snapshot.globalEnabled ? "ENABLED" : "DISABLED")")
                            Spacer()
                            Button(snapshot.globalEnabled ? "REVOKE ALL AI ACCESS" : "Restore global AI access", role: .destructive) {
                                fresh { Task { await model.management(.init(action: "global_enabled", enabled: !snapshot.globalEnabled)) } }
                            }
                        }
                    }
                    ForEach(snapshot.agents) { agent in agentCard(agent) }
                    ForEach(snapshot.services) { service in serviceCard(service) }
                    GroupBox("Active sessions / requests") {
                        if snapshot.activeRequests.isEmpty { Text("None") }
                        ForEach(snapshot.activeRequests) { item in
                            HStack {
                                Text("\(item.capability) · \(item.status) · \(item.requestId)").font(.caption)
                                Spacer()
                                Button("Revoke", role: .destructive) {
                                    fresh { Task { await model.management(.init(action: "request_revoke", target: item.requestId)) } }
                                }
                            }
                        }
                    }
                }
            }.padding()
        }
    }

    private func agentCard(_ agent: AIPAMAgent) -> some View {
        GroupBox("AI client: \(agent.agentId)") {
            VStack(alignment: .leading, spacing: 6) {
                Text("State: \(agent.state) · Unix UID: \(agent.unixUid)")
                ForEach(agent.capabilities) { cap in Text("• \(cap.capability) · \(cap.riskClass) · \(cap.serviceId)").font(.caption) }
                HStack {
                    Picker("State", selection: Binding(
                        get: { selectedStates[agent.agentId] ?? agent.state },
                        set: { selectedStates[agent.agentId] = $0 }
                    )) { ForEach(model.states, id: \.self) { Text($0).tag($0) } }.frame(maxWidth: 220)
                    Button("Apply state") {
                        let state = selectedStates[agent.agentId] ?? agent.state
                        fresh { Task { await model.management(.init(action: "agent_state", target: agent.agentId, state: state)) } }
                    }
                }
            }.frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func serviceCard(_ service: AIPAMService) -> some View {
        GroupBox("Service: \(service.serviceId)") {
            VStack(alignment: .leading, spacing: 5) {
                Text("Mode: \(service.executionMode) · Capabilities: \(service.capabilityCount) · \(service.isEnabled ? "enabled" : "disabled")")
                Text("Credential: \(service.credentialType) · Custody: \(service.custodyIdentifier)").font(.caption)
                Text("Scope: \(service.credentialScope) · Health: \(service.health)").font(.caption)
                Text("Rotation: \(service.rotationDue) · Revocation: \(service.revocationMethod)").font(.caption)
                Button(service.isEnabled ? "Disable AI access" : "Enable AI access", role: service.isEnabled ? .destructive : nil) {
                    fresh { Task { await model.management(.init(action: "service_enabled", target: service.serviceId, enabled: !service.isEnabled)) } }
                }
            }.frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var records: some View {
        HSplitView {
            List(model.history) { item in
                VStack(alignment: .leading) {
                    Text("\(item.status) · \(item.riskClass) · \(item.capability)")
                    Text(Date(timeIntervalSince1970: item.createdAt).formatted()).font(.caption).foregroundStyle(.secondary)
                }
            }
            VStack(alignment: .leading) {
                HStack {
                    TextField("Exact event, e.g. request.deny", text: $model.auditEvent)
                    Button("Search") { Task { await model.refresh() } }
                }.padding()
                List(model.audit) { item in
                    Text("\(item.sequence) · \(item.event) · \(item.outcome)")
                }
            }
        }
    }

    @ViewBuilder private func display(_ label: String, _ value: String?) -> some View {
        if let value, !value.isEmpty { Text("\(label): \(value)") }
    }

    private func fresh(_ action: @escaping @MainActor () -> Void) {
        auth.login(fresh: true) { success in if success { action() } }
    }
}
