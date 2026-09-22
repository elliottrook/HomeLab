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
/// (docs/projects/Aster-Companion-App.md, "Visual identity"). Lives as a
/// large, circular background presence behind the chat rather than a small
/// header glyph. The gentle breathing pulse runs continuously and
/// independently of state (started once, never restarted, so it can't
/// glitch against a state-driven transition); idle vs. thinking is just a
/// calm saturation/opacity crossfade on top of that, not a different
/// animation style - deliberately kept quiet since it now sits behind the
/// whole conversation.
struct OrbView: View {
    let state: AsterState
    var size: CGFloat = 48
    @State private var pulse = false

    var body: some View {
        Group {
            if let asterOrbImage {
                Image(nsImage: asterOrbImage)
                    .resizable()
                    .scaledToFill()
            } else {
                // Loud, visible fallback if the artwork ever fails to load,
                // instead of an empty space that looks like "nothing happened".
                Circle().fill(.red).overlay(Text("!").foregroundStyle(.white))
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
        .saturation(state == .thinking ? 1.0 : 0.35)
        .opacity(state == .thinking ? 1.0 : 0.75)
        .animation(.easeInOut(duration: 0.6), value: state)
        .scaleEffect(pulse ? 1.03 : 1.0)
        .onAppear {
            withAnimation(.easeInOut(duration: 2.4).repeatForever(autoreverses: true)) {
                pulse = true
            }
        }
    }
}
