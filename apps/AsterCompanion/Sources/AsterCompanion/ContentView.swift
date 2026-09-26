import SwiftUI

struct ContentView: View {
    @EnvironmentObject var auth: AuthManager
    @StateObject private var notifications = CompanionNotifications()
    @State private var labHealth: CompanionLabHealth?
    @State private var lastHealthFingerprint: String?
    @State private var messages: [ChatMessage] = []
    @State private var draft: String = ""
    @State private var state: AsterState = .idle
    @State private var errorText: String?
    @StateObject private var replyProgress = ReplyProgress()
    @State private var showingAIPAM = false

    // Persona + per-chat tool selection (M4). The backend's PERSONAS
    // registry is authoritative (services/aster-agent/aster_agent.py) -
    // this view only renders whatever GET /v1/personas returns; "sysadmin"
    // is just the pre-fetch fallback, matching the server's own default.
    @State private var personasResponse: PersonasResponse?
    @State private var currentPersona: String = UserDefaults.standard.string(forKey: "aster_persona") ?? "sysadmin"
    @State private var enabledToolNames: Set<String> = []

    // Gated-action framework (M5): the one wired action is ARR-repair,
    // requested/reviewed/approved independent of chat, mirroring the web
    // client's action card.
    @State private var arrProposal: ArrRepairProposal?
    @State private var arrResultText: String?
    @State private var arrErrorText: String?

    // Voice in/out (M6). Recording and playback are tap-to-start/tap-to-
    // stop, matching the web client's own flow - no silence detection.
    @State private var voiceRecorder = VoiceRecorder()
    @State private var voicePlayer = VoicePlayer()

    private var client: AsterClient { AsterClient(authManager: auth) }

    private var currentPersonaModel: Persona? {
        personasResponse?.personas.first { $0.id == currentPersona }
    }

    private func toolsStorageKey(_ personaId: String) -> String { "aster_tools_" + personaId }

    private func savedEnabledTools(for personaId: String) -> [String]? {
        guard let data = UserDefaults.standard.data(forKey: toolsStorageKey(personaId)) else { return nil }
        return try? JSONDecoder().decode([String].self, from: data)
    }

    private func saveEnabledTools(_ tools: [String]?, for personaId: String) {
        if let tools {
            UserDefaults.standard.set(try? JSONEncoder().encode(tools), forKey: toolsStorageKey(personaId))
        } else {
            UserDefaults.standard.removeObject(forKey: toolsStorageKey(personaId))
        }
    }

    /// All persona tools checked is the common case, so nothing is
    /// persisted for it - a persona gaining a new tool later shows up
    /// already enabled instead of being silently excluded by a stale list.
    private func resetToolSelection() {
        guard let persona = currentPersonaModel else {
            enabledToolNames = []
            return
        }
        let allNames = Set(persona.tools.map(\.name))
        if let saved = savedEnabledTools(for: persona.id) {
            enabledToolNames = Set(saved).intersection(allNames)
        } else {
            enabledToolNames = allNames
        }
    }

    private func toggleTool(_ name: String, isOn: Bool) {
        if isOn { enabledToolNames.insert(name) } else { enabledToolNames.remove(name) }
        guard let persona = currentPersonaModel else { return }
        if enabledToolNames.count == persona.tools.count {
            saveEnabledTools(nil, for: persona.id)
        } else {
            saveEnabledTools(Array(enabledToolNames), for: persona.id)
        }
    }

    /// nil means "every tool the persona allows" - matches the backend's
    /// own null-means-unrestricted semantics for enabled_tools.
    private func enabledToolsPayload() -> [String]? {
        guard let persona = currentPersonaModel else { return nil }
        return enabledToolNames.count == persona.tools.count ? nil : Array(enabledToolNames)
    }

    /// Switching persona starts a fresh chat rather than silently
    /// re-scoping an in-progress one, since the persona's identity
    /// framing is part of the system prompt sent with every turn -
    /// matches the web client's same decision.
    private func switchPersona(_ newPersona: String) {
        guard newPersona != currentPersona,
              personasResponse?.personas.contains(where: { $0.id == newPersona }) == true else { return }
        currentPersona = newPersona
        UserDefaults.standard.set(currentPersona, forKey: "aster_persona")
        messages.removeAll()
        errorText = nil
        resetToolSelection()
    }

    private func loadPersonas() async {
        guard let result = try? await client.fetchPersonas() else { return }
        personasResponse = result
        if !result.personas.contains(where: { $0.id == currentPersona }) {
            currentPersona = result.default
        }
        resetToolSelection()
    }

    var body: some View {
        if !auth.isAuthenticated {
            loginView
        } else {
            chatView
        }
    }

    private var loginView: some View {
        VStack(spacing: 16) {
            OrbView(state: .idle)
            Text("Aster Companion")
                .font(.title2)
            Button(auth.isSigningIn ? "Signing in…" : "Sign in with passkey") { auth.login() }
                .disabled(auth.isSigningIn)
                .buttonStyle(.borderedProminent)
            if let error = auth.lastError {
                Text(error).foregroundStyle(.red).font(.caption)
            }
        }
        .frame(minWidth: 360, minHeight: 240)
        .padding()
    }

    private var chatView: some View {
        ZStack {
            // The orb lives as a large, quiet presence behind the whole
            // conversation rather than a small header glyph - faded well
            // below full opacity so message text on top stays fully
            // readable regardless of idle/thinking state.
            OrbView(state: state, size: 420)
                .opacity(0.16)
                .allowsHitTesting(false)

            VStack(spacing: 0) {
                HStack {
                    Text("Aster").font(.headline)
                    Spacer()
                    if let personas = personasResponse?.personas, !personas.isEmpty {
                        Picker("", selection: Binding(get: { currentPersona }, set: switchPersona)) {
                            ForEach(personas) { persona in
                                Text(persona.label).tag(persona.id)
                            }
                        }
                        .pickerStyle(.menu)
                        .frame(maxWidth: 200)
                        .labelsHidden()
                    }
                    Button("Sign out") { notifications.disable(); auth.logout() }
                        .buttonStyle(.plain)
                        .foregroundStyle(.secondary)
                    Button("AI-PAM") { showingAIPAM = true }
                        .buttonStyle(.bordered)
                }
                .padding()
                .sheet(isPresented: $showingAIPAM) { AIPAMView(auth: auth).environmentObject(auth) }

                DisclosureGroup("Notifications") {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(notifications.status).font(.caption)
                        Text("Private previews. Background alerts require Aster to remain running.")
                            .font(.caption).foregroundStyle(.secondary)
                        if let health = labHealth {
                            Text("Lab health: " + health.status).font(.caption)
                            if let reason = health.reason { Text(reason).font(.caption) }
                            ForEach(Array(health.checks.filter { $0.status != "pass" }.enumerated()), id: \.offset) { _, check in
                                Text(check.summary).font(.caption)
                            }
                        }
                        if notifications.enabled {
                            Button("Disable notifications") { notifications.disable() }
                        } else {
                            Button("Enable notifications") { Task { await notifications.enable() } }
                        }
                    }
                }
                .padding(.horizontal)
                .padding(.bottom, 8)

                if let persona = currentPersonaModel, !persona.tools.isEmpty {
                    DisclosureGroup("Tools") {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(persona.tools) { tool in
                                Toggle(tool.name, isOn: Binding(
                                    get: { enabledToolNames.contains(tool.name) },
                                    set: { toggleTool(tool.name, isOn: $0) }
                                ))
                                .toggleStyle(.checkbox)
                                .help(tool.description)
                                .font(.caption)
                            }
                        }
                        .padding(.top, 4)
                        .padding(.leading, 8)
                    }
                    .font(.caption)
                    .padding(.horizontal)
                    .padding(.bottom, 8)
                }

                HStack {
                    Button("Check for pending ARR action") { checkArrAction() }
                        .buttonStyle(.plain)
                        .foregroundStyle(.secondary)
                        .font(.caption)
                    Spacer()
                }
                .padding(.horizontal)

                if let proposal = arrProposal, let dryRun = proposal.dryRun {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Pending ARR action: \(dryRun.operation ?? "unknown")")
                            .font(.headline)
                        if let service = dryRun.service {
                            Text("Service: \(service)").font(.caption)
                        }
                        if let effect = dryRun.effectIfLaterEnabled {
                            Text("Effect: \(effect)").font(.caption)
                        }
                        if let preconditions = dryRun.preconditions, !preconditions.isEmpty {
                            VStack(alignment: .leading, spacing: 2) {
                                ForEach(preconditions, id: \.self) { item in
                                    Text("• \(item)").font(.caption)
                                }
                            }
                        }
                        if let rollback = dryRun.rollback {
                            Text("Rollback: \(rollback)").font(.caption)
                        }
                        HStack {
                            Button("Approve") { approveArrAction() }
                                .buttonStyle(.borderedProminent)
                                .tint(.red)
                            Button("Dismiss") { dismissArrAction() }
                                .buttonStyle(.bordered)
                        }
                    }
                    .padding(10)
                    .background(Color.orange.opacity(0.15))
                    .cornerRadius(10)
                    .padding(.horizontal)
                }

                if let arrResultText {
                    Text(arrResultText).font(.caption).foregroundStyle(.secondary).padding(.horizontal)
                }
                if let arrErrorText {
                    Text(arrErrorText).font(.caption).foregroundStyle(.red).padding(.horizontal)
                }

                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(messages) { message in
                            HStack {
                                if message.role == .assistant { Spacer(minLength: 0) }
                                VStack(alignment: .leading, spacing: 4) {
                                    if let summary = message.summary, let steps = summary.steps {
                                        DisclosureGroup(steps) {
                                            ForEach(summary.stepLines, id: \.self) { line in
                                                Text(line).padding(.leading, 12)
                                            }
                                        }
                                        .font(.caption.monospacedDigit())
                                        .foregroundStyle(.secondary)
                                    }
                                    Text(message.content)
                                        .padding(10)
                                        .background(message.role == .user ? Color.blue.opacity(0.15) : Color.gray.opacity(0.1))
                                        .cornerRadius(10)
                                    if let stats = message.summary?.stats {
                                        Text(stats)
                                            .font(.caption2.monospacedDigit())
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                if message.role == .user { Spacer(minLength: 0) }
                            }
                        }
                        if replyProgress.isActive {
                            ReplyProgressView(progress: replyProgress)
                        }
                    }
                    .padding()
                }

                if let authWarning = auth.lastError {
                    Text(authWarning).foregroundStyle(.orange).font(.caption).padding(.horizontal)
                }

                if let errorText {
                    Text(errorText).foregroundStyle(.red).font(.caption).padding(.horizontal)
                }

                HStack {
                    TextField("Ask Aster...", text: $draft, axis: .vertical)
                        .textFieldStyle(.roundedBorder)
                        .onSubmit { send() }
                    Button("Send") { send() }
                        .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || state != .idle)
                    Button {
                        toggleMic()
                    } label: {
                        // The Aster orb artwork itself, not a generic system
                        // glyph - a plain SF Symbol mic "looked like a
                        // button", per direct feedback, rather than part of
                        // Aster's own identity.
                        OrbView(state: .idle, size: 28)
                            .overlay(
                                Circle().stroke(state == .listening ? Color.green : Color.clear, lineWidth: 2)
                            )
                    }
                    .buttonStyle(.plain)
                    .disabled(state == .thinking || state == .acting || state == .speaking)
                }
                .padding()
            }
        }
        .frame(minWidth: 480, minHeight: 560)
         .task {
            await loadPersonas()
            while !Task.isCancelled && auth.isAuthenticated {
                await notifications.refresh()
                if let report = try? await client.labHealth() {
                    labHealth = report
                    if let fingerprint = report.fingerprint {
                        if lastHealthFingerprint != fingerprint && ["warning", "failed"].contains(report.status) {
                            await notifications.post(.labAlert, eventID: "lab-" + fingerprint)
                        }
                        lastHealthFingerprint = fingerprint
                    }
                }
                do { try await Task.sleep(for: .seconds(60)) } catch { return }
            }
        }
    }

    private func checkArrAction() {
        arrResultText = nil
        arrErrorText = nil
        Task {
            do {
                let proposal = try await client.fetchArrRepairProposal()
                arrProposal = proposal.isAvailable ? proposal : nil
                if !proposal.isAvailable {
                    arrResultText = "No pending ARR action right now."
                }
            } catch {
                arrErrorText = error.localizedDescription
            }
        }
    }

    private func approveArrAction() {
        guard let candidateRef = arrProposal?.dryRun?.candidateRef else { return }
        state = .acting
        arrErrorText = nil
        Task {
            do {
                let result = try await client.executeArrRepair(candidateRef: candidateRef)
                arrResultText = "Result: \(result.status)"
            } catch {
                arrErrorText = error.localizedDescription
            }
            arrProposal = nil
            state = .idle
        }
    }

    private func dismissArrAction() {
        arrProposal = nil
        arrResultText = nil
        arrErrorText = nil
    }

    /// - Parameter viaVoice: whether this turn started as a voice question
    ///   - only then is the reply spoken back, matching the web client's
    ///   same reasoning (a typed question stays silent).
    private func send(viaVoice: Bool = false) {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, state == .idle || viaVoice else { return }
        messages.append(ChatMessage(role: .user, content: text))
        draft = ""
        errorText = nil
        state = .thinking

        replyProgress.begin()

        Task {
            do {
                let reply = try await client.send(
                    history: messages, persona: currentPersona, enabledTools: enabledToolsPayload(),
                    onEvent: { replyProgress.handle($0) }
                )
                let summary = replyProgress.finish()
                guard auth.isAuthenticated else { state = .idle; return }
                messages.append(ChatMessage(role: .assistant, content: reply, summary: summary))
                await notifications.post(.replyReady, eventID: "reply-" + UUID().uuidString)
                if viaVoice {
                    state = .speaking
                    for chunk in speechChunks(reply) {
                        let audio = try await client.synthesize(text: chunk)
                        try await voicePlayer.play(data: audio)
                    }
                }
            } catch {
                if replyProgress.isActive { _ = replyProgress.finish() }
                errorText = error.localizedDescription
            }
            state = .idle
        }
    }

    private func toggleMic() {
        if state == .listening {
            guard let audioData = voiceRecorder.stopRecording() else {
                state = .idle
                errorText = "No audio was recorded."
                return
            }
            state = .thinking
            Task {
                do {
                    let text = try await client.transcribe(audioData: audioData)
                    guard !text.isEmpty else {
                        errorText = "Could not hear anything - try again."
                        state = .idle
                        return
                    }
                    draft = text
                    send(viaVoice: true)
                } catch {
                    state = .idle
                    errorText = error.localizedDescription
                }
            }
            return
        }

        guard state == .idle else { return }
        state = .thinking
        Task {
            guard await voiceRecorder.requestPermission() else {
                state = .idle
                errorText = "Microphone access denied."
                return
            }
            do {
                errorText = nil
                try voiceRecorder.startRecording()
                state = .listening
            } catch {
                state = .idle
                errorText = error.localizedDescription
            }
        }
    }
}
