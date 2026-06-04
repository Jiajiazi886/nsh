from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, String

from config.database import Base


class GuildBattle(Base):
    __tablename__ = 'guild_battle'
    __table_args__ = {'comment': '约战主表'}

    battle_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='约战ID')
    battle_name = Column(String(100), nullable=True, server_default="''", comment='约战名称')
    battle_date = Column(String(10), nullable=True, server_default="''", comment='约战日期')
    initiator_guild_id = Column(BigInteger, nullable=False, server_default='0', comment='发起方帮会ID')
    opponent_guild_id = Column(BigInteger, nullable=True, server_default='0', comment='对手帮会ID')
    opponent_name = Column(String(50), nullable=True, server_default="''", comment='对手帮会名称')
    battle_time = Column(DateTime, nullable=True, comment='约战时间')
    battle_type = Column(String(20), nullable=True, server_default="''", comment='约战类型')
    battle_result = Column(String(10), nullable=True, server_default="''", comment='约战结果')
    status = Column(CHAR(1), nullable=True, server_default='0', comment='状态（0待开始 1进行中 2已完成）')
    csv_file_url = Column(String(255), nullable=True, server_default="''", comment='CSV文件URL')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注')
    del_flag = Column(CHAR(1), nullable=False, server_default='0', comment='删除标志(0正常 1删除)')
    user_id = Column(BigInteger, nullable=False, server_default='0', comment='导入人用户ID')
    my_guild_name = Column(String(64), nullable=True, server_default="''", comment='自己帮会名称')


class GuildBattleRecord(Base):
    __tablename__ = 'guild_battle_record'
    __table_args__ = {'comment': '约战明细表'}

    record_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='记录ID')
    battle_id = Column(BigInteger, nullable=False, server_default='0', comment='约战ID')
    guild_id = Column(BigInteger, nullable=False, server_default='0', comment='帮会ID')
    battle_date = Column(String(10), nullable=True, server_default="''", comment='约战日期')
    guild_name = Column(String(50), nullable=True, server_default="''", comment='帮会名称')
    player_name = Column(String(30), nullable=False, server_default="''", comment='玩家名称')
    player_class = Column(String(20), nullable=True, server_default="''", comment='玩家职业')
    kills = Column(Integer, nullable=True, server_default='0', comment='击杀数')
    qingquan_kills = Column(Integer, nullable=True, server_default='0', comment='清泉击杀')
    assists = Column(Integer, nullable=True, server_default='0', comment='助攻数')
    resources = Column(Integer, nullable=True, server_default='0', comment='资源分')
    dmg_to_players = Column(BigInteger, nullable=True, server_default='0', comment='对玩家伤害')
    armor_break_players = Column(BigInteger, nullable=True, server_default='0', comment='破甲玩家')
    dmg_to_buildings = Column(BigInteger, nullable=True, server_default='0', comment='对建筑伤害')
    armor_break_buildings = Column(BigInteger, nullable=True, server_default='0', comment='破甲建筑')
    healing = Column(BigInteger, nullable=True, server_default='0', comment='治疗量')
    dmg_taken = Column(BigInteger, nullable=True, server_default='0', comment='承受伤害')
    deaths = Column(Integer, nullable=True, server_default='0', comment='死亡数')
    revives = Column(Integer, nullable=True, server_default='0', comment='复活数')
    burn_bones = Column(Integer, nullable=True, server_default='0', comment='焚骨数')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    del_flag = Column(CHAR(1), nullable=False, server_default='0', comment='删除标志(0正常 1删除)')