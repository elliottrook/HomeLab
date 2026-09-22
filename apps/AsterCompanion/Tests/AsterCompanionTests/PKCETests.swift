import Foundation
import XCTest
@testable import AsterCompanion

final class PKCETests: XCTestCase {
    /// RFC 7636 Appendix B's own worked example - if this passes, the
    /// challenge computation is byte-for-byte spec-correct, not just
    /// "looks plausible".
    func testCodeChallengeMatchesRFC7636ReferenceVector() {
        let verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        let expectedChallenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
        XCTAssertEqual(PKCE.codeChallenge(for: verifier), expectedChallenge)
    }

    func testRandomStringIsURLSafe() {
        let value = PKCE.randomURLSafeString(length: 64)
        let allowed = CharacterSet(charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        XCTAssertTrue(value.unicodeScalars.allSatisfy(allowed.contains))
        XCTAssertFalse(value.isEmpty)
    }

    func testRandomStringsAreNotRepeated() {
        let first = PKCE.randomURLSafeString(length: 32)
        let second = PKCE.randomURLSafeString(length: 32)
        XCTAssertNotEqual(first, second)
    }

    func testBase64URLEncodingHasNoPaddingOrUnsafeCharacters() {
        // 5 raw bytes forces standard base64 padding ("="), which must be stripped.
        let data = Data([0xFF, 0xFE, 0xFD, 0xFC, 0xFB])
        let encoded = data.base64URLEncodedString()
        XCTAssertFalse(encoded.contains("="))
        XCTAssertFalse(encoded.contains("+"))
        XCTAssertFalse(encoded.contains("/"))
    }
}
