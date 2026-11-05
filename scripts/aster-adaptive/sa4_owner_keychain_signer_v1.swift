import Foundation
import Security

// Dedicated owner-approval signer. The private RSA key is permanent in the
// login Keychain, device-local, and requires user presence for every use.
// This program can emit only the public JWK or a signature over one canonical
// SA4 owner-approval proof statement; it has no private-key export operation.

enum SignerError: Error, CustomStringConvertible {
    case invalid(String)
    var description: String {
        switch self { case .invalid(let value): return value }
    }
}

let keyTag = Data("com.elliottrook.aster.sa4.owner-approval.v1".utf8)
let proofFields: Set<String> = [
    "schema", "proof_scope", "signer_id", "signer_key_sha256",
    "payload_sha256", "signature_algorithm", "authority",
]

func hex(_ data: Data) -> String {
    data.map { String(format: "%02x", $0) }.joined()
}

func readLength(_ bytes: [UInt8], _ offset: inout Int) throws -> Int {
    guard offset < bytes.count else { throw SignerError.invalid("truncated DER length") }
    let first = Int(bytes[offset]); offset += 1
    if first < 0x80 { return first }
    let count = first & 0x7f
    guard count > 0, count <= 4, offset + count <= bytes.count else {
        throw SignerError.invalid("invalid DER length")
    }
    var value = 0
    for _ in 0..<count { value = (value << 8) | Int(bytes[offset]); offset += 1 }
    return value
}

func readInteger(_ bytes: [UInt8], _ offset: inout Int) throws -> [UInt8] {
    guard offset < bytes.count, bytes[offset] == 0x02 else {
        throw SignerError.invalid("expected DER integer")
    }
    offset += 1
    let count = try readLength(bytes, &offset)
    guard count > 0, offset + count <= bytes.count else {
        throw SignerError.invalid("truncated DER integer")
    }
    var value = Array(bytes[offset..<(offset + count)]); offset += count
    if value.count > 1, value[0] == 0 { value.removeFirst() }
    return value
}

func parsePublicKey(_ data: Data) throws -> (modulus: [UInt8], exponent: Int) {
    let bytes = [UInt8](data); var offset = 0
    guard offset < bytes.count, bytes[offset] == 0x30 else {
        throw SignerError.invalid("expected RSA public-key sequence")
    }
    offset += 1
    let sequenceLength = try readLength(bytes, &offset)
    guard offset + sequenceLength == bytes.count else {
        throw SignerError.invalid("non-canonical RSA public key")
    }
    let modulus = try readInteger(bytes, &offset)
    let exponentBytes = try readInteger(bytes, &offset)
    guard offset == bytes.count, modulus.count == 256,
          modulus[0] & 0x80 != 0, modulus.last! & 1 == 1,
          exponentBytes.count <= 4 else {
        throw SignerError.invalid("RSA public-key shape changed")
    }
    var exponent = 0
    for byte in exponentBytes { exponent = (exponent << 8) | Int(byte) }
    guard exponent == 65537 else { throw SignerError.invalid("RSA exponent changed") }
    return (modulus, exponent)
}

func canonicalProof(_ raw: Data) throws -> Data {
    let object = try JSONSerialization.jsonObject(with: raw)
    guard let value = object as? [String: Any], Set(value.keys) == proofFields,
          value["schema"] as? String == "aster-sa4-detached-proof.v1",
          value["proof_scope"] as? String == "owner-approval",
          value["signature_algorithm"] as? String == "rsa-pkcs1v1_5-sha256",
          value["authority"] as? String == "signature-only-no-effect",
          let signer = value["signer_id"] as? String,
          signer.range(of: "^[a-z0-9][a-z0-9._-]{2,127}$", options: .regularExpression) != nil,
          let keyDigest = value["signer_key_sha256"] as? String,
          keyDigest.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil,
          let payloadDigest = value["payload_sha256"] as? String,
          payloadDigest.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil else {
        throw SignerError.invalid("owner proof statement changed")
    }
    var canonical = try JSONSerialization.data(withJSONObject: value,
                                                 options: [.sortedKeys, .withoutEscapingSlashes])
    canonical.append(0x0a)
    guard canonical == raw else { throw SignerError.invalid("proof is not canonical JSON") }
    return canonical
}

func copyPrivateKey() throws -> SecKey {
    let query: [CFString: Any] = [
        kSecClass: kSecClassKey,
        kSecAttrApplicationTag: keyTag,
        kSecAttrKeyType: kSecAttrKeyTypeRSA,
        kSecReturnRef: true,
        kSecMatchLimit: kSecMatchLimitOne,
    ]
    var result: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &result)
    if status == errSecItemNotFound {
        throw SignerError.invalid("owner key is absent")
    }
    guard status == errSecSuccess, let key = result as! SecKey? else {
        throw SignerError.invalid("owner key query failed: \(status)")
    }
    return key
}

func createPrivateKey() throws -> SecKey {
    var accessError: Unmanaged<CFError>?
    guard let access = SecAccessControlCreateWithFlags(
        nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
        [.privateKeyUsage, .userPresence], &accessError) else {
        throw accessError!.takeRetainedValue()
    }
    let privateAttributes: [CFString: Any] = [
        kSecAttrIsPermanent: true,
        kSecAttrApplicationTag: keyTag,
        kSecAttrLabel: "Aster SA4 owner approval v1",
        kSecAttrAccessControl: access,
        kSecAttrIsExtractable: false,
        kSecAttrIsSensitive: true,
    ]
    let attributes: [CFString: Any] = [
        kSecAttrKeyType: kSecAttrKeyTypeRSA,
        kSecAttrKeySizeInBits: 2048,
        kSecPrivateKeyAttrs: privateAttributes,
    ]
    var error: Unmanaged<CFError>?
    guard let key = SecKeyCreateRandomKey(attributes as CFDictionary, &error) else {
        throw error!.takeRetainedValue()
    }
    return key
}

func publicJWK(_ privateKey: SecKey) throws -> Data {
    guard let publicKey = SecKeyCopyPublicKey(privateKey) else {
        throw SignerError.invalid("public key is unavailable")
    }
    var error: Unmanaged<CFError>?
    guard let external = SecKeyCopyExternalRepresentation(publicKey, &error) as Data? else {
        throw error!.takeRetainedValue()
    }
    let parsed = try parsePublicKey(external)
    let value: [String: Any] = [
        "e": parsed.exponent, "kty": "RSA", "n": hex(Data(parsed.modulus)),
    ]
    var result = try JSONSerialization.data(withJSONObject: value,
                                             options: [.sortedKeys, .withoutEscapingSlashes])
    result.append(0x0a)
    return result
}

func derLength(_ count: Int) -> [UInt8] {
    if count < 0x80 { return [UInt8(count)] }
    var value = count; var bytes: [UInt8] = []
    while value > 0 { bytes.insert(UInt8(value & 0xff), at: 0); value >>= 8 }
    return [0x80 | UInt8(bytes.count)] + bytes
}

func derInteger(_ value: [UInt8]) -> [UInt8] {
    let body = (value.first! & 0x80 != 0 ? [UInt8(0)] : []) + value
    return [0x02] + derLength(body.count) + body
}

func selfTest() throws {
    let modulus = [UInt8(0xc1)] + [UInt8](repeating: 0x11, count: 254) + [UInt8(0x13)]
    let body = derInteger(modulus) + derInteger([0x01, 0x00, 0x01])
    let parsed = try parsePublicKey(Data([0x30] + derLength(body.count) + body))
    guard parsed.modulus == modulus, parsed.exponent == 65537 else {
        throw SignerError.invalid("DER self-test failed")
    }
    let value: [String: Any] = [
        "schema": "aster-sa4-detached-proof.v1",
        "proof_scope": "owner-approval", "signer_id": "jason-owner",
        "signer_key_sha256": String(repeating: "a", count: 64),
        "payload_sha256": String(repeating: "b", count: 64),
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "authority": "signature-only-no-effect",
    ]
    var raw = try JSONSerialization.data(withJSONObject: value,
                                          options: [.sortedKeys, .withoutEscapingSlashes])
    raw.append(0x0a)
    guard try canonicalProof(raw) == raw else { throw SignerError.invalid("JSON self-test failed") }
    var rejected = false
    do { _ = try canonicalProof(Data(" \n".utf8) + raw) }
    catch { rejected = true }
    guard rejected else { throw SignerError.invalid("noncanonical proof accepted") }
    print("self-test: pass")
}

do {
    let arguments = CommandLine.arguments
    guard arguments.count >= 2 else { throw SignerError.invalid("usage: create|public|sign <canonical-proof>|self-test") }
    switch arguments[1] {
    case "self-test": try selfTest()
    case "create":
        guard arguments.count == 2 else { throw SignerError.invalid("create takes no argument") }
        do { _ = try copyPrivateKey(); throw SignerError.invalid("owner key already exists") }
        catch let error as SignerError where error.description == "owner key is absent" { }
        FileHandle.standardOutput.write(try publicJWK(createPrivateKey()))
    case "public":
        guard arguments.count == 2 else { throw SignerError.invalid("public takes no argument") }
        FileHandle.standardOutput.write(try publicJWK(copyPrivateKey()))
    case "sign":
        guard arguments.count == 3 else { throw SignerError.invalid("sign requires one canonical proof path") }
        let raw = try Data(contentsOf: URL(fileURLWithPath: arguments[2]), options: [.mappedIfSafe])
        guard raw.count <= 4096 else { throw SignerError.invalid("proof exceeds 4096 bytes") }
        let message = try canonicalProof(raw); let key = try copyPrivateKey()
        guard SecKeyIsAlgorithmSupported(key, .sign, .rsaSignatureMessagePKCS1v15SHA256) else {
            throw SignerError.invalid("owner key does not support required signature")
        }
        var error: Unmanaged<CFError>?
        guard let signature = SecKeyCreateSignature(
            key, .rsaSignatureMessagePKCS1v15SHA256, message as CFData, &error) as Data? else {
            throw error!.takeRetainedValue()
        }
        print(hex(signature))
    default: throw SignerError.invalid("unknown command")
    }
} catch {
    FileHandle.standardError.write(Data("error: \(error)\n".utf8))
    exit(1)
}
