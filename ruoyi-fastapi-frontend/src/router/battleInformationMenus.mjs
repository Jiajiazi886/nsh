// Both menu entries share views. Never inject edit permissions into member accounts.
export function addBattleInformationMenus(routes) {
  for (const route of routes) {
    const path=route.path?.replace(/^\//,'')
    if (!['guild','personal'].includes(path)) continue
    route.children ||= []
    if (route.children.some(child=>child.path==='battle-information')) continue
    const prefix=path==='guild'?'Guild':'Personal'
    const children=[
      {path:'mine',name:prefix+'MyBattles',component:'battle-information/mine',meta:{title:'我的约战',icon:'peoples',noCache:true}},
      {path:'history',name:prefix+'BattleHistory',component:'battle-information/history',meta:{title:'历史约战',icon:'documentation',noCache:true}}
    ]
    if(path==='personal')children.splice(1,0,{path:'public',name:prefix+'FindBattles',component:'battle-information/public',meta:{title:'找约战',icon:'search',noCache:true}})
    route.children.push({path:'battle-information',name:prefix+'BattleInformation',component:'ParentView',alwaysShow:true,meta:{title:'约战信息',icon:'date'},children})
  }
  return routes
}
