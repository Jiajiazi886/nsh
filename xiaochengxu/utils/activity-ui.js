const {getClient}=require('../services/activities')
const professionStyles=require('./profession-styles')
const colorOf=p=>professionStyles.style(p).backgroundColor
const textColorOf=p=>professionStyles.style(p).color
const time=t=>(t||'').replace('T',' ')
const op=()=> 'wx_'+Date.now()+'_'+Math.random().toString(36).slice(2)
const folders=players=>[...new Set(players.map(p=>p.profession||'未设置'))].sort().map(profession=>({profession,color:colorOf(profession),textColor:textColorOf(profession),expanded:false,players:players.filter(p=>(p.profession||'未设置')===profession)}))

function listPage(paths){return {
  data:{kind:'mine',orgType:'guild',items:[],professions:['不限职业'],professionIndex:0,professionOptionsVisible:false,vacantOnly:false,page:1,total:0,hasNext:false,loading:false,error:'',hint:''},
  onShow(){if(typeof this.getTabBar==='function'){const tab=this.getTabBar();if(tab)tab.setData({selected:1})}this.load()},
  onUnload(){this._generation=(this._generation||0)+1},
  onPullDownRefresh(){this.load().finally(()=>wx.stopPullDownRefresh())},
  setKind(e){this.setData({kind:e.currentTarget.dataset.kind,page:1,items:[]});this.load()},
  setOrganization(e){this.setData({orgType:e.currentTarget.dataset.type,page:1});this.renderItems();this.load()},
  toggleProfessionOptions(){this.setData({professionOptionsVisible:!this.data.professionOptionsVisible})},
  selectProfession(e){this.setData({professionOptionsVisible:false});this.professionChange({detail:{value:e.currentTarget.dataset.index}})},
  professionChange(e){this.setData({professionIndex:Number(e.detail.value),page:1});this.load()},
  vacancyChange(e){this.setData({vacantOnly:e.detail.value.length>0,page:1});this.load()},
  previous(){if(this.data.page>1){this.setData({page:this.data.page-1});this.load()}},
  next(){if(this.data.hasNext){this.setData({page:this.data.page+1});this.load()}},
  renderItems(){const all=this._items||[];this.setData({items:this.data.kind==='mine'?all.filter(a=>a.orgType===this.data.orgType):all})},
  async load(){const g=(this._generation||0)+1;this._generation=g;this.setData({loading:true,error:'',items:[]});try{const api=getClient();await professionStyles.refresh();const [r,p]=await Promise.all([api.activities({kind:this.data.kind,orgType:this.data.kind==='mine'?this.data.orgType:undefined,page:this.data.page,pageSize:20,profession:this.data.professionIndex?this.data.professions[this.data.professionIndex]:'',vacantOnly:this.data.vacantOnly,participatingOnly:this.data.kind==='mine'}),api.activityProfessions()]);if(g!==this._generation)return;this._items=r.items.map(a=>({...a,timeText:time(a.startsAt),statusText:a.state==='ended'?'已结束':a.isPublic?'公开报名':'组织内部',filledSeats:a.totalSeats-a.emptySeats,shortageTags:Object.keys(a.shortages).map(profession=>({profession,count:a.shortages[profession],color:colorOf(profession),textColor:textColorOf(profession)}))}));this.setData({total:r.total,hasNext:this.data.page*20<r.total,professions:['不限职业',...p],hint:this.data.kind==='mine'?'只显示本人已经参加的帮会和俱乐部约战。':this.data.kind==='public'?'按位置职业要求报名，阵容只读。':'所属组织已到期约战及本人参加过的公开约战。'});this.renderItems()}catch(e){if(g===this._generation){this._items=[];this.setData({error:e.message,items:[]})}}finally{if(g===this._generation)this.setData({loading:false})}},
  open(e){wx.navigateTo({url:paths.detail+'?id='+encodeURIComponent(e.currentTarget.dataset.id)})},
  report(e){wx.navigateTo({url:paths.report+'?id='+encodeURIComponent(e.currentTarget.dataset.id)})}
}}

function detailPage(paths){return {
  data:{activity:null,teams:[],profiles:[],profileLabels:[],profileIndex:0,profileChoiceVisible:false,profileFolders:[],loading:false,busy:false,error:'',profileError:'',snapshots:[],snapshotVisible:false},
  onLoad(options){this.activityId=options.id},onShow(){this.load()},onUnload(){this._generation=(this._generation||0)+1},
  toggleProfileOptions(){this.setData({profileChoiceVisible:!this.data.profileChoiceVisible,profileFolders:this.data.profileFolders.map(f=>({...f,expanded:false}))})},
  toggleProfileFolder(e){this.setData({profileFolders:this.data.profileFolders.map(f=>f.profession===e.currentTarget.dataset.profession?{...f,expanded:!f.expanded}:f)})},
  selectProfile(e){this.setData({profileIndex:Number(e.currentTarget.dataset.index),profileChoiceVisible:false})},
  profileChange(e){this.setData({profileIndex:Number(e.detail.value)})},
  async load(){const g=(this._generation||0)+1;this._generation=g;this.setData({loading:true,error:'',activity:null,teams:[]});try{const api=getClient();await professionStyles.refresh();const a=await api.activity(this.activityId);let profiles=[];try{profiles=await api.activityProfiles();if(g===this._generation)this.setData({profileError:''})}catch(e){if(g===this._generation)this.setData({profileError:e.message})}if(g!==this._generation)return;const mine=new Set(profiles.map(p=>p.memberId));const teams=(a.snapshot?a.snapshot.teams:[]).map(t=>({...t,squads:t.squads.map(s=>({...s,filled:s.seats.filter(seat=>seat.player).length,seats:s.seats.map(seat=>({...seat,color:colorOf(seat.player?seat.player.profession:seat.requiredProfession),textColor:textColorOf(seat.player?seat.player.profession:seat.requiredProfession),requiredStyle:professionStyles.inline(seat.requiredProfession),isMine:!!(seat.player&&mine.has(seat.player.memberId))}))}))}));this.setData({activity:{...a,timeText:time(a.startsAt),savedText:a.snapshot?time(a.snapshot.savedAt):'',statusText:a.state==='ended'?'已结束':a.isPublic?'公开报名':'组织内部'},teams,profiles,profileFolders:folders(profiles.map((p,index)=>({...p,index}))),profileChoiceVisible:false,profileLabels:profiles.map(p=>p.name+' · '+p.profession),profileIndex:Math.min(this.data.profileIndex,Math.max(0,profiles.length-1))})}catch(e){if(g===this._generation)this.setData({error:e.message,activity:null,teams:[]})}finally{if(g===this._generation)this.setData({loading:false})}},
  async action(fn){if(this.data.busy)return;this.setData({busy:true,error:''});try{await fn();await this.load()}catch(e){this.setData({error:e.message+'；请刷新确认状态后重试。'})}finally{this.setData({busy:false})}},
  signup(e){const p=this.data.profiles[this.data.profileIndex];if(!p)return wx.showToast({title:'请先完善绑定角色资料',icon:'none'});const request={expectedRevision:this.data.activity.revision,operationKey:op(),memberId:p.memberId,squadId:e.currentTarget.dataset.squad,position:Number(e.currentTarget.dataset.position)};return this.action(()=>getClient().signupSeat(this.activityId,request))},
  leave(e){const request={expectedRevision:this.data.activity.revision,operationKey:op(),memberId:e.currentTarget.dataset.member};return this.action(()=>getClient().leaveSeat(this.activityId,request))},
  publish(){wx.showModal({title:'发布公开',content:'所有已登录用户将可查看并按职业要求报名。',success:r=>{if(r.confirm)this.action(()=>getClient().publishActivity(this.activityId,{expectedRevision:this.data.activity.revision,operationKey:op()}))}})},
  end(){wx.showModal({title:'结束活动',content:'结束后冻结阵容，不能继续报名或编辑。',success:r=>{if(r.confirm)this.action(()=>getClient().endActivity(this.activityId,{expectedRevision:this.data.activity.revision,operationKey:op()}))}})},
  report(e){wx.navigateTo({url:paths.report+'?id='+encodeURIComponent(e.currentTarget.dataset.id)})},
  async history(){try{const snapshots=await getClient().activitySnapshots(this.activityId);this.setData({snapshots:snapshots.map(s=>({...s,timeText:time(s.savedAt)})),snapshotVisible:!this.data.snapshotVisible})}catch(e){this.setData({error:e.message})}},
}}

function reportPage(){return {
  data:{loading:false,error:'',report:null,folders:[]},onLoad(o){this.reportId=o.id;this.load()},
  async load(){this.setData({loading:true,error:'',report:null,folders:[]});try{await professionStyles.refresh();const report=await getClient().activityReport(this.reportId);this.setData({report,folders:folders(report.players)})}catch(e){this.setData({error:e.message})}finally{this.setData({loading:false})}},
  toggle(e){const profession=e.currentTarget.dataset.profession;this.setData({folders:this.data.folders.map(f=>f.profession===profession?{...f,expanded:!f.expanded}:f)})}
}}
module.exports={listPage,detailPage,reportPage,colorOf,folders}
