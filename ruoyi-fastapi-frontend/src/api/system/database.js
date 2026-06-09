import request from '@/utils/request'

export function getDatabaseOverview() {
  return request({
    url: '/system/database/overview',
    method: 'get'
  })
}

export function getDatabaseUsers(params) {
  return request({
    url: '/system/database/users',
    method: 'get',
    params
  })
}

export function getTableColumns(tableName) {
  return request({
    url: `/system/database/tables/${encodeURIComponent(tableName)}/columns`,
    method: 'get'
  })
}

export function getTableRows(tableName, params) {
  return request({
    url: `/system/database/tables/${encodeURIComponent(tableName)}/rows`,
    method: 'get',
    params
  })
}
