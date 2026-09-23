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
    case listening
    case speaking
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
        // each pulse - rather than the pulse being scale-only. Each active
        // state gets its own hue shift and pulse speed (matching the web
        // client's equivalent CSS states) so thinking/acting/listening/
        // speaking are all visually distinct at a glance, not just labeled
        // differently.
        .saturation(isActive ? (isPulsing ? state.peakSaturation : state.restSaturation) : 0.35)
        .brightness(isActive && isPulsing ? state.peakBrightness : 0.0)
        .hueRotation(.degrees(state.hueDegrees))
        .opacity(isActive ? 1.0 : 0.75)
        .scaleEffect(isPulsing ? state.peakScale : 1.0)
        .animation(.easeInOut(duration: 0.6), value: state)
        .onChange(of: state) { _, newValue in
            if let cycle = newValue.pulseCycleSeconds {
                withAnimation(.easeInOut(duration: cycle).repeatForever(autoreverses: true)) {
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

    private var isActive: Bool { state != .idle }
}

private extension AsterState {
    /// nil means "idle" - no repeating pulse.
    var pulseCycleSeconds: Double? {
        switch self {
        case .idle: return nil
        case .thinking: return 1.6
        case .acting: return 0.8
        case .listening: return 1.0
        case .speaking: return 0.5
        }
    }

    var hueDegrees: Double {
        switch self {
        case .idle, .thinking: return 0
        case .acting: return -20
        case .listening: return 90
        case .speaking: return 180
        }
    }

    var restSaturation: Double { self == .acting ? 0.8 : 0.55 }
    var peakSaturation: Double { self == .acting ? 1.4 : 1.0 }
    var peakBrightness: Double { self == .acting ? 0.2 : 0.12 }
    var peakScale: Double { self == .acting ? 1.12 : 1.08 }
}
