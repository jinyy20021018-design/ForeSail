from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExternalEvent:
    event_id: str
    title: str
    type: str
    event_time: str
    affected_vessel: Optional[str]
    affected_ports: list[str]
    affected_region: str
    severity: str
    confidence: float
    source: str
    impact: str
    expected_classification: str
    old_eta: Optional[str] = None
    new_eta: Optional[str] = None
    delay_days: Optional[int] = None
    extra: dict = field(default_factory=dict)
