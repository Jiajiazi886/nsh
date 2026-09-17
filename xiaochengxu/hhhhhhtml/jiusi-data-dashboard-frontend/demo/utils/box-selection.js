function uniqueIds(ids) {
  const seen = new Set()
  return (Array.isArray(ids) ? ids : []).map(String).filter(function (id) {
    if (!id || seen.has(id)) return false
    seen.add(id)
    return true
  })
}

function derivePlayerOverrides(baseIds, checkedIds) {
  const base = uniqueIds(baseIds)
  const checked = uniqueIds(checkedIds)
  const baseSet = new Set(base)
  const checkedSet = new Set(checked)

  return {
    manualAddIds: checked.filter(function (id) { return !baseSet.has(id) }),
    manualRemoveIds: base.filter(function (id) { return !checkedSet.has(id) })
  }
}

function buildRoleTree(players, keyword, expandedByRole) {
  const source = Array.isArray(players) ? players : []
  const query = String(keyword || '').trim().toLowerCase()
  const groups = []

  source.forEach(function (player) {
    const role = String(player && player.role || '').trim() || '未分类职业'
    let group = groups.find(function (item) { return item.role === role })
    if (!group) {
      group = { role: role, players: [] }
      groups.push(group)
    }
    group.players.push(player)
  })

  return groups.map(function (group) {
    const roleMatches = !query || group.role.toLowerCase().includes(query)
    const visiblePlayers = roleMatches
      ? group.players.slice()
      : group.players.filter(function (player) {
        return String(player && player.name || '').toLowerCase().includes(query)
      })

    if (!visiblePlayers.length) return null

    const hasSavedState = expandedByRole && Object.prototype.hasOwnProperty.call(expandedByRole, group.role)
    return {
      role: group.role,
      count: group.players.length,
      checkedCount: group.players.filter(function (player) { return !!player.checked }).length,
      expanded: hasSavedState ? expandedByRole[group.role] !== false : true,
      players: visiblePlayers
    }
  }).filter(Boolean)
}

module.exports = {
  derivePlayerOverrides,
  buildRoleTree
}
