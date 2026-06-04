from typing import Optional
from pydantic import BaseModel, Field

class TeamCreateModel(BaseModel):
    team_name: str = Field(description='团队名称')
    team_type: Optional[str] = Field(default='', description='团队类型')