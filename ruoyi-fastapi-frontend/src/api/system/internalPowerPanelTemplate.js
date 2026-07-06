import request from '@/utils/request'

export function listInternalPowerPanelTemplate(query) {
  return request({
    url: '/system/internal-power-panel-template/list',
    method: 'get',
    params: query
  })
}

export function getInternalPowerPanelTemplate(templateId) {
  return request({
    url: `/system/internal-power-panel-template/${templateId}`,
    method: 'get'
  })
}

export function addInternalPowerPanelTemplate(data) {
  return request({
    url: '/system/internal-power-panel-template',
    method: 'post',
    data
  })
}

export function updateInternalPowerPanelTemplate(data) {
  return request({
    url: '/system/internal-power-panel-template',
    method: 'put',
    data
  })
}

export function delInternalPowerPanelTemplate(templateIds) {
  return request({
    url: `/system/internal-power-panel-template/${templateIds}`,
    method: 'delete'
  })
}

export function changeInternalPowerPanelTemplateStatus(templateId, status) {
  return request({
    url: `/system/internal-power-panel-template/${templateId}/status`,
    method: 'post',
    data: {
      templateId,
      status
    }
  })
}
