const { store } = require('./utils/store')
const { store: demoStore } = require('./utils/demo-store')

App({
  onLaunch() {
    store.load()
    demoStore.load()
  },
  globalData: {}
})
