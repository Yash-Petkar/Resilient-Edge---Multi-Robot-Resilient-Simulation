import unittest

from backend.api.permissions import permission_for_request, role_allows


class TestRolePermissions(unittest.TestCase):
    def test_observer_is_read_only(self):
        self.assertTrue(role_allows("OBSERVER", "read"))
        self.assertTrue(role_allows("OBSERVER", "audit_read"))
        for permission in (
            "simulation_control",
            "task_dispatch",
            "fault_injection",
            "recovery",
            "experiments",
            "settings",
            "database_admin",
            "destructive",
        ):
            self.assertFalse(role_allows("OBSERVER", permission))

    def test_viewer_is_read_only(self):
        self.assertTrue(role_allows("VIEWER", "read"))
        for permission in ("simulation_control", "task_dispatch", "fault_injection", "recovery", "experiments", "settings", "database_admin", "user_admin", "destructive", "audit_read"):
            self.assertFalse(role_allows("VIEWER", permission))

    def test_operator_can_operate_but_not_administer(self):
        for permission in (
            "simulation_control",
            "task_dispatch",
            "fault_injection",
            "recovery",
            "experiments",
        ):
            self.assertTrue(role_allows("OPERATOR", permission))
        for permission in ("settings", "database_admin", "user_admin", "destructive"):
            self.assertFalse(role_allows("OPERATOR", permission))

    def test_endpoint_policy_distinguishes_operator_and_admin_actions(self):
        self.assertEqual(permission_for_request("GET", "/api/admin/audit"), "audit_read")
        self.assertEqual(permission_for_request("POST", "/api/tasks"), "task_dispatch")
        self.assertEqual(permission_for_request("POST", "/api/faults"), "fault_injection")
        self.assertEqual(permission_for_request("POST", "/api/scenarios/run"), "experiments")
        self.assertEqual(permission_for_request("POST", "/api/settings"), "settings")
        self.assertEqual(permission_for_request("POST", "/api/database/clear"), "database_admin")
        self.assertEqual(permission_for_request("POST", "/api/snapshot/restore"), "destructive")
        self.assertEqual(permission_for_request("POST", "/api/snapshot/save"), "read")
        self.assertIsNone(permission_for_request("POST", "/api/auth/switch-role"))
        self.assertEqual(permission_for_request("POST", "/api/unknown/mutation"), "destructive")


if __name__ == "__main__":
    unittest.main()
