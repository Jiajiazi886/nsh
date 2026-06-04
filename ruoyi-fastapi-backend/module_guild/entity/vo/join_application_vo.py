from pydantic import BaseModel, Field


class GuildSearchModel(BaseModel):
    keyword: str = Field(description='帮会名称关键词')


class JoinApplicationCreateModel(BaseModel):
    guild_id: int = Field(description='目标帮会ID')
    player_name: str = Field(description='玩家角色名')
    player_class: str | None = Field(default='', description='主职业')
    secondary_class: str | None = Field(default='', description='副职')
    remark: str | None = Field(default='', description='备注')


class JoinApplicationReviewModel(BaseModel):
    application_id: int = Field(description='申请ID')
