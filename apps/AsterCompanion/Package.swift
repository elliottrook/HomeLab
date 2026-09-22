// swift-tools-version: 5.10
import PackageDescription

let package = Package(
    name: "AsterCompanion",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "AsterCompanion",
            path: "Sources/AsterCompanion",
            resources: [.copy("Resources/AsterOrb.png")]
        ),
        .testTarget(
            name: "AsterCompanionTests",
            dependencies: ["AsterCompanion"],
            path: "Tests/AsterCompanionTests"
        ),
    ]
)
