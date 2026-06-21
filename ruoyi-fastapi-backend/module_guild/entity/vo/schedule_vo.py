from typing import Any, Optional

from pydantic import BaseModel, Field


class ScheduleTeamCreateModel(BaseModel):
    team_name: str = Field(description='团队名称')


class ScheduleSquadCreateModel(BaseModel):
    squad_name: Optional[str] = Field(default=None, description='小队名称')


class ScheduleRegionRangeModel(BaseModel):
    start_row: int = Field(ge=0, description='选区起始行')
    end_row: int = Field(ge=0, description='选区结束行')
    start_column: int = Field(ge=0, description='选区起始列')
    end_column: int = Field(ge=0, description='选区结束列')


class ScheduleRegionSquadCreateModel(BaseModel):
    squad_name: str = Field(description='小队名称')
    max_members: int = Field(ge=1, le=2000, description='小队人数上限')
    range: ScheduleRegionRangeModel = Field(description='小队对应表格区域')


class ScheduleRegionSquadUpdateModel(BaseModel):
    squad_name: str = Field(description='小队名称')
    max_members: int = Field(ge=1, le=2000, description='小队人数上限')


class ScheduleRegionAssignmentItemModel(BaseModel):
    member_id: int = Field(description='成员ID')
    order_num: int = Field(ge=1, description='小队内位置序号')


class ScheduleRegionAssignmentsModel(BaseModel):
    members: list[ScheduleRegionAssignmentItemModel] = Field(default_factory=list, description='小队成员列表')


class ScheduleRegionTeamCreateModel(BaseModel):
    team_name: str = Field(description='团队名称')
    squad_ids: list[int] = Field(default_factory=list, description='小队ID列表')


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
