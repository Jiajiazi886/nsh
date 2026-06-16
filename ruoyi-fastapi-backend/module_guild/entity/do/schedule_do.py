from datetime import datetime

from sqlalchemy import BigInteger, CHAR, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT

from config.database import Base


class GuildSchedule(Base):
    __tablename__ = 'guild_schedule'
    __table_args__ = {'comment': '约战排表主表'}

    schedule_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='排表ID')
    schedule_name = Column(String(100), nullable=False, server_default="''", comment='排表名称')
    user_id = Column(BigInteger, nullable=False, server_default='0', comment='所属用户ID')
    is_active = Column(CHAR(1), nullable=False, server_default='0', comment='是否当前排表(0否 1是)')
    source_schedule_id = Column(BigInteger, nullable=True, comment='来源排表ID')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    del_flag = Column(CHAR(1), nullable=False, server_default='0', comment='删除标志(0正常 1删除)')


class GuildScheduleTeam(Base):
    __tablename__ = 'guild_schedule_team'
    __table_args__ = {'comment': '约战排表团队表'}

    team_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='排表团队ID')
    schedule_id = Column(BigInteger, nullable=False, server_default='0', comment='排表ID')
    team_name = Column(String(50), nullable=False, server_default="''", comment='团队名称')
    order_num = Column(Integer, nullable=False, server_default='0', comment='显示顺序')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')


class GuildScheduleSquad(Base):
    __tablename__ = 'guild_schedule_squad'
    __table_args__ = {'comment': '约战排表小队表'}

    squad_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='排表小队ID')
    team_id = Column(BigInteger, nullable=False, server_default='0', comment='排表团队ID')
    squad_name = Column(String(50), nullable=False, server_default="''", comment='小队名称')
    max_members = Column(Integer, nullable=False, server_default='6', comment='小队人数上限')
    order_num = Column(Integer, nullable=False, server_default='0', comment='显示顺序')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')


class GuildScheduleAssignment(Base):
    __tablename__ = 'guild_schedule_assignment'
    __table_args__ = {'comment': '约战排表成员分配表'}

    assignment_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='分配ID')
    schedule_id = Column(BigInteger, nullable=False, server_default='0', comment='排表ID')
    team_id = Column(BigInteger, nullable=False, server_default='0', comment='排表团队ID')
    squad_id = Column(BigInteger, nullable=False, server_default='0', comment='排表小队ID')
    member_id = Column(BigInteger, nullable=False, server_default='0', comment='成员ID')
    player_name = Column(String(30), nullable=False, server_default="''", comment='玩家角色名快照')
    player_class = Column(String(20), nullable=True, server_default="''", comment='主职业快照')
    secondary_class = Column(String(20), nullable=True, server_default="''", comment='副职快照')
    order_num = Column(Integer, nullable=False, server_default='0', comment='显示顺序')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')


class GuildScheduleWorkbook(Base):
    __tablename__ = 'guild_schedule_workbook'
    __table_args__ = {'comment': '约战排表自由表格数据表'}

    workbook_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='自由表格ID')
    schedule_id = Column(BigInteger, nullable=False, server_default='0', unique=True, comment='排表ID')
    workbook_json = Column(Text().with_variant(LONGTEXT, 'mysql'), nullable=False, comment='Univer工作簿JSON')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')
