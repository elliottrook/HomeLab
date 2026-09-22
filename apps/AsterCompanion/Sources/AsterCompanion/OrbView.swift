import AppKit
import SwiftUI

/// Loaded via an explicit file path rather than Image("AsterOrb",
/// bundle: .module) - that initializer's named-lookup is really meant
/// for asset-catalog entries, and was unreliable for a loose PNG copied
/// in via a plain `resources:` rule. A missing image here fails loud
/// (a visible red placeholder is printed to stderr) instead of silently
/// rendering nothing, the way the bundle-name lookup did.
private let asterOrbImage: NSImage? = {
    guard let path = Bundle.module.path(forResource: "AsterOrb", ofType: "png") else {
        FileHandle.standardError.write(Data("AsterOrb.png not found in Bundle.module (\(Bundle.module.bundlePath))\n".utf8))
        return nil
    }
    guard let image = NSImage(contentsOfFile: path) else {
        FileHandle.standardError.write(Data("AsterOrb.png found at \(path) but failed to load as an image\n".utf8))
        return nil
    }
    return image
}()

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
        Group {
            if let asterOrbImage {
                Image(nsImage: asterOrbImage)
                    .resizable()
                    .scaledToFit()
            } else {
                // Loud, visible fallback if the artwork ever fails to load,
                // instead of an empty space that looks like "nothing happened".
                Circle().fill(.red).overlay(Text("!").foregroundStyle(.white))
            }
        }
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
