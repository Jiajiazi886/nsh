import auth from '@/plugins/auth'
import router, { constantRoutes, dynamicRoutes } from '@/router'
import { getRouters } from '@/api/menu'
import Layout from '@/layout/index'
import ParentView from '@/components/ParentView'
import InnerLink from '@/layout/components/InnerLink'
import GuildMember from '@/views/guild/member/index.vue'
import SystemAiKey from '@/views/system/aiKey/index.vue'
import SystemPvpAttackPanel from '@/views/system/pvpAttackPanel/index.vue'

// 匹配views里面所有的.vue文件
const modules = import.meta.glob([
  './../../views/**/*.vue',
  '!./../../views/guild/member/index.vue',
  '!./../../views/system/aiKey/index.vue',
  '!./../../views/system/pvpAttackPanel/index.vue'
])

const usePermissionStore = defineStore(
  'permission',
  {
    state: () => ({
      routes: [],
      addRoutes: [],
      defaultRoutes: [],
      topbarRouters: [],
      sidebarRouters: []
    }),
    actions: {
      setRoutes(routes) {
        this.addRoutes = routes
        this.routes = constantRoutes.concat(routes)
      },
      setDefaultRoutes(routes) {
        this.defaultRoutes = constantRoutes.concat(routes)
      },
      setTopbarRoutes(routes) {
        this.topbarRouters = routes
      },
      setSidebarRouters(routes) {
        this.sidebarRouters = routes
      },
      generateRoutes(roles) {
        return new Promise(resolve => {
          // 向后端请求路由数据
          getRouters().then(res => {
            const sdata = JSON.parse(JSON.stringify(res.data))
            const rdata = JSON.parse(JSON.stringify(res.data))
            const defaultData = JSON.parse(JSON.stringify(res.data))
            const sidebarRoutes = filterAsyncRouter(sdata)
            const rewriteRoutes = filterAsyncRouter(rdata, false, true)
            const defaultRoutes = filterAsyncRouter(defaultData)
            const asyncRoutes = filterDynamicRoutes(dynamicRoutes)
            asyncRoutes.forEach(route => { router.addRoute(route) })
            this.setRoutes(rewriteRoutes)
            this.setSidebarRouters(constantRoutes.concat(sidebarRoutes))
            this.setDefaultRoutes(sidebarRoutes)
            this.setTopbarRoutes(defaultRoutes)
            resolve(rewriteRoutes)
          })
        })
      }
    }
  })

// 遍历后台传来的路由字符串，转换为组件对象
function filterAsyncRouter(asyncRouterMap, lastRouter = false, type = false) {
  return asyncRouterMap.filter(route => {
    if (type && route.children) {
      route.children = filterChildren(route.children)
    }
    if (route.component) {
      // Layout ParentView 组件特殊处理
      if (route.component === 'Layout') {
        route.component = Layout
      } else if (route.component === 'ParentView') {
        route.component = ParentView
      } else if (route.component === 'InnerLink') {
        route.component = InnerLink
      } else {
        route.component = loadView(resolveSpecialView(route))
      }
    }
    if (route.children != null && route.children && route.children.length) {
      route.children = filterAsyncRouter(route.children, route, type)
    } else {
      delete route['children']
      delete route['redirect']
    }
    return true
  })
}

function filterChildren(childrenMap, lastRouter = false) {
  var children = []
  childrenMap.forEach(el => {
    el.path = lastRouter ? lastRouter.path + '/' + el.path : el.path
    if (el.children && el.children.length && el.component === 'ParentView') {
      children = children.concat(filterChildren(el.children, el))
    } else {
      children.push(el)
    }
  })
  return children
}

function resolveSpecialView(route) {
  const view = route.component
  if (view !== 'personal/coming-soon/index') {
    return view
  }

  const routeName = route.name || ''
  const routePath = route.path || ''
  const routeTitle = route.meta?.title || ''

  if (
    routeName === 'PersonalJoinGuild' ||
    routeTitle === '加入帮会' ||
    /(^|\/)join$/.test(routePath)
  ) {
    return 'personal/join/index'
  }

  if (
    routeName === 'PersonalProfileEdit' ||
    routeTitle === '个人信息编辑' ||
    /(^|\/)profile-edit$/.test(routePath)
  ) {
    return 'personal/profileEdit/index'
  }

  if (
    routeName === 'PersonalSkill' ||
    routeTitle === '内功管理' ||
    /(^|\/)skill$/.test(routePath)
  ) {
    return 'personal/skill/index'
  }

  return view
}

// 动态路由遍历，验证是否具备权限
export function filterDynamicRoutes(routes) {
  const res = []
  routes.forEach(route => {
    if (route.permissions) {
      if (auth.hasPermiOr(route.permissions)) {
        res.push(route)
      }
    } else if (route.roles) {
      if (auth.hasRoleOr(route.roles)) {
        res.push(route)
      }
    }
  })
  return res
}

export const loadView = (view) => {
  if (view === 'guild/member/index') {
    return GuildMember
  }
  if (view === 'system/aiKey/index') {
    return SystemAiKey
  }
  if (view === 'system/pvpAttackPanel/index') {
    return SystemPvpAttackPanel
  }

  let res;
  for (const path in modules) {
    const dir = path.split('views/')[1].split('.vue')[0];
    if (dir === view) {
      res = () => modules[path]();
    }
  }
  return res
}

export default usePermissionStore
