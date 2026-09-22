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
    case acting
    // speaking/listening states are added in M6 (voice) - not built yet.
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
        // each pulse - rather than the pulse being scale-only. Acting uses
        // a hue shift plus a faster, more intense pulse than thinking, so a
        // real mutating action in flight is visually unmistakable rather
        // than looking like an ordinary "still working" state.
        .saturation(isActive ? (isPulsing ? (state == .acting ? 1.4 : 1.0) : (state == .acting ? 0.8 : 0.55)) : 0.35)
        .brightness(isActive && isPulsing ? (state == .acting ? 0.2 : 0.12) : 0.0)
        .hueRotation(.degrees(state == .acting ? -20 : 0))
        .opacity(isActive ? 1.0 : 0.75)
        .scaleEffect(isPulsing ? (state == .acting ? 1.12 : 1.08) : 1.0)
        .animation(.easeInOut(duration: 0.6), value: state)
        .onChange(of: state) { _, newValue in
            switch newValue {
            case .thinking:
                withAnimation(.easeInOut(duration: 1.6).repeatForever(autoreverses: true)) {
                    isPulsing = true
                }
            case .acting:
                withAnimation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true)) {
                    isPulsing = true
                }
            case .idle:
                // A fresh, shorter-duration animation on the same value
                // interrupts the repeatForever loop and eases back to rest,
                // rather than letting it keep cycling in the background.
                withAnimation(.easeOut(duration: 0.4)) {
                    isPulsing = false
                }
            }
        }
    }

    private var isActive: Bool { state == .thinking || state == .acting }
}
