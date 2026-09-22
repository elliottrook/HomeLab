import SwiftUI

struct ContentView: View {
    @EnvironmentObject var auth: AuthManager
    @State private var messages: [ChatMessage] = []
    @State private var draft: String = ""
    @State private var state: AsterState = .idle
    @State private var errorText: String?

    // Persona + per-chat tool selection (M4). The backend's PERSONAS
    // registry is authoritative (services/aster-agent/aster_agent.py) -
    // this view only renders whatever GET /v1/personas returns; "sysadmin"
    // is just the pre-fetch fallback, matching the server's own default.
    @State private var personasResponse: PersonasResponse?
    @State private var currentPersona: String = UserDefaults.standard.string(forKey: "aster_persona") ?? "sysadmin"
    @State private var enabledToolNames: Set<String> = []

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
            Button("Sign in with passkey") { auth.login() }
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
                    Button("Sign out") { auth.logout() }
                        .buttonStyle(.plain)
                        .foregroundStyle(.secondary)
                }
                .padding()

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

                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(messages) { message in
                            HStack {
                                if message.role == .assistant { Spacer(minLength: 0) }
                                Text(message.content)
                                    .padding(10)
                                    .background(message.role == .user ? Color.blue.opacity(0.15) : Color.gray.opacity(0.1))
                                    .cornerRadius(10)
                                if message.role == .user { Spacer(minLength: 0) }
                            }
                        }
                    }
                    .padding()
                }

                if let errorText {
                    Text(errorText).foregroundStyle(.red).font(.caption).padding(.horizontal)
                }

                HStack {
                    TextField("Ask Aster...", text: $draft, axis: .vertical)
                        .textFieldStyle(.roundedBorder)
                        .onSubmit { send() }
                    Button("Send") { send() }
                        .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || state == .thinking)
                }
                .padding()
            }
        }
        .frame(minWidth: 480, minHeight: 560)
        .task { await loadPersonas() }
    }

    private func send() {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        messages.append(ChatMessage(role: .user, content: text))
        draft = ""
        errorText = nil
        state = .thinking

        Task {
            do {
                let reply = try await client.send(history: messages, persona: currentPersona, enabledTools: enabledToolsPayload())
                messages.append(ChatMessage(role: .assistant, content: reply))
            } catch {
                errorText = error.localizedDescription
            }
            state = .idle
        }
    }
}
