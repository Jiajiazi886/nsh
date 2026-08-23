function selectTab(page, index) {
  if (!page || typeof page.getTabBar !== 'function') return
  const tabBar = page.getTabBar()
  if (tabBar) tabBar.setData({ selected: index })
}

function switchMainTab(event) {
  const url = event.currentTarget.dataset.url
  if (url) wx.switchTab({ url })
}

module.exports = {
  selectTab,
  switchMainTab,
}
