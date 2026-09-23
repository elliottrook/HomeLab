import AppKit
import UserNotifications

/// Deliberately contains no reply text, report details, URLs or action payloads.
enum CompanionNotice: String {
    case replyReady, labAlert

    var body: String {
        switch self {
        case .replyReady: return "Your reply is ready. Open Aster Companion to read it."
        case .labAlert: return "Your lab needs attention. Open Aster Companion to review it."
        }
    }
}

@MainActor
final class CompanionNotifications: ObservableObject {
    @Published private(set) var enabled = UserDefaults.standard.bool(forKey: "aster_notifications_enabled")
    @Published private(set) var status = "Notifications are off."
    private let center = UNUserNotificationCenter.current()

    func refresh() async {
        let settings = await center.notificationSettings()
        if settings.authorizationStatus == .denied {
            status = "Notifications are blocked in System Settings."
        } else if enabled && settings.authorizationStatus == .authorized {
            status = "Notifications are on while Aster is running."
        } else {
            status = "Notifications are off."
        }
    }

    /// Called only by the explicit Enable button, never at launch.
    func enable() async {
        do {
            enabled = try await center.requestAuthorization(options: [.alert, .sound])
            UserDefaults.standard.set(enabled, forKey: "aster_notifications_enabled")
            await refresh()
        } catch {
            status = "Could not enable notifications. Try again in System Settings."
        }
    }

    func disable() {
        enabled = false
        UserDefaults.standard.set(false, forKey: "aster_notifications_enabled")
        center.removeAllPendingNotificationRequests()
        center.removeAllDeliveredNotifications()
        status = "Notifications are off."
    }

    func post(_ notice: CompanionNotice, eventID: String) async {
        guard enabled, !NSApplication.shared.isActive else { return }
        let settings = await center.notificationSettings()
        guard settings.authorizationStatus == .authorized, enabled else {
            await refresh()
            return
        }
        let content = UNMutableNotificationContent()
        content.title = "Aster Companion"
        content.body = notice.body
        content.sound = .default
        // Stable event IDs replace a repeated event instead of stacking copies.
        let request = UNNotificationRequest(identifier: eventID, content: content, trigger: nil)
        do {
            try await center.add(request)
        } catch {
            status = "Notification delivery failed. Your conversation is still available."
        }
    }
}

struct CompanionLabHealth: Decodable {
    struct Check: Decodable {
        let name: String
        let status: String
        let summary: String
    }
    let status: String
    let fingerprint: String?
    let reason: String?
    let checks: [Check]
}
