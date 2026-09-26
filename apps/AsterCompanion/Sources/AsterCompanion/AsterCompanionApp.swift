import SwiftUI

final class AsterCompanionAppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }
}

@main
struct AsterCompanionApp: App {
    @NSApplicationDelegateAdaptor(AsterCompanionAppDelegate.self) private var appDelegate
    @StateObject private var auth = AuthManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(auth)
        }
    }
}
