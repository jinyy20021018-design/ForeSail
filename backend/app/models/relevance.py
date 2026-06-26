from dataclasses import dataclass


@dataclass
class EventRelevanceResult:
    event_id: str
    title: str
    classification: str
    score: int
    matched_factors: list[str]
    explanation: str
    mapped_exposures: list[str]
