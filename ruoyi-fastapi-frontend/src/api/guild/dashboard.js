import request from '@/utils/request'

export function getGuildDashboardSummary() {
  return request({
    url: '/guild/dashboard/summary',
    method: 'get'
  })
}
