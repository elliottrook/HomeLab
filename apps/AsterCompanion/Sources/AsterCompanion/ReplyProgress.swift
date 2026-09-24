import SwiftUI

/// One `aster.progress` event from a progress-enabled chat stream
/// (services/aster-agent/aster_agent.py `progress_chat`).
enum ChatStreamEvent {
    case step(id: String, label: String?, doneLabel: String?, state: String, ms: Int?)
    case token(String)
    case usage(ChatUsage)

    /// Parses a progress frame; nil for anything that isn't one.
    static func progress(from json: [String: Any]) -> ChatStreamEvent? {
        guard json["object"] as? String == "aster.progress" else { return nil }
        switch json["type"] as? String {
        case "step":
            guard let id = json["id"] as? String, let state = json["state"] as? String else { return nil }
            return .step(id: id, label: json["label"] as? String, doneLabel: json["done_label"] as? String,
                         state: state, ms: json["ms"] as? Int)
        case "usage":
            return .usage(ChatUsage(
                promptTokens: json["prompt_tokens"] as? Int ?? 0,
                completionTokens: json["completion_tokens"] as? Int ?? 0,
                tokensPerSecond: (json["tokens_per_second"] as? NSNumber)?.doubleValue ?? 0
            ))
        default:
            return nil
        }
    }
}

struct ChatUsage: Equatable {
    var promptTokens: Int
    var completionTokens: Int
    var tokensPerSecond: Double
}

struct ChatStep: Identifiable, Equatable {
    let id: String
    var label: String
    var doneLabel: String
    var state: String
    var started: Date
    var ms: Int?

    func line(at now: Date) -> String {
        let mark: String
        switch state {
        case "running": mark = "◐ \(label)…"
        case "failed": mark = "✗ \(doneLabel)"
        default: mark = "✓ \(doneLabel)"
        }
        let elapsed = state == "running" ? now.timeIntervalSince(started) : Double(ms ?? 0) / 1000
        return mark + " · " + ReplyProgress.seconds(elapsed)
    }
}

/// Live state for the reply currently being produced: elapsed time, the
/// server's tool steps and a streamed token count, like Claude Code's own
/// working indicator.
@MainActor
final class ReplyProgress: ObservableObject {
    @Published private(set) var isActive = false
    @Published private(set) var steps: [ChatStep] = []
    @Published private(set) var tokens = 0
    @Published private(set) var partial = ""
    private(set) var started = Date()
    private(set) var firstToken: Date?
    private var usage: ChatUsage?

    nonisolated static func seconds(_ interval: TimeInterval) -> String {
        String(format: interval < 10 ? "%.1fs" : "%.0fs", max(0, interval))
    }

    func begin() {
        isActive = true
        steps = []
        tokens = 0
        partial = ""
        usage = nil
        firstToken = nil
        started = Date()
    }

    func handle(_ event: ChatStreamEvent) {
        switch event {
        case let .step(id, label, doneLabel, state, ms):
            if let index = steps.firstIndex(where: { $0.id == id }) {
                steps[index].state = state
                steps[index].ms = ms
            } else {
                let name = label ?? id
                steps.append(ChatStep(id: id, label: name, doneLabel: doneLabel ?? name, state: state, started: Date(), ms: ms))
            }
        case let .token(text):
            if firstToken == nil { firstToken = Date() }
            tokens += 1
            partial += text
        case let .usage(value):
            usage = value
        }
    }

    func headline(at now: Date) -> String {
        let running = steps.first { $0.state == "running" }
        var line = firstToken != nil ? "Answering" : (running.map { "\($0.label)…" } ?? "Thinking")
        line += " · " + Self.seconds(now.timeIntervalSince(started))
        if tokens > 0, let firstToken {
            line += " · \(tokens.formatted()) tokens"
            let generating = now.timeIntervalSince(firstToken)
            if generating > 0.5 { line += String(format: " · %.1f tok/s", Double(tokens) / generating) }
        }
        return line
    }

    /// Ends the turn and returns what is kept with the finished reply.
    func finish() -> ReplySummary {
        isActive = false
        let now = Date()
        let total = now.timeIntervalSince(started)
        let finished = steps.filter { $0.state != "running" }
        let names = finished.enumerated().map { index, step in
            index == 0 ? step.doneLabel : step.doneLabel.prefix(1).lowercased() + step.doneLabel.dropFirst()
        }
        let out = usage?.completionTokens ?? tokens
        let input = usage?.promptTokens ?? 0
        var rate = usage?.tokensPerSecond ?? 0
        if usage == nil, tokens > 0, let firstToken, now.timeIntervalSince(firstToken) > 0 {
            rate = Double(tokens) / now.timeIntervalSince(firstToken)
        }
        var parts = [Self.seconds(total)]
        if out > 0 { parts.append((input > 0 ? "\(input.formatted()) in / " : "") + "\(out.formatted()) out") }
        if rate > 0 { parts.append(String(format: "%.1f tok/s", rate)) }
        return ReplySummary(
            steps: names.isEmpty ? nil : "✓ " + names.joined(separator: ", ") + " · " + Self.seconds(total),
            stepLines: finished.map { $0.line(at: now) },
            stats: parts.joined(separator: " · ")
        )
    }
}

struct ReplySummary: Equatable {
    var steps: String?
    var stepLines: [String]
    var stats: String
}

/// The live indicator shown while a reply is in progress.
struct ReplyProgressView: View {
    @ObservedObject var progress: ReplyProgress

    var body: some View {
        TimelineView(.periodic(from: .now, by: 0.25)) { context in
            VStack(alignment: .leading, spacing: 4) {
                Text(progress.headline(at: context.date))
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
                ForEach(progress.steps) { step in
                    Text(step.line(at: context.date))
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(.secondary)
                        .padding(.leading, 12)
                }
                if !progress.partial.isEmpty {
                    Text(progress.partial)
                        .padding(10)
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(10)
                }
            }
        }
    }
}
