const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const root=path.resolve(__dirname,'../..');
test('account profile and styles SDK uses authenticated shared endpoints',async()=>{
 const requests=[];const api=require('./client').createClient({baseUrl:'http://local',getToken:()=> 'actor',transport:async r=>{requests.push(r);return{status:200,data:{code:200,success:true,data:r.data||[]}}}});
 await api.professionStyles();await api.playerProfile();await api.savePlayerProfile({name:'名字',playerUid:'0001',hasOrangeWeapon:false});await api.organizationPlayerProfile('guild-1','23');
 assert.deepEqual(requests.map(r=>[r.method,r.url]),[['GET','http://local/api/v1/profession-styles'],['GET','http://local/api/v1/player-profile/me'],['PUT','http://local/api/v1/player-profile/me'],['GET','http://local/api/v1/organizations/guild-1/player-profiles/23']]);
 assert.ok(requests.every(r=>r.headers.Authorization==='Bearer actor'));assert.equal(requests[2].data.playerUid,'0001');
});
test('mini style cache isolates accounts and ignores stale in-flight response',async()=>{
 const {createStyleCache}=require('./profession-styles');let token='one',release;const cache=createStyleCache({getIdentity:()=>token,load:()=>new Promise(r=>release=r)});
 const pending=cache.refresh();await Promise.resolve();token='two';assert.notEqual(cache.style('铁衣').backgroundColor,'#123456');release([{profession:'铁衣',backgroundColor:'#123456',textColor:'#abcdef'}]);await pending;assert.notEqual(cache.style('铁衣').backgroundColor,'#123456');
 const own=createStyleCache({getIdentity:()=>token,load:async()=>[{profession:'铁衣',backgroundColor:'#ffffff',textColor:'#000000'}]});await own.refresh();assert.equal(own.style('铁衣').backgroundColor,'#ffffff');token='three';assert.notEqual(own.style('铁衣').backgroundColor,'#ffffff');
});
test('web lineup is drag-only and six-seat mini layout is compact',()=>{
 const editor=fs.readFileSync(path.join(root,'ruoyi-fastapi-frontend/src/views/battle-information/LineupEditor.vue'),'utf8');assert.doesNotMatch(editor,/openPicker|pickerVisible|选择玩家/);assert.match(editor,/@drop.prevent/);assert.match(editor,/requiredProfession/);
 for(const mini of ['xiaochengxu','xiaochengxu/hhhhhhtml/jiusi-data-dashboard-frontend/demo']){
  const css=fs.readFileSync(path.join(root,mini,'utils/activity.wxss'),'utf8');assert.match(css,/grid-template-columns:repeat\(3,/);assert.match(css,/seat-empty/);
 }
});
