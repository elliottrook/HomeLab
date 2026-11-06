import copy,unittest
import sa4_fixed_runner_inactive_install_plan_v1 as plan
import sa4_fixed_runner_inactive_install_result_v1 as result
import sa4_single_file_repair_contract_v1 as contract
def value(): return {"schema":"aster-sa4-fixed-runner-inactive-install-result.v1","destination":plan.DESTINATION,"after_sha256":plan.AFTER_SHA256,"owner":"root","group":"root","mode":"0644","link_count":1,"regular_file":True,"isolated_import":True,"runtime_state_absent":True,"runner_invoked":False,"authority_touched":False,"target_touched":False,"service_actions":[],"production_healthy":True,"rollback_ready":True,"automatic_routing":"off"}
class Tests(unittest.TestCase):
    def test_exact(self): self.assertTrue(result.validate(contract.canonical(value()))["inactive"])
    def test_effect_drift(self):
        for key in ("runner_invoked","authority_touched","target_touched"):
            changed=value(); changed[key]=True
            with self.assertRaises(ValueError): result.validate(contract.canonical(changed))
    def test_metadata_drift(self):
        changed=value(); changed["link_count"]=2
        with self.assertRaises(ValueError): result.validate(contract.canonical(changed))
if __name__=="__main__": unittest.main()
