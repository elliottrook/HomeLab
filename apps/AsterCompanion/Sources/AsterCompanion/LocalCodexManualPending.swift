import Darwin
import Foundation

/// One durable, content-free admission record for the disabled manual candidate.
/// A malformed record blocks new sends; the dispatch journal remains authoritative.
enum LocalCodexManualPending {
    enum RecordError: Error { case unavailable, invalid, alreadyPending }

    private struct Record: Codable {
        let requestID: String
        let manifestSHA256: String
    }

    private static func path(in directory: URL) -> String {
        directory.appendingPathComponent("manual-pending.json").path
    }

    static func load(in directory: URL) throws -> String? {
        let fd = Darwin.open(path(in: directory), O_RDONLY | O_NOFOLLOW)
        if fd < 0 {
            if errno == ENOENT { return nil }
            throw RecordError.unavailable
        }
        defer { _ = Darwin.close(fd) }
        var info = stat()
        guard fstat(fd, &info) == 0,
              (info.st_mode & mode_t(S_IFMT)) == mode_t(S_IFREG),
              info.st_uid == geteuid(), info.st_mode & 0o077 == 0,
              info.st_size > 0, info.st_size <= 512 else { throw RecordError.invalid }
        var bytes = [UInt8](repeating: 0, count: Int(info.st_size))
        let count = bytes.withUnsafeMutableBytes { Darwin.read(fd, $0.baseAddress, $0.count) }
        guard count == bytes.count,
              let record = try? JSONDecoder().decode(Record.self, from: Data(bytes)),
              record.requestID.hasPrefix("request-"), record.requestID.count == 44,
              record.manifestSHA256.count == 64 else { throw RecordError.invalid }
        return record.requestID
    }

    static func claim(in directory: URL, requestID: String, manifestSHA256: String) throws {
        guard requestID.hasPrefix("request-"), requestID.count == 44,
              manifestSHA256.count == 64 else { throw RecordError.invalid }
        let data = try JSONEncoder().encode(Record(requestID: requestID,
                                                   manifestSHA256: manifestSHA256))
        let fd = Darwin.open(path(in: directory), O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0o600)
        if fd < 0 {
            if errno == EEXIST { throw RecordError.alreadyPending }
            throw RecordError.unavailable
        }
        defer { _ = Darwin.close(fd) }
        let written = data.withUnsafeBytes { Darwin.write(fd, $0.baseAddress, $0.count) }
        guard written == data.count, fsync(fd) == 0 else { throw RecordError.unavailable }
    }

    static func clearCompleted(in directory: URL, requestID: String) throws {
        guard try load(in: directory) == requestID else { throw RecordError.invalid }
        guard unlink(path(in: directory)) == 0 else { throw RecordError.unavailable }
    }
}
