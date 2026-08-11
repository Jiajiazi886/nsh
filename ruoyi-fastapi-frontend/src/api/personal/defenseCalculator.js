import request from '@/utils/request'

export function listDefenseAttackPanels() {
  return request({
    url: '/personal/defense-calculator/attack-panels',
    method: 'get'
  })
}

export function listPersonalDefenseAttackPanels() {
  return request({
    url: '/personal/defense-calculator/personal-attack-panels',
    method: 'get'
  })
}

export function addPersonalDefenseAttackPanel(data) {
  return request({
    url: '/personal/defense-calculator/personal-attack-panels',
    method: 'post',
    data
  })
}

export function updatePersonalDefenseAttackPanel(panelId, data) {
  return request({
    url: `/personal/defense-calculator/personal-attack-panels/${panelId}`,
    method: 'put',
    data
  })
}

export function deletePersonalDefenseAttackPanel(panelId) {
  return request({
    url: `/personal/defense-calculator/personal-attack-panels/${panelId}`,
    method: 'delete'
  })
}

export function getDefenseCalculatorSetting() {
  return request({
    url: '/personal/defense-calculator/setting',
    method: 'get',
    headers: { silentError: true }
  })
}

export function saveDefenseCalculatorSetting(data) {
  return request({
    url: '/personal/defense-calculator/setting',
    method: 'put',
    data,
    headers: { silentError: true }
  })
}

export function recognizeDefensePanelImage(file) {
  const data = new FormData()
  data.append('file', file)
  return request({
    url: '/personal/defense-calculator/recognize-panel-image',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function recognizeInternalPowerBenefitsImage(file) {
  const data = new FormData()
  data.append('file', file)
  return request({
    url: '/personal/defense-calculator/recognize-internal-power-benefits',
    method: 'post',
    data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
