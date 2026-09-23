import AVFoundation
import Foundation

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
