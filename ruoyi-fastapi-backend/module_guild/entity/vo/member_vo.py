from typing import Optional
from pydantic import BaseModel, Field

class MemberEditModel(BaseModel):
    member_id: Optional[int] = Field(default=None, description='成员ID')
    player_class: Optional[str] = Field(default=None, description='主职业')
    secondary_class: Optional[str] = Field(default=None, description='副职')
    remark: Optional[str] = Field(default=None, description='备注')
    team_id: Optional[int] = Field(default=None, description='团队ID(None表示不清空，0表示清空)')
    squad_number: Optional[int] = Field(default=None, description='队编号')

class MemberProfileEditModel(BaseModel):
    player_class: Optional[str] = Field(default=None, description='主职业')
    secondary_class: Optional[str] = Field(default=None, description='副职')
    remark: Optional[str] = Field(default=None, description='备注')

class MemberCreateModel(BaseModel):
    player_name: str = Field(description='玩家角色名')
    player_class: Optional[str] = Field(default='', description='主职业')
    secondary_class: Optional[str] = Field(default='', description='副职')
    remark: Optional[str] = Field(default='', description='备注')

class MemberImportModel(BaseModel):
    battle_id: int = Field(description='战斗ID')
    guild_name: str = Field(description='要导入的帮会名称')

class MemberBatchDeleteModel(BaseModel):
    member_ids: list[int] = Field(description='要删除的成员ID列表')
