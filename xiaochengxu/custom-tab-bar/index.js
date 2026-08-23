const TABS = [
  { pagePath: '/pages/home/index', text: '首页', icon: '首' },
  { pagePath: '/pages/activities/index', text: '活动', icon: '活' },
  { pagePath: '/pages/guild/index', text: '帮会', icon: '会' },
  { pagePath: '/pages/records/index', text: '战绩', icon: '绩' },
  { pagePath: '/pages/profile/index', text: '我的', icon: '我' },
]

Component({
  data: {
    selected: 0,
    tabs: TABS,
  },

  methods: {
    switchTab(event) {
      const index = Number(event.currentTarget.dataset.index)
      const tab = this.data.tabs[index]
      if (!tab || index === this.data.selected) return
      wx.switchTab({ url: tab.pagePath })
    },
  },
})
