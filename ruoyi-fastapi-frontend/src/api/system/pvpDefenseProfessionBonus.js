import request from '@/utils/request'

export function listPvpDefenseProfessionBonuses() {
  return request({ url: '/system/pvp-defense-profession-bonus/list', method: 'get' })
}

export function updatePvpDefenseProfessionBonus(professionId, data) {
  return request({
    url: `/system/pvp-defense-profession-bonus/${professionId}`,
    method: 'put',
    data
  })
}
