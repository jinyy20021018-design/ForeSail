from dataclasses import dataclass


@dataclass
class ShipmentWindow:
    etd: str
    eta: str
    latest_shipment_date: str


@dataclass
class CaseWatchProfile:
    case_id: str
    watched_vessel: str
    watched_ports: list[str]
    watched_route_regions: list[str]
    shipment_window: ShipmentWindow
    deadline_sensitivity: list[str]
    risk_categories: list[str]
    alert_rules: list[str]
