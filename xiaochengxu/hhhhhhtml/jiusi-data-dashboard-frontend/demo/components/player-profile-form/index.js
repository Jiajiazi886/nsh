const {getClient}=require('../../services/activities')
const {getToken}=require('../../utils/storage')
const styles=require('../../utils/profession-styles')
const empty=()=>({name:'',playerUid:'',wechatId:'',hasOrangeWeapon:false,profession:'',secondaryProfession:'',remark:''})
Component({
 data:{form:empty(),ready:false,loading:false,saving:false,error:'',dirty:false,options:[],optionField:'',mainStyle:'',secondaryStyle:''},
 lifetimes:{attached(){this.load()},detached(){this._generation=(this._generation||0)+1}},
 pageLifetimes:{show(){const token=getToken();if(token!==this._token){this._token=token;this.setData({form:empty(),ready:false,dirty:false,error:''});this.load()}else if(!this.data.dirty&&!this.data.saving)this.load();else this.refreshStyles()}},
 methods:{
  async refreshStyles(){await styles.refresh();this.setData({mainStyle:styles.inline(this.data.form.profession),secondaryStyle:styles.inline(this.data.form.secondaryProfession),options:(this._professions||[]).map(name=>({name,style:styles.inline(name)}))})},
  async load(){
   const token=getToken(),g=(this._generation||0)+1;this._generation=g;this._token=token;this.setData({loading:true,error:''})
   try{const api=getClient();const [form,professions]=await Promise.all([api.playerProfile(),api.activityProfessions()]);if(g!==this._generation||getToken()!==token)return;this._baseline={...form};this._professions=professions;this.setData({form,ready:true,dirty:false});await this.refreshStyles()}
   catch(e){if(g===this._generation)this.setData({error:e.message})}
   finally{if(g===this._generation)this.setData({loading:false})}
  },
  input(e){const field=e.currentTarget.dataset.field;this.setData({['form.'+field]:e.detail.value,dirty:true})},
  orange(e){this.setData({'form.hasOrangeWeapon':e.detail.value,dirty:true})},
  openOptions(e){this.setData({optionField:e.currentTarget.dataset.field})},
  closeOptions(){this.setData({optionField:''})},
  choose(e){this.setData({['form.'+this.data.optionField]:e.currentTarget.dataset.name||'',optionField:'',dirty:true});this.refreshStyles()},
  reset(){if(this._baseline){this.setData({form:{...this._baseline},dirty:false,error:''});this.refreshStyles()}},
  reload(){if(this.data.dirty)wx.showModal({title:'重新读取',content:'放弃未保存的填写内容？',success:r=>{if(r.confirm)this.load()}});else this.load()},
  async save(){
   if(this.data.saving)return;if(this._token!==getToken()){this.setData({error:'账号已切换，请重新读取个人资料'});return}
   const payload={...this.data.form};for(const k of ['name','playerUid','wechatId','profession','secondaryProfession','remark'])payload[k]=String(payload[k]||'').trim()
   if(!payload.name||payload.name.length>30||payload.playerUid.length>64||payload.wechatId.length>64||payload.remark.length>500){this.setData({error:'名字必填且最多30字；UID和微信号最多64字，备注最多500字'});return}
   const token=getToken();this.setData({saving:true,error:''})
   try{const form=await getClient().savePlayerProfile(payload);if(getToken()!==token)return;this._baseline={...form};this.setData({form,dirty:false});wx.showToast({title:'玩家资料已保存',icon:'success'});this.refreshStyles()}
   catch(e){this.setData({error:e.message+'；填写内容已保留，请重试保存。'})}
   finally{this.setData({saving:false})}
  }
 }
})
