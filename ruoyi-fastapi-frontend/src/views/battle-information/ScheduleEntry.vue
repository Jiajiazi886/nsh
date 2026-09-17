<template>
  <div v-if="error" class="battle-page">
    <p class="battle-error">{{ error }}</p>
    <Button variant="outline" @click="load">重试</Button>
  </div>

  <LineupEditor
    v-else-if="activity"
    :key="activity.activityId"
    :activity="activity"
    @saved="saved"
  />

  <div v-else class="battle-page battle-schedule-entry">
    <header class="battle-list-heading">
      <div>
        <h2>约战排表</h2>
        <p class="battle-muted">约战只能从这里创建。创建后立即进入团队、小队和位置配置。</p>
      </div>
      <Button :disabled="loading || !managedOrgs.length" @click="openCreate">创建约战</Button>
    </header>

    <Card class="battle-schedule-picker">
      <CardHeader>
        <CardTitle>继续配置已有约战</CardTitle>
        <CardDescription>选择你有权管理且尚未结束的活动。</CardDescription>
      </CardHeader>
      <CardContent class="flex flex-col gap-3">
        <div class="battle-schedule-actions">
          <Select v-model="selectedId" :disabled="loading">
            <SelectTrigger class="min-w-[280px]">
              <SelectValue placeholder="选择可管理的约战" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem v-for="a in activities" :key="a.activityId" :value="a.activityId">
                  {{ a.orgName }} · {{ a.name }}
                </SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
          <Button variant="outline" :disabled="loading || !selectedId" @click="select">配置所选活动</Button>
          <Button variant="ghost" @click="router.push('/personal/battle-information/mine')">查看我的约战</Button>
        </div>
        <p v-if="loading" class="battle-muted" role="status">正在读取可管理约战…</p>
        <p v-else-if="!managedOrgs.length" class="battle-muted">你当前不是任何帮会或俱乐部的管理员／助手，不能创建约战。</p>
      </CardContent>
    </Card>

    <Dialog v-model:open="createVisible">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>创建约战</DialogTitle>
          <DialogDescription>填写所属组织、名称和约战时间；创建后进入排表。</DialogDescription>
        </DialogHeader>

        <FieldGroup>
          <Field :data-invalid="!!formError && !form.orgId">
            <FieldLabel for="battle-organization">所属组织</FieldLabel>
            <Select v-model="form.orgId">
              <SelectTrigger id="battle-organization" class="w-full" :aria-invalid="!!formError && !form.orgId">
                <SelectValue placeholder="选择组织" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem v-for="o in managedOrgs" :key="o.orgId" :value="o.orgId">
                    {{ o.name }}（{{ o.orgType === 'guild' ? '帮会' : '俱乐部' }}）
                  </SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>

          <Field :data-invalid="!!formError && !form.name.trim()">
            <FieldLabel for="battle-name">活动名称</FieldLabel>
            <Input id="battle-name" v-model="form.name" maxlength="100" :aria-invalid="!!formError && !form.name.trim()" />
          </Field>

          <Field :data-invalid="!!formError && !form.battleAt">
            <FieldLabel for="battle-time">约战时间</FieldLabel>
            <Input
              id="battle-time"
              v-model="form.battleAt"
              type="datetime-local"
              step="60"
              :aria-invalid="!!formError && !form.battleAt"
            />
            <FieldDescription>默认选择最近一个尚未错过的周二或周四 20:30，也可以手动修改。</FieldDescription>
          </Field>

          <Field>
            <FieldLabel for="battle-remark">说明（对外可见，请勿填写密码或联系方式）</FieldLabel>
            <Textarea id="battle-remark" v-model="form.remark" maxlength="500" />
          </Field>

          <FieldError :errors="[formError]" />
        </FieldGroup>

        <DialogFooter>
          <Button variant="outline" :disabled="submitting" @click="createVisible=false">取消</Button>
          <Button :disabled="submitting" @click="create">{{ submitting ? '正在创建…' : '创建并配置排表' }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import {computed,ref,watch} from 'vue'
import {useRoute,useRouter} from 'vue-router'
import {activityApi} from '@/api/activities'
import LineupEditor from './LineupEditor.vue'
import {defaultBattleTime,toLegacyActivityTimes} from './activityTime.mjs'
import {Button} from '@/components/ui/button'
import {Card,CardContent,CardDescription,CardHeader,CardTitle} from '@/components/ui/card'
import {Dialog,DialogContent,DialogDescription,DialogFooter,DialogHeader,DialogTitle} from '@/components/ui/dialog'
import {Field,FieldDescription,FieldError,FieldGroup,FieldLabel} from '@/components/ui/field'
import {Input} from '@/components/ui/input'
import {Select,SelectContent,SelectGroup,SelectItem,SelectTrigger,SelectValue} from '@/components/ui/select'
import {Textarea} from '@/components/ui/textarea'
import './activity.css'

const route=useRoute(),router=useRouter()
const loading=ref(false),error=ref(''),activity=ref(null),activities=ref([]),selectedId=ref('')
const organizations=ref([]),createVisible=ref(false),submitting=ref(false),formError=ref('')
const form=ref({orgId:'',name:'',battleAt:defaultBattleTime(),remark:''})
const managedOrgs=computed(()=>organizations.value.filter(o=>o.canManage))
let generation=0

async function load(){
  const g=++generation
  loading.value=true
  error.value=''
  activity.value=null
  try{
    if(route.query.activityId){
      const a=await activityApi.activity(String(route.query.activityId))
      if(!a.canManage)throw Error('你没有该活动排表管理权限')
      if(a.state==='ended')throw Error('活动已结束，阵容只能查看')
      if(g===generation)activity.value=a
      return
    }

    const [result,orgs]=await Promise.all([loadManageableActivities(),activityApi.organizations()])
    if(g!==generation)return
    activities.value=result.filter(a=>a.canManage&&a.state!=='ended')
    organizations.value=orgs
    if(!form.value.orgId)form.value.orgId=managedOrgs.value[0]?.orgId||''
  }catch(e){
    if(g===generation)error.value=e.message
  }finally{
    if(g===generation)loading.value=false
  }
}

async function loadManageableActivities(){
  const result=[]
  let page=1
  while(true){
    const response=await activityApi.activities({kind:'mine',page,pageSize:100})
    result.push(...response.items)
    if(result.length>=response.total)break
    page++
  }
  return result
}

function openCreate(){
  form.value={orgId:form.value.orgId||managedOrgs.value[0]?.orgId||'',name:'',battleAt:defaultBattleTime(),remark:''}
  formError.value=''
  createVisible.value=true
}

async function create(){
  if(!form.value.orgId||!form.value.name.trim()||!form.value.battleAt){
    formError.value='请完整填写所属组织、活动名称和约战时间'
    return
  }
  submitting.value=true
  formError.value=''
  try{
    const {battleAt,...base}=form.value
    const created=await activityApi.createActivity({...base,name:base.name.trim(),...toLegacyActivityTimes(battleAt)})
    createVisible.value=false
    router.push({path:'/guild/schedule',query:{activityId:created.activityId}})
  }catch(e){
    formError.value=e.message
  }finally{
    submitting.value=false
  }
}

function select(){router.push({path:'/guild/schedule',query:{activityId:selectedId.value}})}
function saved(result){activity.value={...activity.value,revision:result.revision}}
watch(()=>route.query.activityId,load,{immediate:true})
</script>
