import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.pvp_attack_panel_dao import PvpAttackPanelDao
from module_admin.entity.do.pvp_attack_panel_do import SystemPvpAttackPanel
from module_admin.entity.vo.pvp_attack_panel_vo import PvpAttackPanelModel, PvpAttackPanelQueryModel


class PvpAttackPanelService:
    """管理员进攻方面板与个人防守计算器共用的服务层。"""

    @classmethod
    async def get_list_services(
        cls, query_db: AsyncSession, query: PvpAttackPanelQueryModel
    ) -> PageModel:
        result = await PvpAttackPanelDao.get_list(query_db, query, is_page=True)
        return PageModel(
            rows=[cls._dict_to_model(row) for row in result.rows],
            pageNum=result.page_num,
            pageSize=result.page_size,
            total=result.total,
            hasNext=result.has_next,
        )

    @classmethod
    async def get_enabled_services(cls, query_db: AsyncSession) -> list[PvpAttackPanelModel]:
        return [cls._to_model(row) for row in await PvpAttackPanelDao.list_enabled(query_db)]

    @classmethod
    async def get_detail_services(cls, query_db: AsyncSession, panel_id: int) -> PvpAttackPanelModel:
        return cls._to_model(await cls._require_panel(query_db, panel_id))

    @classmethod
    async def add_services(
        cls, query_db: AsyncSession, payload: PvpAttackPanelModel, operator: str
    ) -> CrudResponseModel:
        now = datetime.now()
        panel = SystemPvpAttackPanel(
            panel_name=payload.panel_name,
            panel_json=cls._panel_json(payload),
            status=payload.status,
            remark=payload.remark or '',
            create_by=operator,
            create_time=now,
            update_by=operator,
            update_time=now,
        )
        await PvpAttackPanelDao.add(query_db, panel)
        panel_id = panel.panel_id
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='进攻方面板已新增', result={'panelId': panel_id})

    @classmethod
    async def edit_services(
        cls, query_db: AsyncSession, payload: PvpAttackPanelModel, operator: str
    ) -> CrudResponseModel:
        if payload.panel_id is None:
            raise ServiceException(message='面板ID不能为空')
        await cls._require_panel(query_db, payload.panel_id)
        await PvpAttackPanelDao.update(
            query_db,
            {
                'panel_id': payload.panel_id,
                'panel_name': payload.panel_name,
                'panel_json': cls._panel_json(payload),
                'status': payload.status,
                'remark': payload.remark or '',
                'update_by': operator,
                'update_time': datetime.now(),
            },
        )
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='进攻方面板已更新')

    @classmethod
    async def change_status_services(
        cls, query_db: AsyncSession, panel_id: int, status: str, operator: str
    ) -> CrudResponseModel:
        await cls._require_panel(query_db, panel_id)
        await PvpAttackPanelDao.change_status(query_db, panel_id, status, operator)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='状态已更新')

    @classmethod
    async def delete_services(cls, query_db: AsyncSession, panel_ids: str) -> CrudResponseModel:
        ids = [int(item) for item in panel_ids.split(',') if item.strip().isdigit()]
        if not ids:
            raise ServiceException(message='请选择需要删除的进攻方面板')
        for panel_id in ids:
            await cls._require_panel(query_db, panel_id)
        await PvpAttackPanelDao.delete_by_ids(query_db, ids)
        await query_db.commit()
        return CrudResponseModel(is_success=True, message='进攻方面板已删除')

    @classmethod
    async def _require_panel(cls, query_db: AsyncSession, panel_id: int) -> SystemPvpAttackPanel:
        panel = await PvpAttackPanelDao.get_by_id(query_db, panel_id)
        if panel is None:
            raise ServiceException(message='进攻方面板不存在')
        return panel

    @staticmethod
    def _panel_json(payload: PvpAttackPanelModel) -> str:
        return json.dumps(payload.model_dump(exclude={'panel_id', 'panel_name', 'status', 'remark', 'create_by', 'create_time', 'update_by', 'update_time'}), ensure_ascii=False)

    @classmethod
    def _to_model(cls, panel: SystemPvpAttackPanel) -> PvpAttackPanelModel:
        return PvpAttackPanelModel(
            panelId=panel.panel_id,
            panelName=panel.panel_name,
            status=panel.status or '0',
            remark=panel.remark or '',
            createBy=panel.create_by or '',
            createTime=panel.create_time,
            updateBy=panel.update_by or '',
            updateTime=panel.update_time,
            **cls._json_loads(panel.panel_json),
        )

    @classmethod
    def _dict_to_model(cls, row: dict[str, Any]) -> PvpAttackPanelModel:
        return PvpAttackPanelModel(
            panelId=row.get('panelId'),
            panelName=row.get('panelName') or '',
            status=row.get('status') or '0',
            remark=row.get('remark') or '',
            createBy=row.get('createBy') or '',
            createTime=row.get('createTime'),
            updateBy=row.get('updateBy') or '',
            updateTime=row.get('updateTime'),
            **cls._json_loads(row.get('panelJson')),
        )

    @staticmethod
    def _json_loads(value: str | None) -> dict[str, Any]:
        try:
            result = json.loads(value or '{}')
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return result if isinstance(result, dict) else {}
