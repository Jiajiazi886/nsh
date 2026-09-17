const test=require('node:test');const assert=require('node:assert/strict');const {listPage,detailPage,folders}=require('../utils/activity-ui')
test('mine separates guild/club; profession folders collapsed',()=>{const page=listPage({detail:'/detail',report:'/report'});let loads=0;page.load=()=>{loads++};page.setData=function(d){Object.assign(this.data,d)};page._items=[{activityId:'g',orgType:'guild'},{activityId:'c',orgType:'club'}];page.renderItems();assert.equal(page.data.items[0].activityId,'g');page.setOrganization({currentTarget:{dataset:{type:'club'}}});assert.equal(page.data.items[0].activityId,'c');assert.equal(loads,1);assert.ok(folders([{name:'甲',profession:'铁衣'}]).every(f=>!f.expanded));assert.notEqual(folders([{profession:'铁衣'},{profession:'素问'}])[0].color,folders([{profession:'铁衣'},{profession:'素问'}])[1].color)})
test('detail is read only, no local seat mutations or demo fallback',()=>{const page=detailPage({report:'/report'});assert.equal(page.assignPlayer,undefined);assert.equal(page.editSeat,undefined);assert.equal(typeof page.signup,'function');assert.equal(typeof page.leave,'function')})
test('role picker uses profession folders initially collapsed and selecting is local',()=>{
 const page=detailPage({report:'/report'});page.setData=function(d){Object.assign(this.data,d)}
 page.data.profileFolders=folders([{name:'甲',memberId:'9',profession:'铁衣',index:0}])
 page.toggleProfileOptions();assert.equal(page.data.profileChoiceVisible,true);assert.ok(page.data.profileFolders.every(f=>!f.expanded))
 page.toggleProfileFolder({currentTarget:{dataset:{profession:'铁衣'}}});assert.equal(page.data.profileFolders[0].expanded,true)
 page.selectProfile({currentTarget:{dataset:{index:0}}});assert.equal(page.data.profileIndex,0);assert.equal(page.data.profileChoiceVisible,false)
})
