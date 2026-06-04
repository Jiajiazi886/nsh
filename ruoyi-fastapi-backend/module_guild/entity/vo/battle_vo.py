from typing import Optional

from pydantic import BaseModel, Field


class BattleRecordItem(BaseModel):
    guild_name: Optional[str] = Field(default=None)
    player_name: str
    player_class: Optional[str] = Field(default=None)
    kills: Optional[int] = Field(default=0)
    qingquan_kills: Optional[int] = Field(default=0)
    assists: Optional[int] = Field(default=0)
    resources: Optional[int] = Field(default=0)
    dmg_to_players: Optional[int] = Field(default=0)
    armor_break_players: Optional[int] = Field(default=0)
    dmg_to_buildings: Optional[int] = Field(default=0)
    armor_break_buildings: Optional[int] = Field(default=0)
    healing: Optional[int] = Field(default=0)
    dmg_taken: Optional[int] = Field(default=0)
    deaths: Optional[int] = Field(default=0)
    revives: Optional[int] = Field(default=0)
    burn_bones: Optional[int] = Field(default=0)


class BattleImportModel(BaseModel):
    battle_date: str = Field(description='约战日期')
    battle_type: Optional[str] = Field(default='友谊赛', description='约战类型')
    battle_result: Optional[str] = Field(default=None, description='约战结果: 胜利/失败')
    my_guild_name: Optional[str] = Field(default=None, description='我方帮会名称')
    opponent_name: Optional[str] = Field(default=None, description='对手帮会名称')
    csv_filename: Optional[str] = Field(default=None, description='上传的CSV文件名')
    remark: Optional[str] = Field(default=None, description='备注')
    records: list[BattleRecordItem] = Field(default=[], description='玩家明细数据')