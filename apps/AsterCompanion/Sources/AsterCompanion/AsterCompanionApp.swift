import SwiftUI

final class AsterCompanionAppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        for url in urls {
            NotificationCenter.default.post(name: .asterCompanionOpenURL, object: url)
        }
    }
}

extension Notification.Name {
    static let asterCompanionOpenURL = Notification.Name("AsterCompanionOpenURL")
}

@main
struct AsterCompanionApp: App {
    @NSApplicationDelegateAdaptor(AsterCompanionAppDelegate.self) private var appDelegate
    @StateObject private var auth = AuthManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(auth)
                .onOpenURL { url in
                    auth.handleOpenURL(url)
                }
                .onReceive(NotificationCenter.default.publisher(for: .asterCompanionOpenURL)) { note in
                    if let url = note.object as? URL {
                        auth.handleOpenURL(url)
                    }
                }
        }
    }
}
