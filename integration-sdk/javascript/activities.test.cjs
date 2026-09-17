const test=require('node:test'); const assert=require('node:assert/strict'); const {createClient}=require('./client')
test('web and wx use same activity endpoints and string IDs',async()=>{
  const requests=[]; const api=createClient({baseUrl:'http://localhost:9100',getToken:()=> 'token',transport:async r=>{requests.push(r);return {status:200,data:{code:200,success:true,data:{activityId:'a'}}}}})
  await api.activities({kind:'public',profession:'铁衣',vacantOnly:true,page:2})
  await api.activity('a'); await api.saveLineup('a',{expectedRevision:0,operationKey:'op',teams:[]})
  await api.signupSeat('a',{memberId:'9007199254740993',squadId:'s',position:1,expectedRevision:1,operationKey:'j'})
  assert.match(requests[0].url,/profession=%E9%93%81%E8%A1%A3/)
  assert.equal(requests[2].method,'PUT'); assert.equal(requests[2].headers.Authorization,'Bearer token')
  assert.equal(requests[3].data.memberId,'9007199254740993')
})

test('activity leave link endpoints are shared and public calls omit authorization', async () => {
  const requests = []
  const api = createClient({
    baseUrl: 'http://localhost:9100',
    getToken: () => 'private-token',
    transport: async request => {
      requests.push(request)
      return { status: 200, data: { code: 200, success: true, data: {} } }
    }
  })

  await api.activityLeaveInfo('leave/abc')
  await api.activityLeaveMembers('leave/abc', '玩家 甲')
  await api.submitActivityLeave('leave/abc', { memberId: '9', remark: '临时有事' })
  await api.activityLeaves('activity-1')
  await api.activityProfiles('guild-1', 'activity-1')

  assert.equal(requests[0].url, 'http://localhost:9100/api/v1/activity-leave/leave%2Fabc')
  assert.equal(requests[0].headers.Authorization, undefined)
  assert.match(requests[1].url, /keyword=%E7%8E%A9%E5%AE%B6%20%E7%94%B2$/)
  assert.equal(requests[1].headers.Authorization, undefined)
  assert.equal(requests[2].method, 'POST')
  assert.equal(requests[2].headers.Authorization, undefined)
  assert.equal(requests[3].headers.Authorization, 'Bearer private-token')
  assert.match(requests[4].url, /orgId=guild-1&activityId=activity-1$/)
})

test('historical lineup templates use the shared authenticated contract', async () => {
  const requests = []
  const api = createClient({
    baseUrl: 'http://localhost:9100',
    getToken: () => 'actor-token',
    transport: async request => {
      requests.push(request)
      return { status: 200, data: { code: 200, success: true, data: [] } }
    }
  })

  await api.activityLineupTemplates('guild/101')

  assert.equal(requests[0].method, 'GET')
  assert.equal(requests[0].url, 'http://localhost:9100/api/v1/activity-lineup-templates?orgId=guild%2F101')
  assert.equal(requests[0].headers.Authorization, 'Bearer actor-token')
})
