import Darwin
import Foundation

/// Private, content-free experimental evidence. The dispatch journal remains authoritative.
enum LocalCodexEvaluationLog {
    enum LogError: Error { case invalid, unavailable }

    private struct Entry: Codable {
        let requestID: String
        let caseIndex: Int
        let event: String
        let manifestSHA256: String
        let observedAtUnix: Double
        let totalSeconds: Double?
        let turnSeconds: Double?
    }

    /// A saved request may advance only the case it originally submitted.
    static func submittedCase(in directory: URL, requestID: String,
                              allowedManifests: Set<String>) -> Int? {
        guard directory.isFileURL,
              directory.resolvingSymlinksInPath().path == directory.standardizedFileURL.path
        else { return nil }
        let path = directory.appendingPathComponent("evaluation-events.jsonl").path
        let fd = Darwin.open(path, O_RDONLY | O_NOFOLLOW)
        guard fd >= 0 else { return nil }
        defer { _ = Darwin.close(fd) }
        var info = stat()
        guard fstat(fd, &info) == 0,
              (info.st_mode & mode_t(S_IFMT)) == mode_t(S_IFREG),
              info.st_uid == geteuid(), info.st_mode & 0o077 == 0,
              info.st_size > 0, info.st_size <= 1_048_576 else { return nil }
        var data = Data()
        var buffer = [UInt8](repeating: 0, count: 8192)
        while true {
            let count = buffer.withUnsafeMutableBytes { bytes in
                Darwin.read(fd, bytes.baseAddress, bytes.count)
            }
            guard count >= 0 else { return nil }
            if count == 0 { break }
            guard data.count + count <= 1_048_576 else { return nil }
            data.append(contentsOf: buffer.prefix(count))
        }
        guard let raw = String(data: data, encoding: .utf8) else { return nil }
        var submitted: Int?
        for line in raw.split(separator: "\n") {
            guard let entry = try? JSONDecoder().decode(Entry.self, from: Data(line.utf8))
            else { return nil }
            guard entry.requestID == requestID else { continue }
            guard allowedManifests.contains(entry.manifestSHA256),
                  (0..<12).contains(entry.caseIndex) else { return nil }
            if entry.event == "submitted" {
                guard submitted == nil else { return nil }
                submitted = entry.caseIndex
            } else if let submitted, entry.caseIndex != submitted {
                return nil
            }
        }
        return submitted
    }

    static func append(in directory: URL, requestID: String, caseIndex: Int,
                       event: String, manifestSHA256: String,
                       totalSeconds: Double? = nil, turnSeconds: Double? = nil) throws {
        guard directory.isFileURL,
              directory.resolvingSymlinksInPath().path == directory.standardizedFileURL.path,
              requestID.hasPrefix("request-"), requestID.count == 44,
              (0..<12).contains(caseIndex),
              ["submitted", "completed", "uncertain", "recovered"].contains(event),
              manifestSHA256.count == 64,
              totalSeconds.map({ $0.isFinite && $0 >= 0 }) ?? true,
              turnSeconds.map({ $0.isFinite && $0 >= 0 }) ?? true
        else { throw LogError.invalid }
        var directoryInfo = stat()
        guard lstat(directory.path, &directoryInfo) == 0,
              (directoryInfo.st_mode & mode_t(S_IFMT)) == mode_t(S_IFDIR),
              directoryInfo.st_uid == geteuid(), directoryInfo.st_mode & 0o077 == 0
        else { throw LogError.unavailable }
        let path = directory.appendingPathComponent("evaluation-events.jsonl").path
        let fd = Darwin.open(path, O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW, 0o600)
        guard fd >= 0 else { throw LogError.unavailable }
        defer { _ = Darwin.close(fd) }
        var info = stat()
        guard fstat(fd, &info) == 0,
              (info.st_mode & mode_t(S_IFMT)) == mode_t(S_IFREG),
              info.st_uid == geteuid(), info.st_mode & 0o077 == 0
        else { throw LogError.unavailable }
        let entry = Entry(requestID: requestID, caseIndex: caseIndex, event: event,
                          manifestSHA256: manifestSHA256,
                          observedAtUnix: Date().timeIntervalSince1970,
                          totalSeconds: totalSeconds, turnSeconds: turnSeconds)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        var data = try encoder.encode(entry)
        data.append(0x0a)
        try data.withUnsafeBytes { bytes in
            guard let start = bytes.baseAddress else { throw LogError.unavailable }
            var offset = 0
            while offset < bytes.count {
                let count = Darwin.write(fd, start.advanced(by: offset), bytes.count - offset)
                guard count > 0 else { throw LogError.unavailable }
                offset += count
            }
        }
        guard fsync(fd) == 0 else { throw LogError.unavailable }
    }
}
