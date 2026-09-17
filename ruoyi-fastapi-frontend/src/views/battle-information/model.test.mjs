import test from 'node:test'
import assert from 'node:assert/strict'
import { makeDraft, makeSquad, assignPlayer, setRequirement, setSeatNotes, toSaveRequest, professionFolders, initialTeams } from './model.mjs'

test('six seats, scoped draft, mismatch refuses without mutating',()=>{
  const d=makeDraft({activityId:'a',revision:2,snapshot:{teams:initialTeams('t','s')}})
  const first=d.teams[0].squads[0]
  assert.equal(first.seats.length,6)
  const locked=setRequirement(d,'s',1,'铁衣')
  assert.throws(()=>assignPlayer(locked,'s',1,{memberId:'9',name:'甲',profession:'素问'}),/职业/)
  assert.equal(locked.teams[0].squads[0].seats[0].player,null)
  const assigned=assignPlayer(locked,'s',1,{memberId:'9',name:'甲',profession:'铁衣',isTemporary:false})
  assert.throws(()=>setRequirement(assigned,'s',1,'素问'),/职业/)
  const request=toSaveRequest(assigned,'op1')
  assert.equal(request.expectedRevision,2)
  assert.deepEqual(request.teams[0].squads[0].seats[0].player,{memberId:'9'})
  assert.equal(d.teams[0].squads[0].seats[0].player,null)
})

test('move players, temporary identity, folders collapsed default',()=>{
  let d=makeDraft({activityId:'a',revision:0,snapshot:{teams:initialTeams('t','s')}})
  d=assignPlayer(d,'s',1,{temporaryId:'temp_a',name:'临时',profession:'铁衣',isTemporary:true})
  d=assignPlayer(d,'s',2,d.teams[0].squads[0].seats[0].player)
  assert.equal(d.teams[0].squads[0].seats[0].player,null)
  assert.equal(toSaveRequest(d,'op').teams[0].squads[0].seats[1].player.temporaryId,'temp_a')
  assert.ok(professionFolders([{name:'甲',profession:'铁衣'}]).every(f=>f.expanded===false))
})

test('cross squad swap validates both sides without mutating the original',()=>{
 let d=makeDraft({activityId:'a',revision:0,snapshot:{teams:[{id:'t',name:'团',squads:[makeSquad('s1','一队'),makeSquad('s2','二队')]}]}})
 d=setRequirement(d,'s1',1,'铁衣')
 d=assignPlayer(d,'s1',1,{memberId:'9',name:'甲',profession:'铁衣'})
 d=assignPlayer(d,'s2',1,{memberId:'10',name:'乙',profession:'素问'})
 const original=JSON.stringify(d)
 assert.throws(()=>assignPlayer(d,'s2',1,d.teams[0].squads[0].seats[0].player),/职业/)
 assert.equal(JSON.stringify(d),original)
 assert.throws(()=>assignPlayer(d,'s1',1,d.teams[0].squads[1].seats[0].player),/职业/)
 assert.equal(JSON.stringify(d),original)
 const unrestricted=setRequirement(d,'s1',1,'')
 const swapped=assignPlayer(unrestricted,'s2',1,unrestricted.teams[0].squads[0].seats[0].player)
 assert.equal(swapped.teams[0].squads[0].seats[0].player.name,'乙')
 assert.equal(swapped.teams[0].squads[1].seats[0].player.name,'甲')
})

test('position notes support combined presets and are included in saved snapshots', () => {
  const draft = makeDraft({ activityId: 'a', revision: 0, snapshot: { teams: initialTeams('t', 's') } })
  const noted = setSeatNotes(draft, 's', 1, ['指挥', '保镖', '指挥', '  '])
  assert.deepEqual(noted.teams[0].squads[0].seats[0].notes, ['指挥', '保镖'])
  assert.deepEqual(toSaveRequest(noted, 'notes').teams[0].squads[0].seats[0].notes, ['指挥', '保镖'])
  assert.deepEqual(draft.teams[0].squads[0].seats[0].notes, [])
})
