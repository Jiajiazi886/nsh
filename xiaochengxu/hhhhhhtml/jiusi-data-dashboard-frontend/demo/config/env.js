const ENVIRONMENTS = {
  development: {
    name: '本地开发',
    baseUrl: 'http://127.0.0.1:9101',
  },
  production: {
    name: '正式环境',
    baseUrl: 'https://www.xn--kbrr2vyxjytebq4azkrrie.icu/docker-api',
  },
}

function resolveEnvironment() {
  try {
    const accountInfo = wx.getAccountInfoSync()
    if (['trial', 'release'].includes(accountInfo.miniProgram.envVersion)) {
      return ENVIRONMENTS.production
    }
  } catch (error) {
    console.warn('无法读取小程序环境，使用本地开发接口', error)
  }
  return ENVIRONMENTS.development
}

module.exports = {
  getEnvironment: resolveEnvironment,
}
