from dataclasses import dataclass


@dataclass
class RiskExposure:
    category: str
    impact: str
    severity: str
    evidence_event_ids: list[str]


@dataclass
class RiskSummary:
    triggered: bool
    trigger_events: list[str]
    exposures: list[RiskExposure]
