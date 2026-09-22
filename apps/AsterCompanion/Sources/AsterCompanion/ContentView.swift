import SwiftUI

struct ContentView: View {
    @EnvironmentObject var auth: AuthManager
    @State private var messages: [ChatMessage] = []
    @State private var draft: String = ""
    @State private var state: AsterState = .idle
    @State private var errorText: String?

    private var client: AsterClient { AsterClient(authManager: auth) }

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
                    Button("Sign out") { auth.logout() }
                        .buttonStyle(.plain)
                        .foregroundStyle(.secondary)
                }
                .padding()

                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(messages) { message in
                            HStack {
                                if message.role == .assistant { Spacer(minLength: 0) }
                                Text(message.content)
                                    .padding(10)
                                    .background(.ultraThinMaterial)
                                    .background(message.role == .user ? Color.blue.opacity(0.12) : Color.gray.opacity(0.08))
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
                let reply = try await client.send(history: messages)
                messages.append(ChatMessage(role: .assistant, content: reply))
            } catch {
                errorText = error.localizedDescription
            }
            state = .idle
        }
    }
}
