import request from '@/utils/request'

export function getCurrentSchedule() {
  return request({
    url: '/guild/schedule/current',
    method: 'get'
  })
}

export function getScheduleHistory() {
  return request({
    url: '/guild/schedule/history',
    method: 'get'
  })
}

export function getScheduleDetail(scheduleId) {
  return request({
    url: `/guild/schedule/${scheduleId}`,
    method: 'get'
  })
}

export function addScheduleTeam(data, options = {}) {
  return request({
    url: '/guild/schedule/team',
    method: 'post',
    headers: { repeatSubmit: options.repeatSubmit ?? true },
    data
  })
}

export function deleteScheduleTeam(teamId) {
  return request({
    url: `/guild/schedule/team/${teamId}`,
    method: 'delete'
  })
}

export function addScheduleSquad(teamId, data, options = {}) {
  return request({
    url: `/guild/schedule/team/${teamId}/squad`,
    method: 'post',
    headers: { repeatSubmit: options.repeatSubmit ?? true },
    data
  })
}

export function deleteScheduleSquad(teamId, squadId) {
  return request({
    url: `/guild/schedule/team/${teamId}/squad/${squadId}`,
    method: 'delete'
  })
}

export function createRegionSquad(data) {
  return request({
    url: '/guild/schedule/region/squad',
    method: 'post',
    data
  })
}

export function syncRegionSquadAssignments(squadId, data, options = {}) {
  return request({
    url: `/guild/schedule/region/squad/${squadId}/assignments`,
    method: 'put',
    headers: { repeatSubmit: options.repeatSubmit ?? true },
    data
  })
}

export function updateRegionSquad(squadId, data, options = {}) {
  return request({
    url: `/guild/schedule/region/squad/${squadId}`,
    method: 'put',
    headers: { repeatSubmit: options.repeatSubmit ?? true },
    data
  })
}

export function createRegionTeam(data) {
  return request({
    url: '/guild/schedule/region/team',
    method: 'post',
    data
  })
}

export function saveScheduleAssignment(data) {
  return request({
    url: '/guild/schedule/assignment',
    method: 'put',
    data
  })
}

export function clearScheduleAssignment(memberId) {
  return request({
    url: `/guild/schedule/assignment/${memberId}`,
    method: 'delete'
  })
}

export function saveScheduleSnapshot(data) {
  return request({
    url: '/guild/schedule/snapshot',
    method: 'post',
    data
  })
}

export function applyScheduleHistory(scheduleId) {
  return request({
    url: `/guild/schedule/history/${scheduleId}/apply`,
    method: 'post'
  })
}

export function renameScheduleHistory(scheduleId, data) {
  return request({
    url: `/guild/schedule/history/${scheduleId}/name`,
    method: 'put',
    data
  })
}

export function deleteScheduleHistory(scheduleId) {
  return request({
    url: `/guild/schedule/history/${scheduleId}`,
    method: 'delete'
  })
}

export function getCurrentScheduleWorkbook() {
  return request({
    url: '/guild/schedule/current/workbook',
    method: 'get'
  })
}

export function getScheduleWorkbook(scheduleId) {
  return request({
    url: `/guild/schedule/${scheduleId}/workbook`,
    method: 'get'
  })
}

export function saveCurrentScheduleWorkbook(workbook, options = {}) {
  return request({
    url: '/guild/schedule/current/workbook',
    method: 'put',
    headers: { repeatSubmit: options.repeatSubmit ?? true },
    data: { workbook }
  })
}

export function importCurrentScheduleWorkbook(workbook) {
  return request({
    url: '/guild/schedule/current/workbook/import',
    method: 'put',
    data: { workbook }
  })
}
