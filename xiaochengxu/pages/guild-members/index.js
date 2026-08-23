const guildService = require('../../services/guild')

Page({
  data: {
    loading: true,
    guild: null,
    members: [],
    visibleMembers: [],
    keyword: '',
    errorMessage: '',
  },

  onLoad() {
    this.loadMembers()
  },

  onPullDownRefresh() {
    this.loadMembers().finally(() => wx.stopPullDownRefresh())
  },

  async loadMembers() {
    this.setData({ loading: true, errorMessage: '' })
    try {
      const [guildResponse, memberResponse] = await Promise.all([
        guildService.getGuildInfo(),
        guildService.getMembers(),
      ])
      const members = memberResponse.data || []
      this.setData({
        guild: guildResponse.data || null,
        members,
        visibleMembers: this.filterMembers(members, this.data.keyword),
      })
    } catch (error) {
      this.setData({
        guild: null,
        members: [],
        visibleMembers: [],
        errorMessage: error.message || '成员名册加载失败',
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  onKeywordInput(event) {
    const keyword = event.detail.value || ''
    this.setData({
      keyword,
      visibleMembers: this.filterMembers(this.data.members, keyword),
    })
  },

  filterMembers(members, keyword) {
    const normalized = (keyword || '').trim().toLowerCase()
    if (!normalized) return members
    return members.filter((member) => [
      member.player_name,
      member.player_class,
      member.secondary_class,
      member.remark,
    ].some((value) => String(value || '').toLowerCase().includes(normalized)))
  },
})
