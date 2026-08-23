const scheduleService = require('../../services/schedule')

Page({
  data: {
    loading: true,
    schedule: null,
    accessMessage: '',
    memberCount: 0,
  },

  onLoad() {
    this.loadSchedule()
  },

  onPullDownRefresh() {
    this.loadSchedule().finally(() => wx.stopPullDownRefresh())
  },

  async loadSchedule() {
    this.setData({ loading: true, accessMessage: '' })
    try {
      const response = await scheduleService.getCurrentSchedule()
      const schedule = response.data || null
      const memberCount = (schedule && schedule.teams ? schedule.teams : []).reduce(
        (teamTotal, team) => teamTotal + (team.squads || []).reduce(
          (squadTotal, squad) => squadTotal + (squad.members || []).length,
          0,
        ),
        0,
      )
      this.setData({ schedule, memberCount })
    } catch (error) {
      this.setData({
        schedule: null,
        accessMessage: error.message || '当前账号暂无排表查看权限',
      })
    } finally {
      this.setData({ loading: false })
    }
  },
})
