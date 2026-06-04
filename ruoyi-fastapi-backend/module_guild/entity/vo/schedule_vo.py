from typing import Optional

from pydantic import BaseModel, Field


class ScheduleTeamCreateModel(BaseModel):
    team_name: str = Field(description='团队名称')


class ScheduleSquadCreateModel(BaseModel):
    squad_name: Optional[str] = Field(default=None, description='小队名称')


class ScheduleAssignmentModel(BaseModel):
    member_id: int = Field(description='成员ID')
    team_id: int = Field(description='排表团队ID')
    squad_id: int = Field(description='排表小队ID')


class ScheduleSnapshotModel(BaseModel):
    schedule_name: str = Field(description='历史排表名称')
