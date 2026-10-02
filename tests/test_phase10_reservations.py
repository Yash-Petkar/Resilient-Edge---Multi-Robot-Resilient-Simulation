import unittest

from core.coordination.reservation_manager import ReservationManager
from core.models.reservation import ReservationDecisionStatus, ReservationStatus


class TestPhase10Reservations(unittest.TestCase):
    def test_request_evaluate_grant_lifecycle(self):
        manager = ReservationManager()
        reservation = manager.request_cell_reservation("R1", (5, 5), 1.0, 3.0, priority=2)
        self.assertIsNotNone(reservation)
        assert reservation is not None
        self.assertEqual(reservation.status, ReservationStatus.GRANTED)
        self.assertEqual(reservation.reservation_id, "res_000001")

        active = manager.activate(reservation.reservation_id, current_time=1.5)
        self.assertEqual(active.status, ReservationStatus.ACTIVE)
        self.assertTrue(manager.is_cell_reserved((5, 5), 2.0))

        released = manager.release(reservation.reservation_id)
        self.assertEqual(released.status, ReservationStatus.RELEASED)
        self.assertFalse(manager.is_cell_reserved((5, 5), 2.0))

    def test_conflict_produces_authoritative_rejection_decision(self):
        manager = ReservationManager()
        first = manager.request_cell_reservation("R1", (2, 2), 10.0, 12.0, priority=1)
        self.assertIsNotNone(first)

        decision = manager.evaluate_request("R2", "cell:2,2", 11.0, 13.0, priority=2)
        self.assertEqual(decision.status, ReservationDecisionStatus.REJECTED)
        self.assertFalse(decision.granted)
        self.assertEqual(decision.conflicting_reservation_ids, ("res_000001",))
        self.assertIn("resource conflict", decision.reason)

        rejected = manager.request_cell_reservation("R2", (2, 2), 11.0, 13.0, priority=2)
        self.assertIsNone(rejected)
        self.assertEqual(len(manager.get_all_active()), 1)

    def test_non_overlapping_windows_can_coexist(self):
        manager = ReservationManager()
        r1 = manager.request_cell_reservation("R1", (1, 1), 0.0, 1.0)
        r2 = manager.request_cell_reservation("R2", (1, 1), 1.0, 2.0)
        self.assertIsNotNone(r1)
        self.assertIsNotNone(r2)

    def test_reverse_edge_swap_is_rejected(self):
        manager = ReservationManager()
        r1 = manager.request_edge_reservation("R1", (1, 1), (1, 2), 5.0, 6.0)
        self.assertIsNotNone(r1)
        r2 = manager.request_edge_reservation("R2", (1, 2), (1, 1), 5.0, 6.0)
        self.assertIsNone(r2)
        decision = manager.get_decision_log()[-1]
        self.assertEqual(decision.status, ReservationDecisionStatus.REJECTED)
        self.assertEqual(decision.reason, "reverse-edge conflict")

    def test_expiry_releases_resource(self):
        manager = ReservationManager()
        r1 = manager.request_cell_reservation("R1", (4, 4), 1.0, 2.0)
        self.assertIsNotNone(r1)
        assert r1 is not None
        manager.activate(r1.reservation_id, current_time=1.5)
        self.assertEqual(manager.clean_expired(2.0), 1)
        self.assertFalse(manager.is_cell_reserved((4, 4), 2.0))

        r2 = manager.request_cell_reservation("R2", (4, 4), 2.0, 3.0)
        self.assertIsNotNone(r2)

    def test_robot_release_clears_all_active_reservations(self):
        manager = ReservationManager()
        r1 = manager.request_cell_reservation("R1", (1, 1), 0.0, 5.0)
        r2 = manager.request_edge_reservation("R1", (1, 1), (1, 2), 0.0, 5.0)
        self.assertIsNotNone(r1)
        self.assertIsNotNone(r2)
        self.assertEqual(manager.release_all_for_robot("R1"), 2)
        self.assertEqual(manager.get_all_active(), [])

    def test_restore_preserves_active_reservations_and_sequence(self):
        manager = ReservationManager()
        r = manager.request_cell_reservation("R1", (7, 7), 2.0, 4.0)
        assert r is not None
        restored = ReservationManager()
        restored.restore([r.to_dict()])
        self.assertEqual(restored.get_all_active()[0].reservation_id, r.reservation_id)
        next_r = restored.request_cell_reservation("R2", (8, 8), 2.0, 4.0)
        assert next_r is not None
        self.assertEqual(next_r.reservation_id, "res_000002")


if __name__ == "__main__":
    unittest.main()
