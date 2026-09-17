from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from module_guild.entity.vo.battle_vo import BattleRecordItem


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', alias_generator=to_camel, populate_by_name=True)


class CreateOrganization(Input):
    org_type: Literal['guild', 'club']
    name: str = Field(min_length=1, max_length=80)


class GrantMember(Input):
    member_id: str = Field(pattern=r'^[1-9][0-9]{0,18}$')
    role: Literal['member', 'assistant'] = 'member'


class CreateActivity(Input):
    org_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=100)
    starts_at: datetime
    ends_at: datetime
    remark: str = Field(default='', max_length=500)

    @model_validator(mode='after')
    def times(self):
        # UI/API uses explicit local wall-clock ISO time, matching existing battle DateTime.
        if self.starts_at.tzinfo or self.ends_at.tzinfo or self.ends_at <= self.starts_at or not self.name.strip():
            raise ValueError('Invalid activity time/name')
        return self


class ChangeActivity(Input):
    expected_revision: int = Field(ge=0, strict=True)
    operation_key: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')


class PlayerInput(Input):
    member_id: str | None = Field(default=None, pattern=r'^[1-9][0-9]{0,18}$')
    temporary_id: str | None = Field(default=None, pattern=r'^temp_[A-Za-z0-9_-]+$', max_length=64)
    name: str = Field(default='', max_length=30)
    profession: str = Field(default='', max_length=30)

    @model_validator(mode='after')
    def identity(self):
        if bool(self.member_id) == bool(self.temporary_id):
            raise ValueError('Choose one identity')
        return self


class SeatInput(Input):
    position: int = Field(ge=1, le=6, strict=True)
    required_profession: str = Field(default='', max_length=30)
    notes: list[str] = Field(default_factory=list, max_length=20)
    player: PlayerInput | None = None

    @model_validator(mode='after')
    def clean_notes(self):
        cleaned = []
        for note in self.notes:
            value = note.strip()
            if not value or len(value) > 20:
                raise ValueError('Invalid seat note')
            if value not in cleaned:
                cleaned.append(value)
        self.notes = cleaned
        return self


class SquadInput(Input):
    id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1, max_length=30)
    seats: list[SeatInput] = Field(min_length=6, max_length=6)

    @model_validator(mode='after')
    def positions(self):
        if sorted(s.position for s in self.seats) != list(range(1, 7)) or not self.name.strip():
            raise ValueError('Six unique seats required')
        return self


class TeamInput(Input):
    id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')
    name: str = Field(min_length=1, max_length=30)
    squads: list[SquadInput] = Field(default_factory=list, max_length=100)


class SaveLineup(ChangeActivity):
    teams: list[TeamInput] = Field(min_length=1, max_length=100)


class SignupSeat(ChangeActivity):
    member_id: str = Field(pattern=r'^[1-9][0-9]{0,18}$')
    squad_id: str = Field(min_length=1, max_length=100)
    position: int = Field(ge=1, le=6, strict=True)


class LeaveSeat(ChangeActivity):
    member_id: str = Field(pattern=r'^[1-9][0-9]{0,18}$')


class ActivityLeaveRequest(Input):
    member_id: str = Field(pattern=r'^[1-9][0-9]{0,18}$')
    remark: str = Field(default='', max_length=500)


class LinkReport(ChangeActivity):
    battle_id: str = Field(pattern=r'^[1-9][0-9]{0,18}$')


class ImportActivityReport(ChangeActivity):
    file_name: str = Field(min_length=5, max_length=100, pattern=r'^.+\.[cC][sS][vV]$')
    battle_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    battle_result: str = Field(default='', max_length=10)
    my_guild_name: str = Field(default='', max_length=64)
    opponent_name: str = Field(default='', max_length=50)
    remark: str = Field(default='', max_length=500)
    records: list[BattleRecordItem] = Field(min_length=1, max_length=1000)
