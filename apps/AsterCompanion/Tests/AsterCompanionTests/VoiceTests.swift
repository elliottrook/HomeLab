import XCTest
@testable import AsterCompanion

final class VoiceTests: XCTestCase {
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
