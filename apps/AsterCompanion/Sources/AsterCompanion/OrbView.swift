import SwiftUI

enum AsterState {
    case idle
    case thinking
    // speaking/listening/acting states are added in later milestones
    // (voice in M6, gated actions in M5) - not built yet.
}

/// Visual state indicator built from the accepted app-icon artwork itself
/// (docs/projects/Aster-Companion-App.md, "Visual identity") rather than a
/// generic placeholder shape - the icon's petals/compass-needle motif was
/// designed with this exact use in mind. Idle is the artwork at rest;
/// thinking adds a slow continuous rotation (the compass-needle read as
/// "searching/orienting") plus a gentle breathing pulse, distinct enough
/// from idle at a glance without needing a second asset.
struct OrbView: View {
    let state: AsterState
    @State private var rotation: Double = 0
    @State private var pulse = false

    var body: some View {
        Image("AsterOrb", bundle: .module)
            .resizable()
            .scaledToFit()
            .frame(width: 48, height: 48)
            .saturation(state == .thinking ? 1.0 : 0.35)
            .opacity(state == .thinking ? 1.0 : 0.75)
            .rotationEffect(.degrees(rotation))
            .scaleEffect(state == .thinking && pulse ? 1.08 : 1.0)
            .animation(
                state == .thinking
                    ? .easeInOut(duration: 1.2).repeatForever(autoreverses: true)
                    : .default,
                value: pulse
            )
            .onAppear { pulse = true }
            .onChange(of: state) { _, newValue in
                if newValue == .thinking {
                    startSpinning()
                } else {
                    withAnimation(.easeOut(duration: 0.4)) { rotation = 0 }
                }
            }
    }

    private func startSpinning() {
        withAnimation(.linear(duration: 6).repeatForever(autoreverses: false)) {
            rotation += 360
        }
    }
}
