const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path')
const roots=[path.resolve(__dirname,'..'),path.resolve(__dirname,'../hhhhhhtml/jiusi-data-dashboard-frontend/demo')]
for(const root of roots){
 function runtime(){let definition,token='one',calls=0,payload,fail=false;
 const form={name:'名字',playerUid:'00042',wechatId:'private',hasOrangeWeapon:false,profession:'铁衣',secondaryProfession:'',remark:''}
 const api={playerProfile:async()=>{calls++;return {...form}},activityProfessions:async()=>['铁衣'],savePlayerProfile:async p=>{payload=p;if(fail)throw Error('断网');return p}}
 vm.runInNewContext(fs.readFileSync(path.join(root,'components/player-profile-form/index.js'),'utf8'),{Component:d=>definition=d,require:p=>p.includes('activities')?{getClient:()=>api}:p.includes('storage')?{getToken:()=>token}:{inline:()=>'',refresh:async()=>{}},wx:{showToast:()=>{},showModal:()=>{}}})
 const page={data:JSON.parse(JSON.stringify(definition.data)),...definition.methods,setData(d){for(const [k,v] of Object.entries(d)){const keys=k.split('.');if(keys.length===2)this.data[keys[0]][keys[1]]=v;else this.data[k]=v}}}
 return {page,definition,form,get payload(){return payload},get calls(){return calls},fail(){fail=true},switch(){token='two'}}
 }
 test(path.relative(roots[0],root)+': profile independent of membership and save preserves string uid/boolean',async()=>{const r=runtime();await r.page.load();assert.equal(r.page.data.ready,true);await r.page.save();assert.equal(r.payload.playerUid,'00042');assert.equal(r.payload.hasOrangeWeapon,false)})
 test(path.relative(roots[0],root)+': failed save keeps input; show does not clobber unsaved draft',async()=>{const r=runtime();await r.page.load();r.page.input({currentTarget:{dataset:{field:'name'}},detail:{value:'还未保存'}});r.fail();await r.page.save();assert.equal(r.page.data.form.name,'还未保存');assert.match(r.page.data.error,/断网/);const before=r.calls;r.definition.pageLifetimes.show.call(r.page);await Promise.resolve();assert.equal(r.calls,before);r.switch();r.definition.pageLifetimes.show.call(r.page);await Promise.resolve();assert.equal(r.page.data.ready,false)})
}
