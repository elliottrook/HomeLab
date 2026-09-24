import XCTest
@testable import AsterCompanion

@MainActor
final class ReplyProgressTests: XCTestCase {
    /// Matches the frames progress_chat emits (services/aster-agent/aster_agent.py).
    private func event(_ json: String) -> ChatStreamEvent? {
        let object = try! JSONSerialization.jsonObject(with: Data(json.utf8)) as! [String: Any]
        return ChatStreamEvent.progress(from: object)
    }

    func testIgnoresOrdinaryChatChunks() {
        XCTAssertNil(event(#"{"object":"chat.completion.chunk","choices":[]}"#))
    }

    func testStepsTokensAndUsageBecomeTheReplySummary() throws {
        let progress = ReplyProgress()
        progress.begin()
        for frame in [
            #"{"object":"aster.progress","type":"step","id":"s1","tool":"get_lab_health","label":"Reading lab health","done_label":"Read lab health","state":"running"}"#,
            #"{"object":"aster.progress","type":"step","id":"s1","state":"done","ms":1200}"#,
            #"{"object":"aster.progress","type":"step","id":"s2","tool":"context","label":"Reading context","done_label":"Read context","state":"running"}"#,
        ] {
            progress.handle(try XCTUnwrap(event(frame)))
        }
        XCTAssertTrue(progress.headline(at: Date()).hasPrefix("Reading context…"))
        progress.handle(.token("Hi"))
        XCTAssertTrue(progress.headline(at: Date()).hasPrefix("Answering"))
        progress.handle(try XCTUnwrap(event(#"{"object":"aster.progress","type":"step","id":"s2","state":"done","ms":900}"#)))
        progress.handle(try XCTUnwrap(event(
            #"{"object":"aster.progress","type":"usage","prompt_tokens":1797,"completion_tokens":58,"tokens_per_second":6.89}"#)))

        let summary = progress.finish()
        XCTAssertFalse(progress.isActive)
        XCTAssertEqual(summary.stepLines, ["✓ Read lab health · 1.2s", "✓ Read context · 0.9s"])
        XCTAssertTrue(try XCTUnwrap(summary.steps).hasPrefix("✓ Read lab health, read context · "))
        XCTAssertTrue(summary.stats.hasSuffix(" · \(1797.formatted()) in / 58 out · 6.9 tok/s"), summary.stats)
    }
}
