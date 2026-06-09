from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DatabaseTableModel(BaseModel):
    """
    Database table summary for the read-only admin database browser.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    table_name: str = Field(description='Table name')
    table_comment: str | None = Field(default='', description='Table comment')
    row_count: int | None = Field(default=0, description='Approximate row count')
    data_length: int | None = Field(default=0, description='Data size in bytes')
    index_length: int | None = Field(default=0, description='Index size in bytes')
    create_time: datetime | None = Field(default=None, description='Create time')
    update_time: datetime | None = Field(default=None, description='Update time')


class DatabaseOverviewModel(BaseModel):
    """
    Database overview.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    database_name: str = Field(description='Current database name')
    database_type: str = Field(description='Database type')
    total_tables: int = Field(description='Total table count')
    tables: list[DatabaseTableModel] = Field(default_factory=list, description='Tables')


class DatabaseColumnModel(BaseModel):
    """
    Database column detail.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    column_name: str = Field(description='Column name')
    data_type: str | None = Field(default='', description='Data type')
    column_type: str | None = Field(default='', description='Full column type')
    is_nullable: str | None = Field(default='', description='Whether nullable')
    column_key: str | None = Field(default='', description='Column key')
    column_default: Any | None = Field(default=None, description='Default value')
    column_comment: str | None = Field(default='', description='Column comment')
    ordinal_position: int | None = Field(default=0, description='Column order')


class DatabaseRowsModel(BaseModel):
    """
    Paginated table rows.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    table_name: str = Field(description='Table name')
    columns: list[str] = Field(default_factory=list, description='Column names')
    rows: list[dict[str, Any]] = Field(default_factory=list, description='Rows')
    page_num: int = Field(description='Current page')
    page_size: int = Field(description='Page size')
    total: int = Field(description='Total rows')


class DatabaseUserRowModel(BaseModel):
    """
    Admin-visible user summary without data-scope filtering.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    user_id: int | None = Field(default=None, description='User ID')
    user_name: str | None = Field(default='', description='Account')
    nick_name: str | None = Field(default='', description='Nickname')
    user_type: str | None = Field(default='', description='User type')
    email: str | None = Field(default='', description='Email')
    status: str | None = Field(default='', description='Status')
    del_flag: str | None = Field(default='', description='Delete flag')
    login_ip: str | None = Field(default='', description='Last login IP')
    login_date: datetime | None = Field(default=None, description='Last login date')
    create_time: datetime | None = Field(default=None, description='Create time')
    role_names: str | None = Field(default='', description='Role names')
    role_keys: str | None = Field(default='', description='Role keys')
    remark: str | None = Field(default='', description='Remark')


class DatabaseUsersModel(BaseModel):
    """
    Paginated all-user summary.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    rows: list[DatabaseUserRowModel] = Field(default_factory=list, description='User rows')
    page_num: int = Field(description='Current page')
    page_size: int = Field(description='Page size')
    total: int = Field(description='Total users')
