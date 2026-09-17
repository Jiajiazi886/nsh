<template>
  <div class="app-container box-analysis-page">
    <div class="box-analysis-heading">
      <div>
        <h1>数据分析</h1>
        <p>选择历史保存的排表，再选择固定格式 CSV。数据只在当前浏览器解析，不使用图表。</p>
      </div>
      <Badge variant="outline">分析盒子</Badge>
    </div>

    <Card>
      <CardHeader>
        <CardTitle>分析来源</CardTitle>
        <CardDescription>默认使用当前组织最新排表，也可以切换到任意历史保存版本。</CardDescription>
      </CardHeader>
      <CardContent class="box-analysis-controls">
        <Field>
          <FieldLabel>组织</FieldLabel>
          <Select :model-value="selectedOrgId || '__none__'" :disabled="loading" @update:model-value="selectOrganization">
            <SelectTrigger><SelectValue placeholder="请选择组织" /></SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="__none__">请选择组织</SelectItem>
                <SelectItem v-for="org in organizations" :key="org.orgId" :value="org.orgId">{{ org.name }}（{{ org.orgType === 'guild' ? '帮会' : '俱乐部' }}）</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <Field>
          <FieldLabel>团队配置</FieldLabel>
          <Select :model-value="selectedSnapshotId || '__none__'" :disabled="loading || !templates.length" @update:model-value="selectTemplate">
            <SelectTrigger><SelectValue :placeholder="templates.length ? '选择历史排表' : '暂无历史排表'" /></SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="__none__">{{ templates.length ? '请选择排表' : '暂无历史排表' }}</SelectItem>
                <SelectItem v-for="(item,index) in templates" :key="item.snapshotId" :value="item.snapshotId">{{ index === 0 ? '最新排表 · ' : '' }}{{ item.activityName }} · 版本 {{ item.version }} · {{ formatTime(item.savedAt) }}</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <div class="box-analysis-file">
          <span>比赛数据</span>
          <input ref="fileInput" class="sr-only" type="file" accept=".csv,text/csv" @change="readCsv">
          <Button variant="outline" :disabled="loading" @click="fileInput?.click()">选择 CSV 文件</Button>
          <small>{{ fileName || '尚未选择文件' }}</small>
        </div>
        <Button :disabled="!selectedTemplate || !parsed || loading" @click="analyze">生成分析盒子</Button>
      </CardContent>
    </Card>

    <p v-if="error" class="box-analysis-error" role="alert">{{ error }}</p>
    <div v-if="parsed?.warnings?.length" class="box-analysis-warnings">
      <p v-for="warning in parsed.warnings" :key="warning">{{ warning }}</p>
    </div>

    <template v-if="result">
      <Card>
        <CardHeader>
          <CardTitle>{{ result.selectedGuild || '未识别帮会' }} · 匹配结果</CardTitle>
          <CardDescription>系统按历史排表中的玩家名字自动选择匹配人数最多的 CSV 帮会。</CardDescription>
        </CardHeader>
        <CardContent class="box-analysis-summary">
          <div><span>排表人数</span><strong>{{ result.configuredPlayers }}</strong></div>
          <div><span>CSV 人数</span><strong>{{ result.csvPlayers }}</strong></div>
          <div><span>已匹配</span><strong>{{ result.matchedPlayers }}</strong></div>
          <div><span>CSV 独有</span><strong>{{ result.csvOnlyPlayers }}</strong></div>
          <div><span>缺少数据</span><strong>{{ result.missingDataPlayers }}</strong></div>
        </CardContent>
      </Card>

      <div class="box-analysis-list">
        <Card v-for="box in result.boxes" :key="box.id" class="analysis-box">
          <CardHeader class="analysis-box-header">
            <div>
              <CardTitle>{{ box.name }}</CardTitle>
              <CardDescription>匹配 {{ box.matchedPlayers }} / {{ box.configuredPlayers }} 人</CardDescription>
            </div>
            <Button variant="ghost" size="sm" @click="toggleBox(box.id)">{{ expanded.has(box.id) ? '收起' : '展开' }}</Button>
          </CardHeader>
          <CardContent>
            <div class="analysis-box-metrics">
              <div v-for="metric in visibleMetrics" :key="metric.key"><span>{{ metric.label }}</span><strong>{{ metricValue(box.metrics, metric) }}</strong></div>
            </div>
            <div v-if="expanded.has(box.id)" class="analysis-squads">
              <section v-for="squad in box.squads" :key="squad.id">
                <header><strong>{{ squad.name }}</strong><span>{{ squad.matchedPlayers }} / {{ squad.configuredPlayers }} 人有数据</span></header>
                <div class="analysis-players">
                  <div v-for="player in squad.players" :key="player.name" :class="{ missing: !player.hasData }">
                    <span class="analysis-player-name">{{ player.name }}</span>
                    <ProfessionTag :name="player.profession" />
                    <small>{{ player.hasData ? `击败 ${formatNumber(player.metrics.kills)} · 助攻 ${formatNumber(player.metrics.assists)}` : '无比赛数据' }}</small>
                  </div>
                </div>
              </section>
            </div>
          </CardContent>
        </Card>
      </div>
    </template>

    <Card v-else class="box-analysis-empty">
      <CardContent>选择团队配置和 CSV 后，点击“生成分析盒子”。</CardContent>
    </Card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { activityApi } from '@/api/activities'
import ProfessionTag from '@/components/ProfessionTag/index.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldLabel } from '@/components/ui/field'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { parseBattleCsv } from '@/views/battle-information/battleCsv.mjs'
import { buildBoxAnalysis } from './analysisBoxes.mjs'

const organizations=ref([]),selectedOrgId=ref(''),templates=ref([]),selectedSnapshotId=ref(''),fileInput=ref(null),fileName=ref(''),parsed=ref(null),result=ref(null),expanded=ref(new Set()),loading=ref(false),error=ref('')
const selectedTemplate=computed(()=>templates.value.find(item=>item.snapshotId===selectedSnapshotId.value)||null)
const visibleMetrics=[
  {key:'kills',label:'击败／清泉',pair:'qingquan_kills'},
  {key:'assists',label:'助攻'},
  {key:'dmg_to_players',label:'对玩家伤害'},
  {key:'healing',label:'治疗值'},
  {key:'dmg_taken',label:'承受伤害'},
  {key:'deaths',label:'重伤'},
]

function formatTime(value){return value?String(value).replace('T',' ').slice(0,16):'时间未知'}
function formatNumber(value){try{return BigInt(value||'0').toLocaleString('zh-CN')}catch{return '0'}}
function metricValue(metrics,metric){const first=formatNumber(metrics?.[metric.key]);return metric.pair?`${first} / ${formatNumber(metrics?.[metric.pair])}`:first}
function resetResult(){result.value=null;expanded.value=new Set()}
function toggleBox(id){const next=new Set(expanded.value);next.has(id)?next.delete(id):next.add(id);expanded.value=next}
function selectOrganization(value){selectedOrgId.value=value==='__none__'?'':value;loadTemplates()}
function selectTemplate(value){selectedSnapshotId.value=value==='__none__'?'':value;resetResult()}

async function loadOrganizations(){
  loading.value=true;error.value=''
  try{organizations.value=(await activityApi.organizations()).filter(org=>org.canManage);selectedOrgId.value=organizations.value[0]?.orgId||'';await loadTemplates()}
  catch(e){error.value=e.message}
  finally{loading.value=false}
}
async function loadTemplates(){
  templates.value=[];selectedSnapshotId.value='';resetResult();if(!selectedOrgId.value)return
  try{templates.value=await activityApi.activityLineupTemplates(selectedOrgId.value);selectedSnapshotId.value=templates.value[0]?.snapshotId||''}
  catch(e){error.value=e.message}
}
async function readCsv(event){
  const file=event.target.files?.[0];parsed.value=null;fileName.value='';resetResult();error.value=''
  if(!file)return
  if(!/\.csv$/i.test(file.name)){error.value='只支持 .csv 文件';return}
  try{parsed.value=parseBattleCsv(await file.text());fileName.value=file.name}
  catch(e){error.value=e.message}
  finally{event.target.value=''}
}
function analyze(){if(!selectedTemplate.value||!parsed.value)return;try{result.value=buildBoxAnalysis(selectedTemplate.value.teams,parsed.value.records)}catch(e){error.value=e.message}}
onMounted(loadOrganizations)
</script>

<style scoped>
.box-analysis-page{display:grid;gap:14px;color:#172033}.box-analysis-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.box-analysis-heading h1{margin:0 0 6px;font-size:24px}.box-analysis-heading p{margin:0;color:#667085}.box-analysis-controls{display:grid;grid-template-columns:minmax(180px,.7fr) minmax(280px,1.3fr) minmax(200px,.8fr) auto;gap:12px;align-items:end}.box-analysis-file{display:grid;gap:7px}.box-analysis-file>span{font-size:13px;font-weight:600}.box-analysis-file small{overflow:hidden;color:#667085;text-overflow:ellipsis;white-space:nowrap}.box-analysis-error,.box-analysis-warnings{margin:0;border:1px solid #fecaca;border-radius:8px;background:#fff7f7;color:#b42318;padding:11px 13px}.box-analysis-warnings{border-color:#f6d58c;background:#fffaf0;color:#8a5a00}.box-analysis-warnings p{margin:3px 0}.box-analysis-summary{display:grid;grid-template-columns:repeat(5,minmax(100px,1fr));gap:10px}.box-analysis-summary>div,.analysis-box-metrics>div{border:1px solid #e1e5eb;border-radius:8px;background:#fafbfc;padding:10px}.box-analysis-summary span,.analysis-box-metrics span{display:block;color:#667085;font-size:12px}.box-analysis-summary strong{display:block;margin-top:3px;font-size:21px}.box-analysis-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.analysis-box-header{display:flex;flex-direction:row;align-items:center;justify-content:space-between}.analysis-box-metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.analysis-box-metrics strong{display:block;margin-top:4px;font-size:14px}.analysis-squads{display:grid;gap:10px;margin-top:12px;padding-top:12px;border-top:1px solid #e4e7ec}.analysis-squads section{border:1px solid #e1e5eb;border-radius:8px;padding:10px}.analysis-squads header{display:flex;justify-content:space-between;gap:10px;font-size:13px}.analysis-squads header span{color:#667085}.analysis-players{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;margin-top:9px}.analysis-players>div{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 8px;align-items:center;border-radius:6px;background:#f7f8fa;padding:7px 8px;font-size:12px}.analysis-players>div.missing{background:#fff8e8}.analysis-player-name{overflow:hidden;font-weight:600;text-overflow:ellipsis;white-space:nowrap}.analysis-players small{grid-column:1/-1;color:#667085}.box-analysis-empty{text-align:center;color:#667085}.box-analysis-empty :deep([data-slot=card-content]){padding-top:24px}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@media(max-width:1100px){.box-analysis-controls{grid-template-columns:1fr 1fr}.box-analysis-list{grid-template-columns:1fr}}@media(max-width:700px){.box-analysis-controls,.box-analysis-summary{grid-template-columns:1fr}.analysis-box-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.analysis-players{grid-template-columns:1fr}}
</style>
