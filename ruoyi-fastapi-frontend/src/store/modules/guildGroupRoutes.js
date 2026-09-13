// Only extend a group menu already returned by the authenticated backend.
export function withTeamManagementRoute(routes) {
  return (routes || []).map(source => {
    const route = { ...source }
    if (source.children) route.children = withTeamManagementRoute(source.children)
    const children = route.children || []
    const schedule = children.find(child => child.component === 'guild/schedule/index' && !child.hidden)
    const isGroup = source.component === 'ParentView' &&
      (source.meta?.title === '分团管理' || source.path === 'group')
    if (isGroup && !source.hidden && schedule && !children.some(child =>
      child.component === 'guild/teamManagement/index' || child.path === 'team-management')) {
      route.children = [{
        path: 'team-management', name: 'GuildTeamManagementPlaceholder',
        component: 'guild/teamManagement/index',
        meta: { title: '团队管理', icon: 'peoples', noCache: true }
      }, ...children]
    }
    return route
  })
}
