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
/// header glyph. The whole point of the graphic is the pulse *being* the
/// thinking signal: idle is genuinely static (no motion at all), and only
/// while thinking does it breathe - a continuous ambient pulse regardless
/// of state would defeat that, so this one starts/stops explicitly on the
/// state transition rather than always running.
struct OrbView: View {
    let state: AsterState
    var size: CGFloat = 48
    @State private var isPulsing = false

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
        // Saturation/brightness/scale are all derived from the same
        // isPulsing flag so they animate together as one breathing motion -
        // dim and still at rest, brighter and more colorful at the peak of
        // each pulse - rather than the pulse being scale-only.
        .saturation(state == .thinking ? (isPulsing ? 1.0 : 0.55) : 0.35)
        .brightness(state == .thinking && isPulsing ? 0.12 : 0.0)
        .opacity(state == .thinking ? 1.0 : 0.75)
        .scaleEffect(isPulsing ? 1.08 : 1.0)
        .animation(.easeInOut(duration: 0.6), value: state)
        .onChange(of: state) { _, newValue in
            if newValue == .thinking {
                withAnimation(.easeInOut(duration: 1.6).repeatForever(autoreverses: true)) {
                    isPulsing = true
                }
            } else {
                // A fresh, shorter-duration animation on the same value
                // interrupts the repeatForever loop and eases back to rest,
                // rather than letting it keep cycling in the background.
                withAnimation(.easeOut(duration: 0.4)) {
                    isPulsing = false
                }
            }
        }
    }
}
