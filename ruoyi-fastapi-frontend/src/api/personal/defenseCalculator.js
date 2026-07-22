import request from '@/utils/request'

export function listDefenseAttackPanels() {
  return request({
    url: '/personal/defense-calculator/attack-panels',
    method: 'get'
  })
}
