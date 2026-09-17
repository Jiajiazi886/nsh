export const clone = value => JSON.parse(JSON.stringify(value))
export const playerKey = p => p?.memberId || p?.temporaryId
export const makeSquad = (id,name='一队') => ({id,name,seats:Array.from({length:6},(_,i)=>({position:i+1,requiredProfession:'',notes:[],player:null}))})
export const initialTeams = (teamId,squadId) => [{id:teamId,name:'一团',squads:[makeSquad(squadId)]}]
export const makeDraft = activity => ({version:1,activityId:activity.activityId,baseRevision:activity.revision,teams:clone(activity.snapshot?.teams || []),dirty:false,localRevision:0})
export const changeDraft = (draft,action) => { const next=clone(draft); action(next.teams); next.dirty=true; next.localRevision++; delete next.pending; return next }
const getSeat = (teams,squadId,position) => teams.flatMap(t=>t.squads).find(s=>s.id===squadId)?.seats.find(s=>s.position===position)
const check = (seat,player) => { if(!seat) throw Error('位置不存在'); if(player && seat.requiredProfession && seat.requiredProfession!==player.profession) throw Error('玩家职业不符合位置要求') }
export function assignPlayer(draft,squadId,position,player) {
  return changeDraft(draft,teams=>{
    const target=getSeat(teams,squadId,position); check(target,player)
    const all=teams.flatMap(t=>t.squads).flatMap(s=>s.seats)
    const origin=player && all.find(s=>playerKey(s.player)===playerKey(player))
    if(origin===target) return
    if(origin) {check(origin,target.player); origin.player=target.player}
    target.player=player?clone(player):null
  })
}
export const setRequirement = (draft,squadId,position,profession) => changeDraft(draft,teams=>{
  const seat=getSeat(teams,squadId,position); if(!seat) throw Error('位置不存在')
  if(seat.player && profession && seat.player.profession!==profession) throw Error('已安排玩家的职业与指定职业不符，请先移出玩家')
  seat.requiredProfession=profession
})
export const setSeatNotes = (draft,squadId,position,notes) => changeDraft(draft,teams=>{
  const seat=getSeat(teams,squadId,position); if(!seat) throw Error('位置不存在')
  seat.notes=[...new Set((notes||[]).map(note=>String(note).trim()).filter(Boolean))].slice(0,20)
})
export const professionFolders = players => [...new Set(players.map(p=>p.profession || '未设置'))].sort((a,b)=>a.localeCompare(b,'zh-CN')).map(profession=>({profession,expanded:false,players:players.filter(p=>(p.profession||'未设置')===profession)}))
export function toSaveRequest(draft,operationKey) {
  const teams=clone(draft.teams)
  for(const team of teams) for(const squad of team.squads) for(const seat of squad.seats) if(seat.player) {
    const p=seat.player
    seat.player=p.isTemporary ? {temporaryId:p.temporaryId,name:p.name,profession:p.profession} : {memberId:String(p.memberId)}
  }
  return {expectedRevision:draft.baseRevision,operationKey,teams}
}
