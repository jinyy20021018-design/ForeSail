from dataclasses import dataclass


@dataclass
class RecommendedAction:
    action_id: str
    title: str
    owner_role: str
    priority: str
    deadline: str
    status: str
    related_exposure: str
