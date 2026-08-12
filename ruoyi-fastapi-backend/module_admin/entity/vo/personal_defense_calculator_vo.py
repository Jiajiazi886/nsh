from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from module_admin.entity.vo.pvp_attack_panel_vo import PvpAttackPanelFields


class DefenseCalculatorDefenderModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    defense: float = Field(default=2550, ge=0)
    resist: float = Field(default=0, ge=0)
    crit_resist: float = Field(default=0, ge=0)
    resist_pct: float = Field(default=0, ge=0)
    hp: float = Field(default=100000, ge=0)
    crit_defense: float = Field(default=0, ge=0)
    technique_resist: float = Field(default=0, ge=0)
    internal_reduction: float = Field(default=0, ge=0)
    gear_reduction: float = Field(default=0, ge=0)
    martial_reduction: float = Field(default=0, ge=0)
    other_reduction: float = Field(default=0, ge=0)


class PersonalPvpAttackPanelPayload(PvpAttackPanelFields):
    """用户可编辑的进攻方面板数值，名称和序号由服务端生成。"""


class PersonalPvpAttackPanelModel(PvpAttackPanelFields):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    panel_id: int | None = None
    sequence_no: int = 0
    panel_name: str = ''
    create_time: datetime | None = None
    update_time: datetime | None = None


class ProfessionBonusOverrideModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    defense_bonus_pct: float = Field(default=0, ge=0, le=1000)
    hp_bonus_pct: float = Field(default=0, ge=0, le=1000)


class DefenseCalculatorSettingModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    defender: DefenseCalculatorDefenderModel = Field(default_factory=DefenseCalculatorDefenderModel)
    selected_panel_source: Literal['system', 'personal'] = 'system'
    selected_panel_id: int = Field(default=0, ge=0)
    profession_id: int = Field(default=0, ge=0)
    profession_name: str = ''
    profession_overrides: dict[str, ProfessionBonusOverrideModel] = Field(default_factory=dict)
    selected_internal_power_ids: list[int] = Field(default_factory=list, max_length=6)
    recommendation_inputs: dict[str, float] = Field(default_factory=dict)
    update_time: datetime | None = None
