from dataclasses import dataclass, field
from typing import List, Optional

@dataclass(frozen=True)
class VaccineSummary:
    id: str
    name: str
    disease: str
    life_stages: List[str]
    short_summary: str
    status: str = "draft"
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    reviewed_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
