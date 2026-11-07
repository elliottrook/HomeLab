import AppKit
import Foundation

guard CommandLine.arguments.count == 3 else {
    fputs("usage: render_tv_splash.swift SOURCE.svg OUTPUT.png\n", stderr)
    exit(64)
}

let source = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])
guard let logo = NSImage(contentsOf: source) else {
    fputs("approved SVG could not be decoded\n", stderr)
    exit(65)
}
guard let bitmap = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: 1920,
    pixelsHigh: 1080,
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
) else {
    fputs("could not allocate placement bitmap\n", stderr)
    exit(70)
}

NSGraphicsContext.saveGraphicsState()
guard let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
    fputs("could not create placement context\n", stderr)
    exit(70)
}
NSGraphicsContext.current = context
NSColor(calibratedRed: 29.0 / 255.0, green: 36.0 / 255.0, blue: 31.0 / 255.0, alpha: 1).setFill()
NSRect(x: 0, y: 0, width: 1920, height: 1080).fill()
logo.draw(
    in: NSRect(x: 660, y: 347, width: 600, height: 386),
    from: .zero,
    operation: .sourceOver,
    fraction: 1,
    respectFlipped: true,
    hints: [.interpolation: NSImageInterpolation.high]
)
context.flushGraphics()
NSGraphicsContext.restoreGraphicsState()

guard let png = bitmap.representation(using: .png, properties: [:]) else {
    fputs("could not encode placement PNG\n", stderr)
    exit(70)
}
try png.write(to: output, options: .atomic)
