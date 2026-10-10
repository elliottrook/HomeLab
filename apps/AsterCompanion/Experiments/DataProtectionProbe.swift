import Foundation
import Security

// Disposable experiment only. Never use the live Companion service/account.
private let service = "com.elliottrook.aster-companion.synthetic-dp-probe-20261009"
private let account = "disposable"
private let fixture = Data("ASTER_SYNTHETIC_DP_PROBE_20261009".utf8)

@main
struct DataProtectionProbe {
    static func main() {
        guard CommandLine.arguments.count == 2 else {
            fputs("usage: probe add|read|delete\n", stderr)
            exit(64)
        }
        let action = CommandLine.arguments[1]
        var query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecUseDataProtectionKeychain as String: true,
        ]
        let status: OSStatus
        switch action {
        case "add":
            query[kSecValueData as String] = fixture
            query[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
            status = SecItemAdd(query as CFDictionary, nil)
        case "read":
            query[kSecReturnData as String] = true
            query[kSecMatchLimit as String] = kSecMatchLimitOne
            var value: AnyObject?
            status = SecItemCopyMatching(query as CFDictionary, &value)
            if status == errSecSuccess, let data = value as? Data, data != fixture {
                fputs("unexpected synthetic fixture\n", stderr)
                exit(65)
            }
        case "delete":
            status = SecItemDelete(query as CFDictionary)
        default:
            fputs("unknown action\n", stderr)
            exit(64)
        }
        // Only a status code and synthetic probe version are printed.
        #if PROBE_UPDATE
        let version = 2
        #else
        let version = 1
        #endif
        print("version=\(version) action=\(action) status=\(status)")
        exit(status == errSecSuccess ? 0 : 1)
    }
}
