const { createClient, createWxTransport } = require('../utils/nsh-api-sdk')
const { getEnvironment } = require('../config/env')
const { getToken, invalidateSession } = require('../utils/storage')
let client, root
function getClient() {
  const baseUrl = getEnvironment().baseUrl
  if (!client || root !== baseUrl) {
    root = baseUrl
    const send = createWxTransport(wx)
    client = createClient({ baseUrl, getToken, transport: async request => {
      const response = await send(request)
      const authorization = request.headers.Authorization
      // Anonymous login failures must not trigger a login redirect.
      if (response.status === 401 && authorization) {
        invalidateSession(authorization.slice(7))
      } else if (response.status === 401 && !/\/auth\/(login|captcha|config)$/.test(request.url)) {
        invalidateSession('')
      }
      return response
    } })
  }
  return client
}
module.exports = { getClient }
