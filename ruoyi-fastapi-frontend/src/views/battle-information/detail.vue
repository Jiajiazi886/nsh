<template>
  <div class="battle-page battle-detail-page">
    <div class="battle-detail-nav">
      <Button variant="outline" @click="router.back()">返回</Button>
      <Button variant="outline" :disabled="loading" @click="load">{{ loading ? '刷新中…' : '刷新' }}</Button>
    </div>
    <p v-if="loading && !activity" class="battle-muted" role="status">正在读取约战详情…</p>
    <p v-if="error" class="battle-error" role="alert">{{ error }}</p>

    <template v-if="activity">
      <section class="battle-panel battle-detail-head">
        <div class="battle-detail-title">
          <div>
            <h2>{{ activity.name }}</h2>
            <p class="battle-detail-meta">{{ activity.orgName }} · {{ activity.orgType === 'guild' ? '帮会' : '俱乐部' }} · {{ statusText }}</p>
          </div>
          <div class="battle-detail-time"><small>约战时间</small><strong>{{ formatBattleTime(activity.startsAt) }}</strong></div>
        </div>
        <p v-if="activity.remark" class="battle-detail-remark">{{ activity.remark }}</p>

        <div class="battle-detail-summary">
          <div><small>阵容人数</small><strong>{{ filledSeats }} / {{ activity.totalSeats }}</strong></div>
          <div><small>空缺位置</small><strong>{{ activity.emptySeats }}</strong></div>
          <div><small>阵容版本</small><strong>{{ activity.snapshot ? 'v' + activity.snapshot.version : '未保存' }}</strong></div>
          <div><small>战报数据</small><strong>{{ activity.hasReport ? activity.reportIds.length + ' 份' : '暂无' }}</strong></div>
          <div v-if="shortageEntries.length" class="battle-detail-shortages"><small>职业缺口</small><span v-for="([name,count]) in shortageEntries" :key="name"><ProfessionTag :name="name"/>{{ count }}</span></div>
        </div>

        <div class="battle-detail-actions">
          <Button v-if="activity.canManage && activity.state !== 'ended'" @click="openLineup">配置排表</Button>
          <Button v-if="activity.canManage && activity.state !== 'ended' && !activity.isPublic && activity.snapshot" variant="outline" :disabled="busy" @click="requestChange('publish')">{{ busy ? '处理中…' : '发布公开' }}</Button>
          <Button v-if="activity.canManage" variant="outline" @click="importVisible=true">上传 CSV</Button>
          <Button v-if="activity.canManage && activity.state !== 'ended' && activity.snapshot" variant="destructive" :disabled="busy" @click="requestChange('end')">结束活动</Button>
        </div>
      </section>

      <section v-if="activity.canSignup" class="battle-panel battle-signup-bar">
        <span>报名角色</span>
        <Select v-model="profileId">
          <SelectTrigger class="battle-profile-select">
            <SelectValue placeholder="选择本人已绑定角色">
              <span v-if="selectedProfile" class="battle-profile-selected"><span>{{ selectedProfile.name }} · </span><ProfessionTag :name="selectedProfile.profession"/></span>
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem v-for="profile in profiles" :key="profile.memberId" :value="profile.memberId">
                <span>{{ profile.name }} · </span><ProfessionTag :name="profile.profession"/>
              </SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <span class="battle-muted">选择角色后，点击下方空缺位置报名。</span>
        <p v-if="profileError" class="battle-error">{{ profileError }}</p>
        <p v-else-if="!profiles.length" class="battle-muted">当前账号没有有效绑定角色，请先完善帮会成员资料。</p>
      </section>

      <section class="battle-detail-lineup">
        <div class="battle-section-heading">
          <div><h3>当前阵容</h3><span class="battle-muted">只展示最后一次成功保存的版本</span></div>
          <span v-if="activity.snapshot" class="battle-muted">保存于 {{ activity.snapshot.savedAt?.replace('T', ' ') }}</span>
        </div>
        <div class="battle-teams">
          <article v-for="team in activity.snapshot?.teams || []" :key="team.id" class="battle-team">
            <header><strong>{{ team.name }}</strong><span class="battle-muted">{{ teamFilled(team) }} / {{ teamSeats(team) }}</span></header>
            <section v-for="squad in team.squads" :key="squad.id" class="battle-squad">
              <header><strong>{{ squad.name }}</strong><span class="battle-muted">{{ squad.seats.filter(seat => seat.player).length }} / 6</span></header>
              <div class="battle-seats">
                <div v-for="seat in squad.seats" :key="seat.position" class="battle-seat" :class="{ 'battle-seat-empty': !seat.player }">
                  <small>位置 {{ seat.position }}</small>
                  <ProfessionTag :name="seat.requiredProfession"/>
                  <template v-if="seat.player">
                    <strong :title="seat.player.name">{{ seat.player.name }}{{ seat.player.isTemporary ? '（临时）' : '' }}</strong>
                    <ProfessionTag :name="seat.player.profession"/>
                    <Button v-if="activity.state === 'open' && profiles.some(profile => profile.memberId === seat.player.memberId)" variant="ghost" size="xs" :disabled="busy" @click="leave(seat.player.memberId)">请假</Button>
                  </template>
                  <template v-else>
                    <strong>空缺</strong>
                    <Button v-if="activity.canSignup" variant="link" size="xs" :disabled="busy || !profileId" @click="signup(squad.id, seat.position)">报名</Button>
                  </template>
                </div>
              </div>
            </section>
          </article>
        </div>
        <div v-if="!activity.snapshot" class="battle-empty-note" role="status">管理员尚未保存阵容</div>
      </section>

      <section class="battle-panel battle-detail-reports">
        <div class="battle-section-heading">
          <div><h3>战报数据</h3><span class="battle-muted">CSV 与当前约战直接关联</span></div>
        </div>
        <div v-if="activity.hasReport" class="battle-report-list">
          <div v-for="(id,index) in activity.reportIds" :key="id"><span>战报 {{ index + 1 }}</span><Button variant="link" size="sm" @click="reportDialog.open(id)">查看战报</Button></div>
        </div>
        <p v-else class="battle-empty-note">暂无战报数据。管理员可使用页面上方“上传 CSV”导入。</p>
      </section>
    </template>

    <ReportDialog ref="reportDialog"/>
    <BattleCsvImport v-model="importVisible" :activity="activity" @imported="load"/>
    <AlertDialog v-model:open="confirmVisible">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{{ confirmTitle }}</AlertDialogTitle>
          <AlertDialogDescription>{{ confirmDescription }}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction :variant="pendingChange === 'end' ? 'destructive' : 'default'" :disabled="busy" @click="confirmChange">{{ confirmActionText }}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { activityApi } from '@/api/activities'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import ProfessionTag from '@/components/ProfessionTag/index.vue'
import { loadGuildClassColors } from '@/utils/guildClassColor'
import ReportDialog from './ReportDialog.vue'
import BattleCsvImport from './BattleCsvImport.vue'
import { formatBattleTime } from './activityTime.mjs'
import './activity.css'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const profileError = ref('')
const activity = ref(null)
const profiles = ref([])
const profileId = ref('')
const reportDialog = ref(null)
const importVisible = ref(false)
const confirmVisible = ref(false)
const pendingChange = ref('')
const filledSeats = computed(() => Math.max(0, (activity.value?.totalSeats || 0) - (activity.value?.emptySeats || 0)))
const shortageEntries = computed(() => Object.entries(activity.value?.shortages || {}))
const selectedProfile = computed(() => profiles.value.find(profile => profile.memberId === profileId.value))
const statusText = computed(() => activity.value?.state === 'ended' ? '已结束' : activity.value?.isPublic ? '公开报名' : '组织内部')
const confirmTitle = computed(() => pendingChange.value === 'end' ? '确认结束活动' : '确认发布公开')
const confirmDescription = computed(() => pendingChange.value === 'end' ? '结束后阵容不能再修改，是否继续？' : '发布后所有已登录用户都可查看并按职业报名，是否继续？')
const confirmActionText = computed(() => pendingChange.value === 'end' ? '结束活动' : '发布公开')
const op = () => ({ expectedRevision: activity.value.revision, operationKey: crypto.randomUUID() })
let generation = 0

function teamSeats(team) { return team.squads.reduce((sum, squad) => sum + squad.seats.length, 0) }
function teamFilled(team) { return team.squads.reduce((sum, squad) => sum + squad.seats.filter(seat => seat.player).length, 0) }
function openLineup() { router.push({ path: '/guild/schedule', query: { activityId: activity.value.activityId } }) }

async function load() {
  loadGuildClassColors(true)
  const current = ++generation
  loading.value = true
  error.value = ''
  try {
    const next = await activityApi.activity(String(route.params.activityId))
    if (current !== generation) return
    activity.value = next
  } catch (loadError) {
    if (current === generation) { activity.value = null; error.value = loadError.message }
  } finally {
    if (current === generation) loading.value = false
  }
  try {
    profiles.value = await activityApi.activityProfiles()
    profileError.value = ''
    if (!profiles.value.some(profile => profile.memberId === profileId.value)) profileId.value = profiles.value[0]?.memberId || ''
  } catch (loadError) {
    profileError.value = loadError.message
    profiles.value = []
  }
}

async function action(fn) {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try { await fn(); await load() }
  catch (actionError) { error.value = actionError.message + '；请刷新确认状态后重试。' }
  finally { busy.value = false }
}

function signup(squadId, position) { return action(() => activityApi.signupSeat(activity.value.activityId, { ...op(), memberId: profileId.value, squadId, position })) }
function leave(memberId) { return action(() => activityApi.leaveSeat(activity.value.activityId, { ...op(), memberId })) }
function requestChange(kind) {
  pendingChange.value = kind
  confirmVisible.value = true
}
function confirmChange() {
  const kind = pendingChange.value
  confirmVisible.value = false
  pendingChange.value = ''
  return action(() => kind === 'end' ? activityApi.endActivity(activity.value.activityId, op()) : activityApi.publishActivity(activity.value.activityId, op()))
}

watch(() => route.params.activityId, load, { immediate: true })
</script>
