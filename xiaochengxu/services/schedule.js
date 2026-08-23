const { request } = require('../utils/request')

function getCurrentSchedule() {
  return request({ url: '/guild/schedule/current' })
}

function getScheduleHistory() {
  return request({ url: '/guild/schedule/history' })
}

module.exports = {
  getCurrentSchedule,
  getScheduleHistory,
}
