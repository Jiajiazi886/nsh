from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ProfessionBonusUpdateModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    defense_bonus_pct: float = Field(default=0, ge=0, le=1000)
    hp_bonus_pct: float = Field(default=0, ge=0, le=1000)


class ProfessionBonusModel(ProfessionBonusUpdateModel):
    profession_id: int
    profession_name: str
    order_num: int = 0
    update_by: str = ''
    update_time: datetime | None = None
