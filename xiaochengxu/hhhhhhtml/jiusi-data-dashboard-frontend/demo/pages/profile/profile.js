const {getClient}=require('../../services/activities')
const {clearSession,getToken}=require('../../utils/storage')
const {folders}=require('../../utils/activity-ui')
Page({data:{user:null,organizations:[],folders:[],error:'',loading:false},onShow(){this.load()},
 async load(){this.setData({loading:true,error:'',user:null});try{const api=getClient();const [user,organizations,players]=await Promise.all([api.me(),api.organizations(),api.activityProfiles()]);this.setData({user,organizations,folders:folders(players)})}catch(e){this.setData({error:e.message,organizations:[],folders:[]})}finally{this.setData({loading:false})}},
 toggle(e){this.setData({folders:this.data.folders.map(f=>f.profession===e.currentTarget.dataset.profession?{...f,expanded:!f.expanded}:f)})},
 goLogin(){wx.reLaunch({url:'/pages/login/login'})},
 async logout(){const token=getToken();try{await getClient().logout()}catch(_){wx.showToast({title:'仅退出本机，后端退出未确认',icon:'none'})}if(getToken()&&getToken()!==token)return;clearSession();wx.reLaunch({url:'/pages/login/login'})}
})
