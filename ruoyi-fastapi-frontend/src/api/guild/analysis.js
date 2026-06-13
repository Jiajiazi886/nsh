import request from '@/utils/request'

export function analyzeScheduleBattle(params) {
  return request({
    url: '/guild/analysis/schedule-battle',
    method: 'get',
    params
  })
}
