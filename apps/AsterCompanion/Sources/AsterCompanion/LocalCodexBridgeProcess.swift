import Foundation
import Darwin

/// One-shot local helper used only by explicitly flagged review surfaces.
enum LocalCodexBridgeProcess {
    enum BridgeError: Error { case unavailable, invalidBundle, invalidRequest, timeout, failed, oversized }

    static func packagedScript(in bundle: Bundle = .main) throws -> URL {
        guard let root = bundle.resourceURL else { throw BridgeError.invalidBundle }
        let script = root.appendingPathComponent("LocalCodexBridge/local_bridge_cli.py")
        guard FileManager.default.fileExists(atPath: script.path),
              script.resolvingSymlinksInPath().path.hasPrefix(root.resolvingSymlinksInPath().path + "/")
        else { throw BridgeError.invalidBundle }
        return script
    }

    static func inspectBundled(prepare: Bool = false) throws -> Data {
        try inspect(script: packagedScript(), prepare: prepare)
    }

    static func recordedStatus(requestID: String, stateDirectory: URL) throws -> Data {
        guard requestID.hasPrefix("request-"),
              stateDirectory.isFileURL,
              stateDirectory.resolvingSymlinksInPath().path == stateDirectory.standardizedFileURL.path
        else { throw BridgeError.invalidRequest }
        return try launch(script: packagedScript(),
                          arguments: ["--status", "--state-dir", stateDirectory.path,
                                      "--request-id", requestID],
                          input: nil, timeout: 8)
    }

    static func privateStateDirectory(base: URL? = nil) throws -> URL {
        let files = FileManager.default
        guard let support = base ?? files.urls(for: .applicationSupportDirectory,
                                             in: .userDomainMask).first,
              support.isFileURL,
              support.resolvingSymlinksInPath().path == support.standardizedFileURL.path else {
            throw BridgeError.unavailable
        }
        let app = support.appendingPathComponent("AsterCompanion", isDirectory: true)
        let state = app.appendingPathComponent("LocalCodexPilot", isDirectory: true)
        for directory in [app, state] {
            try files.createDirectory(at: directory, withIntermediateDirectories: false,
                                      attributes: [.posixPermissions: 0o700])
            let attrs = try files.attributesOfItem(atPath: directory.path)
            guard directory.resolvingSymlinksInPath().path == directory.standardizedFileURL.path,
                  let owner = attrs[.ownerAccountID] as? NSNumber,
                  owner.intValue == Int(geteuid()),
                  let mode = attrs[.posixPermissions] as? NSNumber,
                  mode.intValue & 0o077 == 0 else {
                throw BridgeError.invalidBundle
            }
        }
        return state
    }

    /// Call only from a reviewed UI action off the main thread.
    static func submitBundled(_ request: ReviewedCodexRequest,
                              approvedHash: String, stateDirectory: URL) throws -> Data {
        try submit(script: packagedScript(), request: request,
                   approvedHash: approvedHash, stateDirectory: stateDirectory)
    }

    static func submit(script: URL, request: ReviewedCodexRequest,
                       approvedHash: String, stateDirectory: URL,
                       timeout: TimeInterval = 190) throws -> Data {
        let hex = CharacterSet(charactersIn: "0123456789abcdef")
        guard approvedHash.count == 64,
              approvedHash.unicodeScalars.allSatisfy({ hex.contains($0) }),
              stateDirectory.isFileURL, stateDirectory.path.hasPrefix("/"),
              stateDirectory.resolvingSymlinksInPath().path == stateDirectory.standardizedFileURL.path
        else { throw BridgeError.invalidRequest }
        let frame = try AIPAMCoding.encoder.encode(request)
        guard frame.count <= 20000 else { throw BridgeError.invalidRequest }
        return try launch(script: script, arguments: ["--run", "--approved-sha256", approvedHash,
                                                      "--state-dir", stateDirectory.path],
                          input: frame, timeout: timeout)
    }

    /// Inert default or metadata-only preparation; no model turn in either mode.
    static func inspect(script: URL, prepare: Bool = false, timeout: TimeInterval = 15) throws -> Data {
        guard timeout > 0, timeout <= 30 else { throw BridgeError.invalidRequest }
        return try launch(script: script, arguments: prepare ? ["--prepare"] : [],
                          input: nil, timeout: timeout)
    }

    private static func launch(script: URL, arguments: [String], input: Data?,
                               timeout: TimeInterval) throws -> Data {
        guard timeout > 0, timeout <= 190, script.isFileURL,
              FileManager.default.fileExists(atPath: script.path) else {
            throw BridgeError.invalidBundle
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        process.arguments = ["-E", "-S", script.path] + arguments
        let codexDirectory = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS"
        process.environment = [
            "HOME": NSHomeDirectory(),
            "PATH": codexDirectory + ":/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "TMPDIR": FileManager.default.temporaryDirectory.path
        ]
        process.currentDirectoryURL = FileManager.default.temporaryDirectory
        let output = Pipe()
        process.standardOutput = output
        process.standardError = FileHandle.nullDevice
        let inputPipe = input == nil ? nil : Pipe()
        process.standardInput = inputPipe ?? FileHandle.nullDevice
        let finished = DispatchSemaphore(value: 0)
        process.terminationHandler = { _ in finished.signal() }
        do { try process.run() }
        catch { throw BridgeError.unavailable }
        let drained = DispatchGroup()
        var captured = Data()
        var overflow = false
        drained.enter()
        DispatchQueue.global(qos: .userInitiated).async {
            while true {
                let chunk = output.fileHandleForReading.availableData
                if chunk.isEmpty { break }
                if captured.count + chunk.count > 65536 {
                    overflow = true
                } else if !overflow {
                    captured.append(chunk)
                }
                // Keep draining after the bound so the child can exit cleanly.
            }
            drained.leave()
        }
        if let inputPipe, let input {
            DispatchQueue.global(qos: .userInitiated).async {
                try? inputPipe.fileHandleForWriting.write(contentsOf: input)
                try? inputPipe.fileHandleForWriting.close()
            }
        }
        if finished.wait(timeout: .now() + timeout) == .timedOut {
            process.terminate()
            if finished.wait(timeout: .now() + 2) == .timedOut {
                kill(process.processIdentifier, SIGKILL)
                _ = finished.wait(timeout: .now() + 2)
            }
            throw BridgeError.timeout
        }
        guard drained.wait(timeout: .now() + 2) == .success else { throw BridgeError.failed }
        guard process.terminationStatus == 0 else { throw BridgeError.failed }
        guard !overflow else { throw BridgeError.oversized }
        return captured
    }
}
