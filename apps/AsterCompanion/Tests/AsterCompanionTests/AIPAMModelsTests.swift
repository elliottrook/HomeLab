import XCTest
@testable import AsterCompanion

final class AIPAMModelsTests: XCTestCase {
    func testDecodesPendingApprovalWithoutSecretBearingFields() throws {
        let data = Data(#"[{"request_id":"req-1","agent_id":"agent-hermes","capability":"lab.doctor.run","risk_class":"yellow","payload_hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","created_at":1,"expires_at":2,"display":{"reason":"diagnose","target":"doctor","effect":"one run","rollback":"revoke"},"token":"must-not-be-modeled"}]"#.utf8)
        let items = try AIPAMCoding.decoder.decode([AIPAMPendingApproval].self, from: data)
        XCTAssertEqual(items.first?.capability, "lab.doctor.run")
        XCTAssertEqual(items.first?.display.effect, "one run")
        XCTAssertFalse(items.first?.requiresFreshAuthentication ?? true)
        XCTAssertFalse(String(describing: items.first!).contains("must-not-be-modeled"))
    }

    func testDecodesManagementSnapshotAndRedFreshness() throws {
        let data = Data(#"{"global_enabled":true,"agents":[{"agent_id":"agent-hermes","unix_uid":995,"state":"operator","created_at":1,"capability_count":1,"capabilities":[{"capability":"network.change","risk_class":"red","service_id":"synthetic"}]}],"services":[{"service_id":"synthetic","execution_mode":"proxy","enabled":1,"created_at":1,"credential_type":"none","custody_identifier":"none","credential_scope":"synthetic-only","rotation_due":"not-applicable","revocation_method":"disable-service","health":"healthy","capability_count":1}],"active_requests":[]}"#.utf8)
        let snapshot = try AIPAMCoding.decoder.decode(AIPAMSnapshot.self, from: data)
        XCTAssertTrue(snapshot.globalEnabled)
        XCTAssertTrue(snapshot.services[0].isEnabled)
        XCTAssertEqual(snapshot.agents[0].capabilities[0].riskClass, "red")

        let pending = Data(#"{"request_id":"req-red","agent_id":"agent-hermes","capability":"network.change","risk_class":"red","payload_hash":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","created_at":1,"expires_at":2,"display":{}}"#.utf8)
        XCTAssertTrue(try AIPAMCoding.decoder.decode(AIPAMPendingApproval.self, from: pending).requiresFreshAuthentication)
    }

    func testManagementActionEncodesOnlyAllowlistedShape() throws {
        let action = AIPAMManagementAction(action: "service_enabled", target: "lab-operations", enabled: false)
        let object = try XCTUnwrap(JSONSerialization.jsonObject(with: AIPAMCoding.encoder.encode(action)) as? [String: Any])
        XCTAssertEqual(Set(object.keys), ["action", "target", "enabled"])
        XCTAssertEqual(object["target"] as? String, "lab-operations")
    }

    func testDecodesHistoryAndAuditShapes() throws {
        let history = Data(#"[{"request_id":"r","agent_id":"a","capability":"c","risk_class":"green","payload_hash":"h","status":"consumed","created_at":1,"expires_at":2,"approved_at":1,"consumed_at":2,"revoked_at":null,"approval_actor":null,"approval_auth_time":null,"approval_assurance":null,"display":{}}]"#.utf8)
        XCTAssertEqual(try AIPAMCoding.decoder.decode([AIPAMHistoryItem].self, from: history)[0].status, "consumed")
        let audit = Data(#"[{"sequence":7,"occurred_at":3,"event":"request.consume","actor":"agent-hermes","request_id":"r","capability":"c","risk_class":"green","payload_hash":"h","outcome":"consumed"}]"#.utf8)
        XCTAssertEqual(try AIPAMCoding.decoder.decode([AIPAMAuditItem].self, from: audit)[0].event, "request.consume")
    }
}
