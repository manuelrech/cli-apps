from datetime import date

from pydantic import BaseModel


class Project(BaseModel):
    id: str
    name: str


class TimeEntry(BaseModel):
    description: str
    project_id: str
    project_name: str


class TaskSummary(BaseModel):
    description: str
    project_name: str
    hours: float
    entries: int


class LogRequest(BaseModel):
    target_date: date
    description: str
    project_id: str
