from pydantic import BaseModel


class StatOut(BaseModel):
    label: str
    value: str
    detail: str
    tone: str = "neutral"
    section: str | None = None


class ActivityOut(BaseModel):
    title: str
    subtitle: str
    meta: str


class DashboardOut(BaseModel):
    stats: list[StatOut]
    activity: list[ActivityOut]
    highlights: list[str]
