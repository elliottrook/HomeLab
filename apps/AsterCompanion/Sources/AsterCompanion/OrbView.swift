import SwiftUI

enum AsterState {
    case idle
    case thinking
    // speaking/listening/acting states are added in later milestones
    // (voice in M6, gated actions in M5) - not built yet.
}

/// Minimal visual state indicator for M3: idle vs. thinking only.
/// Deliberately simple; the real orb/EQ-style design is refined once
/// voice and gated actions exist and there are more states to distinguish.
struct OrbView: View {
    let state: AsterState
    @State private var pulse = false

    var body: some View {
        Circle()
            .fill(color)
            .frame(width: 48, height: 48)
            .scaleEffect(state == .thinking && pulse ? 1.15 : 1.0)
            .opacity(state == .thinking && pulse ? 0.7 : 1.0)
            .animation(
                state == .thinking
                    ? .easeInOut(duration: 0.8).repeatForever(autoreverses: true)
                    : .default,
                value: pulse
            )
            .onAppear { pulse = true }
    }

    private var color: Color {
        switch state {
        case .idle: return .gray
        case .thinking: return .blue
        }
    }
}
