from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class InternalPowerImageDisplayStatusModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    enabled: bool = Field(default=True, description='是否显示内功图片')


class InternalPowerImageDisplaySaveModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    enabled: bool = Field(description='是否显示内功图片')
