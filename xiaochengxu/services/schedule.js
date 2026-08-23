const { request } = require('../utils/request')

function getCurrentSchedule() {
  return request({ url: '/guild/schedule/current' })
}

module.exports = {
  getCurrentSchedule,
}
