from datetime import datetime

from pydantic import BaseModel


class DashboardMetric(BaseModel):
    key: str
    label: str
    value: int
    detail: str


class DashboardTrendPoint(BaseModel):
    label: str
    analyses: int
    actas: int


class DashboardDistributionItem(BaseModel):
    label: str
    value: int


class DashboardTaskStatus(BaseModel):
    pending: int
    completed: int


class DashboardActivityItem(BaseModel):
    title: str
    type: str
    reference: str
    created_at: datetime


class DashboardAuditItem(BaseModel):
    title: str
    detail: str
    status: str
    created_at: datetime


class DashboardRead(BaseModel):
    metrics: list[DashboardMetric]
    trend: list[DashboardTrendPoint]
    distribution: list[DashboardDistributionItem]
    tasks: DashboardTaskStatus
    activity: list[DashboardActivityItem]
    audits: list[DashboardAuditItem]
