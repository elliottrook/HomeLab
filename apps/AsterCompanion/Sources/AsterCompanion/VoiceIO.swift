import AVFoundation
import Foundation

private struct VoiceFrameMetadata: Decodable {
    let type: String
    let sample_format: String?
    let sample_rate: Int?
    let channels: Int?
}

struct AVS1Decoder {
    private var buffer = Data()
    private(set) var ended = false

    mutating func append(_ data: Data) throws -> [Data] {
        buffer.append(data)
        var audio: [Data] = []
        while buffer.count >= 12 {
            guard buffer.prefix(4) == Data("AVS1".utf8) else {
                throw AsterClientError.stream("Invalid streamed speech framing.")
            }
            let headerSize = Int(buffer[4..<8].reduce(UInt32(0)) { ($0 << 8) | UInt32($1) })
            let payloadSize = Int(buffer[8..<12].reduce(UInt32(0)) { ($0 << 8) | UInt32($1) })
            guard headerSize <= 4096, payloadSize <= 2_097_152 else {
                throw AsterClientError.stream("Streamed speech frame exceeds limits.")
            }
            let frameSize = 12 + headerSize + payloadSize
            guard buffer.count >= frameSize else { break }
            let metadata = try JSONDecoder().decode(
                VoiceFrameMetadata.self, from: buffer.subdata(in: 12..<(12 + headerSize))
            )
            let payload = buffer.subdata(in: (12 + headerSize)..<frameSize)
            buffer.removeFirst(frameSize)
            switch metadata.type {
            case "audio":
                guard metadata.sample_format == "pcm_s16le", metadata.channels == 1,
                      let rate = metadata.sample_rate, (8_000...48_000).contains(rate),
                      payload.count.isMultiple(of: 2) else {
                    throw AsterClientError.stream("Unsupported streamed audio format.")
                }
                audio.append(pcm16WAV(payload, sampleRate: rate))
            case "end": ended = true
            case "cancelled": ended = true
            case "error": throw AsterClientError.stream("Speech synthesis failed.")
            default: throw AsterClientError.stream("Unknown streamed speech frame.")
            }
        }
        return audio
    }

    func finish() throws {
        guard buffer.isEmpty, ended else {
            throw AsterClientError.stream("Streamed speech ended unexpectedly.")
        }
    }
}

func pcm16WAV(_ pcm: Data, sampleRate: Int) -> Data {
    var wav = Data()
    func text(_ value: String) { wav.append(Data(value.utf8)) }
    func little<T: FixedWidthInteger>(_ value: T) {
        var encoded = value.littleEndian
        withUnsafeBytes(of: &encoded) { wav.append(contentsOf: $0) }
    }
    text("RIFF"); little(UInt32(36 + pcm.count)); text("WAVEfmt ")
    little(UInt32(16)); little(UInt16(1)); little(UInt16(1)); little(UInt32(sampleRate))
    little(UInt32(sampleRate * 2)); little(UInt16(2)); little(UInt16(16))
    text("data"); little(UInt32(pcm.count)); wav.append(pcm)
    return wav
}

/// Records a short voice question to a temp file and hands back its bytes.
/// Deliberately minimal - no level metering, no silence detection - the UI
/// drives start/stop explicitly via the mic button, matching the web
/// client's own tap-to-start/tap-to-stop flow.
@MainActor
final class VoiceRecorder {
    private var recorder: AVAudioRecorder?
    private var recordingURL: URL?

    func requestPermission() async -> Bool {
        switch AVCaptureDevice.authorizationStatus(for: .audio) {
        case .authorized:
            return true
        case .notDetermined:
            return await withCheckedContinuation { continuation in
                AVCaptureDevice.requestAccess(for: .audio) { granted in
                    continuation.resume(returning: granted)
                }
            }
        default:
            return false
        }
    }

    func startRecording() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".m4a")
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 16000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
        ]
        let recorder = try AVAudioRecorder(url: url, settings: settings)
        guard recorder.record() else {
            try? FileManager.default.removeItem(at: url)
            throw VoiceError.recordingFailed
        }
        self.recorder = recorder
        self.recordingURL = url
    }

    /// Stops recording and returns the captured audio, or nil if nothing
    /// was recorded (e.g. startRecording was never called or failed).
    func stopRecording() -> Data? {
        recorder?.stop()
        recorder = nil
        guard let url = recordingURL else { return nil }
        recordingURL = nil
        defer { try? FileManager.default.removeItem(at: url) }
        return try? Data(contentsOf: url)
    }
}

/// Plays back synthesized speech and lets the caller await completion, so
/// the UI can hold a "speaking" visual state for exactly as long as
/// playback actually runs.
@MainActor
final class VoicePlayer: NSObject, AVAudioPlayerDelegate {
    private var player: AVAudioPlayer?
    private var continuation: CheckedContinuation<Void, Error>?

    func play(data: Data) async throws {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            self.continuation = continuation
            do {
                let player = try AVAudioPlayer(data: data)
                player.delegate = self
                self.player = player
                if !player.play() {
                    finish(error: VoiceError.playbackFailed)
                }
            } catch {
                finish(error: error)
            }
        }
    }

    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor in self.finish(error: flag ? nil : VoiceError.playbackFailed) }
    }

    nonisolated func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        Task { @MainActor in self.finish(error: error ?? VoiceError.playbackFailed) }
    }

    private func finish(error: Error? = nil) {
        if let error { continuation?.resume(throwing: error) }
        else { continuation?.resume() }
        continuation = nil
        player = nil
    }
}

private enum VoiceError: LocalizedError {
    case recordingFailed, playbackFailed
    var errorDescription: String? {
        switch self {
        case .recordingFailed: return "Could not start recording. Please try again."
        case .playbackFailed: return "Could not play the spoken reply. Please try again."
        }
    }
}

/// Limit Unicode scalars (the API counts code points), not Swift grapheme clusters.
func speechChunks(_ text: String, limit: Int = 1800) -> [String] {
    precondition(limit > 0)
    var remaining = text.trimmingCharacters(in: .whitespacesAndNewlines)
    var chunks: [String] = []
    while remaining.unicodeScalars.count > limit {
        let boundary = remaining.unicodeScalars.index(remaining.unicodeScalars.startIndex, offsetBy: limit)
        let prefix = remaining[..<boundary]
        let split = prefix.lastIndex(of: " ").flatMap { index in
            remaining[..<index].unicodeScalars.count >= limit / 2 ? index : nil
        } ?? boundary
        chunks.append(String(remaining[..<split]))
        remaining = String(remaining[split...]).trimmingCharacters(in: .whitespacesAndNewlines)
    }
    if !remaining.isEmpty { chunks.append(remaining) }
    return chunks
}
