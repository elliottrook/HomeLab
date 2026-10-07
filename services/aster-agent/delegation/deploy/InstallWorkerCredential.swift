// Candidate provisioning helper. Default does not access Keychain.
// --install is reserved for a separately approved private controller pipe.
// No secret command argument, environment variable, plaintext file or output.
import Foundation
import Security

let service = "com.elliottrook.aster-codex-worker"
let account = "authentik-app-password"

func fail() -> Never {
    FileHandle.standardError.write(Data("Worker credential installation unconfirmed; reconcile before retry.\n".utf8))
    exit(1)
}

guard CommandLine.arguments == [CommandLine.arguments[0], "--install"] else {
    print("{\"enabled\":false,\"keychain_accessed\":false}")
    exit(CommandLine.arguments.count == 1 ? 0 : 2)
}
// No interactive paste path: the approved controller must supply an owned pipe.
guard isatty(STDIN_FILENO) == 0 else { fail() }
var bytes = Data()
while true {
    let chunk = FileHandle.standardInput.readData(ofLength: 1024)
    if chunk.isEmpty { break }
    bytes.append(chunk)
    guard bytes.count <= 16384 else { fail() }
}
guard let password = String(data: bytes, encoding: .utf8), !password.isEmpty,
      !password.contains(where: { $0.isWhitespace }) else { fail() }

// Create-only: never replace the human Companion login or an earlier worker item.
let query: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrService as String: service,
    kSecAttrAccount as String: account,
    kSecMatchLimit as String: kSecMatchLimitOne,
    kSecUseAuthenticationUI as String: kSecUseAuthenticationUIFail,
]
let existing = SecItemCopyMatching(query as CFDictionary, nil)
guard existing == errSecItemNotFound else { fail() }

// Explicit reader, not an allow-all-applications ACL. This remains a same-user
// boundary: other code run as Jason can invoke security, so model tools stay off.
var reader: SecTrustedApplication?
guard SecTrustedApplicationCreateFromPath("/usr/bin/security", &reader) == errSecSuccess,
      let reader else { fail() }
var access: SecAccess?
guard SecAccessCreate("Aster worker Authentik credential" as CFString,
                      [reader] as CFArray, &access) == errSecSuccess,
      let access else { fail() }
let attributes: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrService as String: service,
    kSecAttrAccount as String: account,
    kSecAttrLabel as String: "Aster Codex worker — 24-hour pilot",
    kSecAttrSynchronizable as String: false,
    kSecAttrAccess as String: access,
    kSecValueData as String: bytes,
]
guard SecItemAdd(attributes as CFDictionary, nil) == errSecSuccess else { fail() }
print("{\"created\":true,\"overwritten\":false,\"roundtrip_verified\":false}")
// Controller must verify the fixed reader's round trip privately before activation.
