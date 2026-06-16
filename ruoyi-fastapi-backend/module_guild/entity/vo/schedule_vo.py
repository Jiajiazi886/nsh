from typing import Any, Optional

from pydantic import BaseModel, Field


class ScheduleTeamCreateModel(BaseModel):
    team_name: str = Field(description='团队名称')


class ScheduleSquadCreateModel(BaseModel):
    squad_name: Optional[str] = Field(default=None, description='小队名称')


class ScheduleAssignmentModel(BaseModel):
    member_id: int = Field(description='成员ID')
    team_id: int = Field(description='排表团队ID')
    squad_id: int = Field(description='排表小队ID')
    order_num: Optional[int] = Field(default=None, description='小队内位置序号')


class ScheduleSnapshotModel(BaseModel):
    schedule_name: str = Field(description='历史排表名称')


class ScheduleHistoryRenameModel(BaseModel):
    schedule_name: str = Field(description='历史排表名称')


class ScheduleWorkbookModel(BaseModel):
    workbook: dict[str, Any] = Field(default_factory=dict, description='Univer工作簿JSON')
