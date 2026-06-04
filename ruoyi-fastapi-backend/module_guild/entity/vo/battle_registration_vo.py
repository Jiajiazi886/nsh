from typing import Optional

from pydantic import BaseModel, Field


class BattleInviteCreateModel(BaseModel):
    battle_name: str = Field(description='约战名称')
    battle_time: Optional[str] = Field(default=None, description='约战时间')
    expire_hours: int = Field(default=24, ge=1, le=720, description='链接有效小时数')
    remark: Optional[str] = Field(default='', description='备注')


class BattleRegistrationReviewModel(BaseModel):
    registration_id: int = Field(description='报名ID')
    approval_comment: Optional[str] = Field(default='', description='审核备注')


class PublicBattleRegistrationModel(BaseModel):
    member_id: int = Field(description='帮会成员ID')
    player_class: Optional[str] = Field(default='', description='本次约战主职业')
    secondary_class: Optional[str] = Field(default='', description='本次约战副职')
    applicant_name: Optional[str] = Field(default='', description='报名人称呼')
    applicant_contact: Optional[str] = Field(default='', description='联系方式')
    remark: Optional[str] = Field(default='', description='备注')


class PublicBattleJoinApplicationModel(BaseModel):
    player_name: str = Field(description='玩家角色名')
    player_class: Optional[str] = Field(default='', description='主职业')
    secondary_class: Optional[str] = Field(default='', description='副职')
    applicant_name: Optional[str] = Field(default='', description='申请人称呼')
    applicant_contact: Optional[str] = Field(default='', description='联系方式')
    remark: Optional[str] = Field(default='', description='备注')
