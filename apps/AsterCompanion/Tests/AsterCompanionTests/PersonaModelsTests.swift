import XCTest
@testable import AsterCompanion

final class PersonaModelsTests: XCTestCase {
    /// Matches the real shape GET /v1/personas returns
    /// (services/aster-agent/aster_agent.py) - guards against the client
    /// and backend silently drifting on field names.
    func testDecodesRealBackendShape() throws {
        let json = """
        {
          "default": "sysadmin",
          "personas": [
            {
              "id": "sysadmin",
              "label": "Sysadmin Aster",
              "tools": [
                {"name": "get_current_time", "description": "Get the current local date and time."}
              ]
            },
            {
              "id": "media",
              "label": "Media Automation Aster",
              "tools": [
                {"name": "get_arr_report", "description": "Read the latest sanitized ARR aggregate report."}
              ]
            }
          ]
        }
        """.data(using: .utf8)!

        let decoded = try JSONDecoder().decode(PersonasResponse.self, from: json)
        XCTAssertEqual(decoded.default, "sysadmin")
        XCTAssertEqual(decoded.personas.map(\.id), ["sysadmin", "media"])
        XCTAssertEqual(decoded.personas[1].label, "Media Automation Aster")
        XCTAssertEqual(decoded.personas[1].tools.first?.name, "get_arr_report")
    }
}
