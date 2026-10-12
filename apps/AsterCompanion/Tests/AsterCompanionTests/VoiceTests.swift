import XCTest
@testable import AsterCompanion

final class VoiceTests: XCTestCase {
    private func frame(_ metadata: [String: Any], payload: Data = Data()) throws -> Data {
        let header = try JSONSerialization.data(withJSONObject: metadata)
        var value = Data("AVS1".utf8)
        for size in [UInt32(header.count), UInt32(payload.count)] {
            var encoded = size.bigEndian
            withUnsafeBytes(of: &encoded) { value.append(contentsOf: $0) }
        }
        value.append(header); value.append(payload)
        return value
    }

    func testAVS1DecoderHandlesSplitFramesAndBuildsWAV() throws {
        let pcm = Data([0, 0, 1, 0])
        let wire = try frame(["type": "audio", "sample_format": "pcm_s16le", "sample_rate": 24000, "channels": 1], payload: pcm)
            + frame(["type": "end"])
        var decoder = AVS1Decoder()
        XCTAssertTrue(try decoder.append(wire.prefix(9)).isEmpty)
        let audio = try decoder.append(wire.dropFirst(9))
        XCTAssertEqual(audio.count, 1)
        XCTAssertEqual(String(data: audio[0].prefix(4), encoding: .ascii), "RIFF")
        XCTAssertEqual(audio[0].count, 44 + pcm.count)
        XCTAssertNoThrow(try decoder.finish())
    }

    func testAVS1DecoderRejectsOversizedAndIncompleteStreams() throws {
        var decoder = AVS1Decoder()
        XCTAssertThrowsError(try decoder.append(Data("NOPE00000000".utf8)))
        decoder = AVS1Decoder()
        _ = try decoder.append(try frame(["type": "audio", "sample_format": "pcm_s16le", "sample_rate": 24000, "channels": 1], payload: Data([0, 0])))
        XCTAssertThrowsError(try decoder.finish())
    }

    func testChunksPreserveLongReplyWithinServerLimit() {
        let text = String(repeating: "Aster speaks clearly. ", count: 300).trimmingCharacters(in: .whitespaces)
        let chunks = speechChunks(text)
        XCTAssertTrue(chunks.count > 1)
        XCTAssertTrue(chunks.allSatisfy { $0.unicodeScalars.count <= 1800 })
        XCTAssertEqual(chunks.joined(separator: " "), text)
    }

    func testChunksBoundCombiningScalarsAndUnbrokenText() {
        let text = String(repeating: "a\u{0301}", count: 3000)
        let chunks = speechChunks(text)
        XCTAssertTrue(chunks.allSatisfy { $0.unicodeScalars.count <= 1800 })
        XCTAssertEqual(chunks.joined(), text)
    }
}
