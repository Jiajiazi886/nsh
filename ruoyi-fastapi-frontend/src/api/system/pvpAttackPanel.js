import request from '@/utils/request'

export function listPvpAttackPanels(params) {
  return request({ url: '/system/pvp-attack-panel/list', method: 'get', params })
}

export function getPvpAttackPanel(panelId) {
  return request({ url: `/system/pvp-attack-panel/${panelId}`, method: 'get' })
}

export function addPvpAttackPanel(data) {
  return request({ url: '/system/pvp-attack-panel', method: 'post', data })
}

export function updatePvpAttackPanel(data) {
  return request({ url: '/system/pvp-attack-panel', method: 'put', data })
}

export function changePvpAttackPanelStatus(panelId, data) {
  return request({ url: `/system/pvp-attack-panel/${panelId}/status`, method: 'post', data })
}

export function deletePvpAttackPanel(panelIds) {
  return request({ url: `/system/pvp-attack-panel/${panelIds}`, method: 'delete' })
}
