import unittest

from app.services.incoterm_rule_service import attribute_event, legs_hit_by_event
from app.services.relevance_engine import classify_event

BASE_CASE = {
    "case_id": "CASE-ATTR",
    "vessel": "CAPEMOLLINI",
    "route": "Shanghai -> South China Sea -> Chittagong -> Dhaka",
    "port_of_loading": "Shanghai",
    "port_of_discharge": "Chittagong",
    "final_destination": "Dhaka",
    "etd": "2026-11-25",
    "eta": "2026-12-08",
    "latest_shipment_date": "2026-11-30",
    "payment_method": "LC at sight",
    "incoterm": "CIF",
    "trade_perspective": "SELLER",
}

POL_TYPHOON = {
    "event_id": "EVT-POL",
    "title": "Typhoon approaching Shanghai",
    "type": "WEATHER",
    "event_time": "2026-11-24",
    "affected_ports": ["Shanghai"],
    "affected_region": "East China Sea",
    "severity": "High",
    "impact": "Potential departure delay near Shanghai route",
}

MAIN_CARRIAGE_STORM = {
    "event_id": "EVT-MAIN",
    "title": "Severe storm over South China Sea shipping lanes",
    "type": "WEATHER",
    "event_time": "2026-11-28",
    "affected_ports": [],
    "affected_region": "South China Sea",
    "severity": "High",
    "impact": "Vessels advised to avoid the area",
}

DESTINATION_STRIKE = {
    "event_id": "EVT-DEST",
    "title": "Chittagong port strike",
    "type": "PORT_STRIKE",
    "event_time": "2026-11-26",
    "affected_ports": ["Chittagong"],
    "affected_region": "Bangladesh",
    "severity": "High",
    "impact": "Port operation disruption",
}


class LegAttributionTest(unittest.TestCase):
    def test_pol_event_maps_to_port_of_loading_leg(self) -> None:
        self.assertIn("PORT_OF_LOADING", legs_hit_by_event(BASE_CASE, POL_TYPHOON))

    def test_corridor_event_maps_to_main_carriage_leg(self) -> None:
        self.assertEqual(legs_hit_by_event(BASE_CASE, MAIN_CARRIAGE_STORM), ["MAIN_CARRIAGE"])

    def test_destination_event_maps_to_destination_leg(self) -> None:
        self.assertIn("DESTINATION", legs_hit_by_event(BASE_CASE, DESTINATION_STRIKE))


class IncotermAttributionTest(unittest.TestCase):
    def test_cif_seller_pol_typhoon_is_cargo_and_payment_risk(self) -> None:
        attribution = attribute_event(BASE_CASE, POL_TYPHOON)
        self.assertTrue(attribution["our_cargo_risk"])
        self.assertTrue(attribution["our_payment_risk"])
        self.assertTrue(attribution["monitor_worthy"])

    def test_cif_seller_retains_duties_on_main_carriage(self) -> None:
        attribution = attribute_event(BASE_CASE, MAIN_CARRIAGE_STORM)
        self.assertFalse(attribution["our_cargo_risk"])
        self.assertTrue(attribution["controls_main_carriage"])
        self.assertTrue(attribution["monitor_worthy"])

    def test_fob_seller_main_carriage_event_is_not_our_risk(self) -> None:
        case = dict(BASE_CASE, incoterm="FOB", payment_method="TT in advance")
        attribution = attribute_event(case, MAIN_CARRIAGE_STORM)
        self.assertFalse(attribution["our_cargo_risk"])
        self.assertFalse(attribution["our_payment_risk"])
        self.assertFalse(attribution["monitor_worthy"])

    def test_fob_buyer_bears_main_carriage_risk(self) -> None:
        case = dict(BASE_CASE, incoterm="FOB", trade_perspective="BUYER")
        attribution = attribute_event(case, MAIN_CARRIAGE_STORM)
        self.assertTrue(attribution["our_cargo_risk"])
        self.assertTrue(attribution["monitor_worthy"])

    def test_cif_buyer_main_carriage_flags_minimum_cover_gap(self) -> None:
        case = dict(BASE_CASE, trade_perspective="BUYER")
        attribution = attribute_event(case, MAIN_CARRIAGE_STORM)
        self.assertTrue(attribution["our_cargo_risk"])
        self.assertIn("CIF_MIN_COVER_GAP", attribution["warnings"])

    def test_dap_seller_bears_risk_to_destination(self) -> None:
        case = dict(BASE_CASE, incoterm="DAP", payment_method="Open account")
        attribution = attribute_event(case, DESTINATION_STRIKE)
        self.assertTrue(attribution["our_cargo_risk"])
        self.assertEqual(attribution["cargo_risk_owner_by_leg"].get("DESTINATION"), "SELLER")

    def test_unknown_incoterm_fails_open(self) -> None:
        case = dict(BASE_CASE, incoterm="")
        attribution = attribute_event(case, MAIN_CARRIAGE_STORM)
        self.assertTrue(attribution["monitor_worthy"])
        self.assertIn("INCOTERM_UNKNOWN", attribution["warnings"])


SECURITY_EVENT = {
    "event_id": "EVT-SEC",
    "title": "Vessels attacked in South China Sea lanes",
    "type": "SECURITY",
    "event_time": "2026-11-28",
    "affected_ports": [],
    "affected_region": "South China Sea",
    "severity": "HIGH",
    "impact": "Transit slowdown may delay ETA for vessels in the area",
}


class RelevanceDowngradeTest(unittest.TestCase):
    def test_fob_seller_relevant_main_carriage_event_downgrades_to_watch(self) -> None:
        case = dict(BASE_CASE, incoterm="FOB", payment_method="TT in advance")
        result = classify_event(case, SECURITY_EVENT)
        self.assertEqual(result["classification"], "Watch")
        self.assertIn("incoterm_risk_not_ours", result["matched_factors"])

    def test_cif_seller_same_event_stays_relevant(self) -> None:
        result = classify_event(BASE_CASE, SECURITY_EVENT)
        self.assertEqual(result["classification"], "Relevant")
        self.assertNotIn("incoterm_risk_not_ours", result["matched_factors"])


if __name__ == "__main__":
    unittest.main()
