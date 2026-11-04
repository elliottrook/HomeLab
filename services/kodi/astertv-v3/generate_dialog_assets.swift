#!/usr/bin/env swift
import AppKit
import Foundation

let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
    .appendingPathComponent("overlay/skin.asterhome.v3pilot/media")
let size = NSSize(width: 64, height: 64)
let gold = NSColor(calibratedRed: 173/255, green: 138/255, blue: 77/255, alpha: 1)

func write(_ image: NSImage, to url: URL) {
    guard let tiff = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let png = bitmap.representation(using: .png, properties: [:]) else {
        fatalError("could-not-encode-\(url.lastPathComponent)")
    }
    try! png.write(to: url, options: .atomic)
}

func surface(name: String, top: NSColor, bottom: NSColor, radius: CGFloat, dark: Bool = false) {
    let image = NSImage(size: size)
    image.lockFocus()
    NSColor.clear.setFill()
    NSRect(origin: .zero, size: size).fill()
    let shadowRect = NSRect(x: 3, y: 2, width: 58, height: 56)
    NSColor(calibratedWhite: 0.04, alpha: dark ? 0.32 : 0.48).setFill()
    NSBezierPath(roundedRect: shadowRect, xRadius: radius, yRadius: radius).fill()
    let faceRect = NSRect(x: 2, y: 6, width: 60, height: 56)
    let face = NSBezierPath(roundedRect: faceRect, xRadius: radius, yRadius: radius)
    NSGraphicsContext.saveGraphicsState()
    face.addClip()
    NSGradient(starting: bottom, ending: top)!.draw(in: faceRect, angle: 90)
    NSGraphicsContext.restoreGraphicsState()
    gold.setStroke()
    face.lineWidth = dark ? 1.5 : 2
    face.stroke()
    if !dark {
        NSColor(calibratedWhite: 1, alpha: 0.42).setStroke()
        let shine = NSBezierPath()
        shine.move(to: NSPoint(x: 19, y: 58))
        shine.line(to: NSPoint(x: 45, y: 58))
        shine.lineWidth = 1.5
        shine.lineCapStyle = .round
        shine.stroke()
    }
    image.unlockFocus()
    write(image, to: root.appendingPathComponent(name))
}

surface(name: "ui-dialog-pill-rest.png",
        top: NSColor(calibratedRed: 241/255, green: 238/255, blue: 230/255, alpha: 1),
        bottom: NSColor(calibratedRed: 196/255, green: 192/255, blue: 181/255, alpha: 1), radius: 10)
surface(name: "ui-dialog-result-rest.png",
        top: NSColor(calibratedRed: 242/255, green: 239/255, blue: 232/255, alpha: 1),
        bottom: NSColor(calibratedRed: 196/255, green: 192/255, blue: 181/255, alpha: 1), radius: 8)
surface(name: "ui-dialog-section.png",
        top: NSColor(calibratedRed: 41/255, green: 39/255, blue: 33/255, alpha: 1),
        bottom: NSColor(calibratedRed: 23/255, green: 22/255, blue: 18/255, alpha: 1), radius: 18, dark: true)

let frames = [
    [18, 34, 50, 30, 14], [34, 18, 30, 50, 26],
    [50, 30, 14, 26, 38], [26, 46, 34, 14, 30],
]
let waveform = root.appendingPathComponent("aster-ai-listening-png")
try! FileManager.default.createDirectory(at: waveform, withIntermediateDirectories: true)
for (index, heights) in frames.enumerated() {
    let image = NSImage(size: size)
    image.lockFocus()
    NSColor.clear.setFill()
    NSRect(origin: .zero, size: size).fill()
    gold.setFill()
    for (bar, height) in heights.enumerated() {
        let rect = NSRect(x: 3 + CGFloat(bar * 13), y: (64 - CGFloat(height)) / 2,
                          width: 7, height: CGFloat(height))
        NSBezierPath(roundedRect: rect, xRadius: 3, yRadius: 3).fill()
    }
    image.unlockFocus()
    write(image, to: waveform.appendingPathComponent(String(format: "%02d.png", index + 1)))
}
