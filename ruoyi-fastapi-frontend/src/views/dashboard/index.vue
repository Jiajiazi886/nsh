<template>
  <div ref="pageRef" class="app-container guild-dashboard" v-loading="loading">
    <section class="signup-command" data-guild-motion="hero">
      <div class="command-main">
        <div class="section-kicker">
          <el-icon><Flag /></el-icon>
          <span>{{ scopeLabel }}</span>
        </div>
        <template v-if="activeInvite">
          <h1>约战报名人数</h1>
          <div class="invite-meta">
            <span>{{ activeInvite.guild_name || guildName || '当前帮会' }}</span>
            <span>{{ formatDateTime(activeInvite.battle_time) }}</span>
            <el-tag type="success" effect="light">当前生效链接</el-tag>
          </div>
          <div class="invite-actions">
            <el-button type="primary" :icon="DocumentCopy" @click="copyInviteLink">复制报名链接</el-button>
            <el-button :icon="Refresh" @click="fetchDashboard">刷新</el-button>
          </div>
        </template>
        <template v-else>
          <h1>当前没有生效报名链接</h1>
          <p class="empty-copy">创建新的约战报名链接后，这里会显示真实报名人数、职业分布和申请信息。</p>
          <el-button type="primary" :icon="Link" @click="goTo('/guild/review/battle')">创建报名链接</el-button>
        </template>
      </div>

      <div class="command-number">
        <span>已报名</span>
        <strong>{{ formatNumber(activeInvite?.registration_count) }}</strong>
        <small>包含待审核、已通过、已拒绝</small>
      </div>
    </section>

    <section class="signup-grid">
      <article class="panel signup-classes" data-guild-reveal>
        <div class="panel-head">
          <div>
            <span class="eyebrow">Signup Classes</span>
            <h2>报名职业人数</h2>
          </div>
          <span class="panel-note">{{ formatNumber(activeInvite?.registration_count) }} 人</span>
        </div>
        <div v-if="signupClasses.length" class="class-card-grid compact">
          <el-popover
            v-for="item in signupClasses"
            :key="item.class_name"
            placement="top"
            trigger="hover"
            :width="240"
            popper-class="guild-player-popover"
          >
            <template #reference>
              <div class="class-card signup-class-card">
                <span class="class-chip" :style="getGuildClassStyle(item.class_name)">{{ item.class_name }}</span>
                <strong>{{ formatNumber(item.count) }}</strong>
                <small>{{ item.percent || 0 }}%</small>
                <div class="class-meter">
                  <i :style="{ width: classWidth(item.percent), ...getGuildClassBarStyle(item.class_name) }"></i>
                </div>
              </div>
            </template>
            <div class="player-popover">
              <div class="popover-title">{{ item.class_name }} · {{ formatNumber(item.count) }} 人</div>
              <div v-if="item.players?.length" class="player-list">
                <span v-for="player in item.players" :key="player.registration_id">{{ player.player_name }}</span>
              </div>
              <span v-else class="muted-text">暂无报名玩家明细</span>
            </div>
          </el-popover>
        </div>
        <el-empty v-else description="当前链接还没有报名记录" :image-size="90" />
      </article>

      <article class="panel guild-classes" data-guild-reveal>
        <div class="panel-head">
          <div>
            <span class="eyebrow">Guild Roster</span>
            <h2>帮会主职分布</h2>
          </div>
          <span class="panel-note">悬浮卡片查看玩家</span>
        </div>
        <div v-if="guildClasses.length" class="class-card-grid">
          <el-popover
            v-for="item in guildClasses"
            :key="item.class_name"
            placement="top"
            trigger="hover"
            :width="260"
            popper-class="guild-player-popover"
          >
            <template #reference>
              <div class="class-card roster-card">
                <span class="class-chip" :style="getGuildClassStyle(item.class_name)">{{ item.class_name }}</span>
                <strong>{{ formatNumber(item.count) }}</strong>
                <small>{{ item.percent || 0 }}%</small>
                <div class="class-meter">
                  <i :style="{ width: classWidth(item.percent), ...getGuildClassBarStyle(item.class_name) }"></i>
                </div>
              </div>
            </template>
            <div class="player-popover">
              <div class="popover-title">{{ item.class_name }} · {{ formatNumber(item.count) }} 人</div>
              <div v-if="item.players?.length" class="player-list">
                <span v-for="player in item.players" :key="player.member_id">{{ player.player_name }}</span>
              </div>
              <span v-else class="muted-text">暂无玩家明细</span>
            </div>
          </el-popover>
        </div>
        <el-empty v-else description="当前帮会还没有可统计的主职成员" :image-size="90" />
      </article>
    </section>

    <section class="detail-grid">
      <article class="panel" data-guild-reveal>
        <div class="panel-head">
          <div>
            <span class="eyebrow">Battle Signup</span>
            <h2>约战审核</h2>
          </div>
          <el-button
            text
            type="primary"
            :icon="Check"
            :disabled="!pendingRegistrations.length"
            :loading="battleActionId === 'bulk'"
            @click="approveAllPendingRegistrations"
          >
            同意
          </el-button>
        </div>
        <div v-if="registrations.length" class="detail-list">
          <div v-for="item in registrations" :key="item.registration_id" class="detail-row">
            <div>
              <strong>{{ item.player_name }}</strong>
              <span>{{ item.applicant_name || '未填写称呼' }} · {{ formatDateTime(item.apply_time) }}</span>
            </div>
            <span class="class-chip" :style="getGuildClassStyle(item.player_class)">{{ item.player_class || '未设置' }}</span>
            <el-tag :type="reviewTagType(item.approval_status)" effect="light">
              {{ reviewStatusLabel(item.approval_status) }}
            </el-tag>
            <div v-if="item.approval_status === '0'" class="row-actions">
              <el-button
                link
                type="primary"
                :loading="battleActionId === `approve-${item.registration_id}`"
                @click="reviewBattleRegistration(item, 'approve')"
              >
                同意
              </el-button>
              <el-button
                link
                type="danger"
                :loading="battleActionId === `reject-${item.registration_id}`"
                @click="reviewBattleRegistration(item, 'reject')"
              >
                拒绝
              </el-button>
            </div>
          </div>
        </div>
        <el-empty v-else description="当前链接暂无报名明细" :image-size="90" />
      </article>

      <article class="panel" data-guild-reveal>
        <div class="panel-head">
          <div>
            <span class="eyebrow">Join Review</span>
            <h2>入帮申请</h2>
          </div>
          <div class="panel-head-actions">
            <div class="stacked-count">
              <strong>{{ formatNumber(activeInvite?.pending_join_count ?? reviewSummary.pending_join_count) }}</strong>
              <span>待审核</span>
            </div>
            <el-button
              text
              type="primary"
              :icon="Check"
              :disabled="!pendingJoinApplications.length"
              :loading="joinActionId === 'bulk'"
              @click="approveAllPendingJoinApplications"
            >
              同意
            </el-button>
          </div>
        </div>
        <div v-if="joinApplications.length" class="detail-list">
          <div v-for="item in joinApplications" :key="item.application_id" class="detail-row application-row">
            <div>
              <strong>{{ item.player_name }}</strong>
              <span>{{ item.guild_name || activeInvite?.guild_name || '当前帮会' }} · {{ formatDateTime(item.apply_time) }}</span>
            </div>
            <span class="class-chip" :style="getGuildClassStyle(item.player_class)">{{ item.player_class || '未设置' }}</span>
            <el-tag :type="reviewTagType(item.review_status)" effect="light">
              {{ reviewStatusLabel(item.review_status) }}
            </el-tag>
            <div v-if="item.review_status === '0'" class="row-actions">
              <el-button
                link
                type="primary"
                :loading="joinActionId === `approve-${item.application_id}`"
                @click="reviewJoinApplication(item, 'approve')"
              >
                同意
              </el-button>
              <el-button
                link
                type="danger"
                :loading="joinActionId === `reject-${item.application_id}`"
                @click="reviewJoinApplication(item, 'reject')"
              >
                拒绝
              </el-button>
            </div>
          </div>
        </div>
        <el-empty v-else description="当前帮会暂无入帮申请" :image-size="90" />
      </article>
    </section>

    <section class="ops-grid">
      <article class="metric-card" data-guild-reveal>
        <div class="metric-icon green"><el-icon><UserFilled /></el-icon></div>
        <div>
          <span>活跃成员</span>
          <strong>{{ formatNumber(memberSummary.active_count) }}</strong>
          <small>成员总数 {{ formatNumber(memberSummary.total_count) }}</small>
        </div>
      </article>
      <article class="metric-card" data-guild-reveal>
        <div class="metric-icon amber"><el-icon><Bell /></el-icon></div>
        <div>
          <span>入帮待审</span>
          <strong>{{ formatNumber(reviewSummary.pending_join_count) }}</strong>
          <small>当前权限范围</small>
        </div>
      </article>
      <article class="metric-card" data-guild-reveal>
        <div class="metric-icon red"><el-icon><Tickets /></el-icon></div>
        <div>
          <span>报名待审</span>
          <strong>{{ formatNumber(reviewSummary.pending_battle_registration_count) }}</strong>
          <small>约战报名审核</small>
        </div>
      </article>
      <article class="metric-card" data-guild-reveal>
        <div class="metric-icon blue"><el-icon><Grid /></el-icon></div>
        <div>
          <span>当前排表</span>
          <strong>{{ formatNumber(scheduleSummary.assignment_count || scheduleSummary.total_assignment_count) }}</strong>
          <small>{{ scheduleLabel }}</small>
        </div>
      </article>
    </section>

    <section class="detail-grid history-grid">
      <article class="panel" data-guild-reveal>
        <div class="panel-head">
          <div>
            <span class="eyebrow">Recent Battle</span>
            <h2>最近复盘</h2>
          </div>
          <el-button text type="primary" :icon="Right" @click="goTo('/guild/battle/list')">历史</el-button>
        </div>
        <div v-if="latestBattle" class="battle-line">
          <div class="battle-date">
            <strong>{{ battleDay(latestBattle) }}</strong>
            <span>{{ battleMonth(latestBattle) }}</span>
          </div>
          <div>
            <strong>{{ latestBattle.battle_name || '未命名约战' }}</strong>
            <span>{{ latestBattle.my_guild_name || guildName || '己方帮会' }} vs {{ latestBattle.opponent_name || '未记录对手' }}</span>
          </div>
          <el-tag :type="resultTagType(latestBattle.battle_result)" effect="light">
            {{ latestBattle.battle_result || statusLabel(latestBattle.status) }}
          </el-tag>
        </div>
        <el-empty v-else description="当前范围暂无约战复盘" :image-size="90" />
      </article>

      <article class="panel" data-guild-reveal>
        <div class="panel-head">
          <div>
            <span class="eyebrow">Battle Review</span>
            <h2>复盘指标</h2>
          </div>
          <span class="panel-note">胜率 {{ battleSummary.win_rate || 0 }}%</span>
        </div>
        <div v-if="battleRecordSummary" class="record-metrics">
          <div v-for="item in recordMetricItems" :key="item.key" class="record-metric">
            <span>{{ item.label }}</span>
            <strong>{{ formatCompactNumber(item.value) }}</strong>
          </div>
        </div>
        <el-empty v-else description="最近约战还没有复盘明细" :image-size="90" />
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Bell,
  Check,
  DocumentCopy,
  Flag,
  Grid,
  Link,
  Refresh,
  Right,
  Tickets,
  UserFilled
} from '@element-plus/icons-vue'
import { getGuildDashboardSummary } from '@/api/guild/dashboard'
import { approveBattleRegistration, rejectBattleRegistration } from '@/api/guild/battle'
import { approveJoinApplication, rejectJoinApplication } from '@/api/guild/join'
import useGuildMemberStore from '@/store/modules/guildMember'
import useUserStore from '@/store/modules/user'
import { useGuildClassColors } from '@/utils/guildClassColor'
import { useGuildPageMotion } from '@/composables/useGuildPageMotion'

defineOptions({
  name: 'DashBoard'
})

const router = useRouter()
const guildMemberStore = useGuildMemberStore()
const userStore = useUserStore()
const pageRef = ref(null)
const loading = ref(false)
const battleActionId = ref('')
const joinActionId = ref('')
const dashboard = ref({})
const { getGuildClassBarStyle, getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()

useGuildPageMotion(pageRef)

const scope = computed(() => dashboard.value.scope || {})
const scopeLabel = computed(() => scope.value.label || '当前数据')
const guild = computed(() => dashboard.value.guild || {})
const guildName = computed(() => guild.value.guild_name || '')
const activeInvite = computed(() => dashboard.value.active_invite_summary || null)
const signupClasses = computed(() => activeInvite.value?.registration_class_distribution || [])
const cachedGuildClasses = computed(() => buildClassDistributionFromMembers(guildMemberStore.members))
const guildClasses = computed(() => {
  if (scope.value.type === 'common' && guildMemberStore.hasReadyCache && cachedGuildClasses.value.length) {
    return cachedGuildClasses.value
  }
  return activeInvite.value?.guild_class_distribution || dashboard.value.class_distribution || []
})
const registrations = computed(() => activeInvite.value?.registrations || [])
const pendingRegistrations = computed(() => registrations.value.filter(item => item.approval_status === '0'))
const joinApplications = computed(() => activeInvite.value?.join_applications || [])
const pendingJoinApplications = computed(() => joinApplications.value.filter(item => item.review_status === '0'))
const battleSummary = computed(() => dashboard.value.battle_summary || {})
const latestBattles = computed(() => dashboard.value.latest_battles || [])
const latestBattle = computed(() => latestBattles.value[0] || null)
const battleRecordSummary = computed(() => latestBattle.value?.my_guild_summary || dashboard.value.latest_battle_record_summary || null)
const memberSummary = computed(() => dashboard.value.member_summary || {})
const reviewSummary = computed(() => dashboard.value.review_summary || {})
const scheduleSummary = computed(() => dashboard.value.schedule_summary || {})

const scheduleLabel = computed(() => {
  if (!scheduleSummary.value.schedule_id) return '暂无启用排表'
  return `${scheduleSummary.value.team_count || 0} 队 / ${scheduleSummary.value.squad_count || 0} 小队`
})

const recordMetricItems = computed(() => {
  const record = battleRecordSummary.value || {}
  return [
    { key: 'participants', label: '参战', value: record.participants },
    { key: 'kills', label: '击杀', value: record.kills },
    { key: 'assists', label: '助攻', value: record.assists },
    { key: 'damage', label: '伤害', value: record.damage },
    { key: 'healing', label: '治疗', value: record.healing },
    { key: 'deaths', label: '死亡', value: record.deaths }
  ]
})

async function fetchDashboard() {
  loading.value = true
  try {
    const res = await getGuildDashboardSummary()
    dashboard.value = res.data || {}
  } finally {
    loading.value = false
  }
}

function warmGuildMemberCache() {
  if (guildMemberStore.hasReadyCache) return
  guildMemberStore.preloadAfterLogin(userStore.permissions)
}

function buildClassDistributionFromMembers(members = []) {
  const grouped = new Map()
  members.forEach(member => {
    const className = (member.player_class || '').trim()
    if (!className) return
    const group = grouped.get(className) || {
      class_name: className,
      count: 0,
      percent: 0,
      players: []
    }
    group.count += 1
    group.players.push({
      member_id: member.member_id,
      player_name: member.player_name,
      player_class: member.player_class || '',
      secondary_class: member.secondary_class || '',
      role_in_guild: member.role_in_guild || ''
    })
    grouped.set(className, group)
  })
  const total = Array.from(grouped.values()).reduce((sum, item) => sum + item.count, 0)
  return Array.from(grouped.values())
    .map(item => ({
      ...item,
      percent: total ? Math.round((item.count / total) * 1000) / 10 : 0
    }))
    .sort((a, b) => b.count - a.count || a.class_name.localeCompare(b.class_name, 'zh-CN'))
}

function goTo(path) {
  router.push(path)
}

async function copyInviteLink() {
  if (!activeInvite.value?.public_path) return
  await navigator.clipboard.writeText(`${window.location.origin}${activeInvite.value.public_path}`)
  ElMessage.success('报名链接已复制')
}

async function reviewBattleRegistration(item, type) {
  const isApprove = type === 'approve'
  battleActionId.value = `${type}-${item.registration_id}`
  try {
    if (isApprove) {
      await approveBattleRegistration(item.registration_id)
      ElMessage.success(`${item.player_name} 已同意`)
    } else {
      await rejectBattleRegistration(item.registration_id)
      ElMessage.success(`${item.player_name} 已拒绝`)
    }
    await fetchDashboard()
  } finally {
    battleActionId.value = ''
  }
}

async function approveAllPendingRegistrations() {
  if (!pendingRegistrations.value.length) return
  battleActionId.value = 'bulk'
  try {
    await Promise.all(pendingRegistrations.value.map(item => approveBattleRegistration(item.registration_id)))
    ElMessage.success(`已同意 ${pendingRegistrations.value.length} 条约战报名`)
    await fetchDashboard()
  } finally {
    battleActionId.value = ''
  }
}

async function approveAllPendingJoinApplications() {
  if (!pendingJoinApplications.value.length) return
  joinActionId.value = 'bulk'
  try {
    await Promise.all(pendingJoinApplications.value.map(item => approveJoinApplication(item.application_id)))
    ElMessage.success(`已同意 ${pendingJoinApplications.value.length} 条入帮申请`)
    await fetchDashboard()
    window.dispatchEvent(new Event('guild-member-data-changed'))
  } finally {
    joinActionId.value = ''
  }
}

async function reviewJoinApplication(item, type) {
  const isApprove = type === 'approve'
  joinActionId.value = `${type}-${item.application_id}`
  try {
    if (isApprove) {
      await approveJoinApplication(item.application_id)
      ElMessage.success(`${item.player_name} 已同意入帮`)
    } else {
      await rejectJoinApplication(item.application_id)
      ElMessage.success(`${item.player_name} 已拒绝入帮`)
    }
    await fetchDashboard()
    window.dispatchEvent(new Event('guild-member-data-changed'))
  } finally {
    joinActionId.value = ''
  }
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

function formatCompactNumber(value) {
  const number = Number(value || 0)
  if (number >= 100000000) return `${(number / 100000000).toFixed(1)}亿`
  if (number >= 10000) return `${(number / 10000).toFixed(1)}万`
  return formatNumber(number)
}

function normalizeDate(value) {
  if (!value) return null
  if (/^\d{8}$/.test(String(value))) {
    const raw = String(value)
    return new Date(`${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}T00:00:00`)
  }
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatDateTime(value) {
  const date = normalizeDate(value)
  if (!date) return '未记录时间'
  return date.toLocaleString('zh-CN', { hour12: false })
}

function battleDay(battle) {
  const date = normalizeDate(battle.battle_time || battle.battle_date || battle.create_time)
  return date ? String(date.getDate()).padStart(2, '0') : '--'
}

function battleMonth(battle) {
  const date = normalizeDate(battle.battle_time || battle.battle_date || battle.create_time)
  return date ? `${date.getMonth() + 1}月` : '未知'
}

function statusLabel(status) {
  return { 0: '待开始', 1: '进行中', 2: '已完成' }[String(status)] || '未记录'
}

function resultTagType(result) {
  if (!result) return 'info'
  if (String(result).includes('胜')) return 'success'
  if (String(result).includes('负') || String(result).includes('败')) return 'danger'
  return 'warning'
}

function reviewStatusLabel(status) {
  return { 0: '待审核', 1: '已通过', 2: '已拒绝' }[String(status)] || '未记录'
}

function reviewTagType(status) {
  return { 0: 'warning', 1: 'success', 2: 'danger' }[String(status)] || 'info'
}

function classWidth(percent) {
  const value = Number(percent || 0)
  if (!value) return '0%'
  return `${Math.max(7, value)}%`
}

onMounted(() => {
  warmGuildMemberCache()
  fetchDashboard()
  loadGuildClassColors()
})
</script>

<style scoped lang="scss">
.guild-dashboard {
  display: flex;
  flex-direction: column;
  gap: 18px;
  color: #172033;
  background:
    linear-gradient(180deg, rgba(250, 252, 255, 0.97), rgba(244, 248, 250, 0.97)),
    repeating-linear-gradient(90deg, rgba(23, 32, 51, 0.025) 0, rgba(23, 32, 51, 0.025) 1px, transparent 1px, transparent 84px);
}

.signup-command,
.panel,
.metric-card {
  border: 1px solid rgba(23, 32, 51, 0.09);
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(250, 252, 253, 0.9));
  box-shadow: 0 18px 42px rgba(23, 32, 51, 0.08);
}

.signup-command {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 22px;
  min-height: 220px;
  padding: 30px;
  overflow: hidden;
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.96), rgba(247, 251, 249, 0.92)),
    linear-gradient(90deg, rgba(47, 111, 99, 0.08), rgba(232, 215, 84, 0.08));
}

.command-main {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.section-kicker,
.eyebrow {
  color: #2f6f63;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0;
  text-transform: uppercase;
}

.section-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.command-main h1 {
  margin: 14px 0 12px;
  color: #121826;
  font-size: 36px;
  line-height: 1.14;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.empty-copy {
  max-width: 620px;
  margin: 0 0 18px;
  color: #64748b;
  font-size: 15px;
  line-height: 1.8;
}

.invite-meta,
.invite-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
}

.invite-meta {
  color: #5f6f86;
  font-weight: 700;
}

.invite-actions {
  margin-top: 20px;
}

.command-number {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  padding: 22px;
  border-radius: 13px;
  background:
    linear-gradient(135deg, #11261f, #1e473d),
    #11261f;
  color: #e8fff5;
}

.command-number span,
.command-number small,
.metric-card span,
.metric-card small {
  display: block;
}

.command-number strong {
  display: block;
  margin-top: 8px;
  font-size: 56px;
  line-height: 1;
}

.command-number small {
  margin-top: 12px;
  color: rgba(232, 255, 245, 0.72);
}

.signup-grid,
.detail-grid,
.history-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(420px, 1.1fr);
  align-items: start;
  gap: 18px;
}

.detail-grid {
  grid-template-columns: minmax(0, 1fr) minmax(380px, 0.9fr);
}

.panel {
  min-width: 0;
  padding: 22px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.panel-head-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.panel-head h2 {
  margin: 5px 0 0;
  color: #121826;
  font-size: 20px;
  line-height: 1.25;
}

.panel-note,
.muted-text,
.detail-row span,
.battle-line span,
.metric-card span,
.metric-card small {
  color: #64748b;
  font-size: 13px;
}

.class-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 12px;
}

.class-card-grid.compact {
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
}

.class-card {
  min-height: 112px;
  padding: 14px;
  border: 1px solid rgba(23, 32, 51, 0.08);
  border-radius: 12px;
  background: #fbfcfd;
  transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
}

.class-card:hover {
  border-color: rgba(47, 111, 99, 0.28);
  box-shadow: 0 14px 28px rgba(23, 32, 51, 0.09);
  transform: translate3d(0, -2px, 0);
}

.class-chip {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  min-height: 24px;
  padding: 3px 9px;
  border: 1px solid rgba(23, 32, 51, 0.12);
  border-radius: 999px;
  background: #eef5f1;
  color: #25443b;
  font-size: 12px;
  font-weight: 800;
}

.class-card strong {
  display: block;
  margin-top: 12px;
  color: #121826;
  font-size: 28px;
  line-height: 1;
}

.class-card small {
  display: block;
  margin-top: 6px;
  color: #64748b;
}

.class-meter {
  height: 8px;
  margin-top: 14px;
  overflow: hidden;
  border-radius: 999px;
  background: #e9eef2;
}

.class-meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2f6f63, #7bb99f);
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 12px;
  min-height: 64px;
  padding: 12px;
  border: 1px solid rgba(23, 32, 51, 0.07);
  border-radius: 12px;
  background: #fbfcfd;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  white-space: nowrap;
}

.detail-row strong,
.battle-line strong {
  display: block;
  color: #121826;
  overflow-wrap: anywhere;
}

.stacked-count {
  display: grid;
  justify-items: end;
  line-height: 1.1;
}

.stacked-count strong {
  color: #121826;
  font-size: 24px;
}

.ops-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-card {
  display: flex;
  gap: 14px;
  align-items: center;
  min-height: 112px;
  padding: 18px;
}

.metric-card strong {
  display: block;
  margin: 5px 0;
  color: #121826;
  font-size: 28px;
  line-height: 1.1;
}

.metric-icon {
  display: grid;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 12px;
  font-size: 20px;
}

.metric-icon.green {
  background: #e4f5ee;
  color: #23765e;
}

.metric-icon.amber {
  background: #fff4d7;
  color: #9a6a00;
}

.metric-icon.red {
  background: #ffe8e2;
  color: #b94d32;
}

.metric-icon.blue {
  background: #e7f0ff;
  color: #2d5caa;
}

.battle-line {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  min-height: 76px;
  padding: 12px;
  border: 1px solid rgba(23, 32, 51, 0.07);
  border-radius: 12px;
  background: #fbfcfd;
}

.battle-date {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 12px;
  background: #11261f;
  color: #f5fff9;
}

.battle-date strong {
  font-size: 18px;
  line-height: 1;
}

.battle-date span {
  color: rgba(245, 255, 249, 0.72);
  font-size: 12px;
}

.record-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.record-metric {
  min-height: 82px;
  padding: 14px;
  border-radius: 12px;
  background: #f4f8f7;
}

.record-metric span {
  color: #64748b;
  font-size: 13px;
}

.record-metric strong {
  display: block;
  margin-top: 10px;
  color: #121826;
  font-size: 24px;
  line-height: 1.1;
}

.player-popover {
  display: grid;
  gap: 10px;
}

.popover-title {
  color: #121826;
  font-weight: 800;
}

.player-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.player-list span {
  padding: 4px 8px;
  border-radius: 999px;
  background: #f2f5f7;
  color: #334155;
  font-size: 12px;
}

@media (max-width: 1180px) {
  .signup-command,
  .signup-grid,
  .detail-grid,
  .history-grid,
  .ops-grid {
    grid-template-columns: 1fr;
  }

  .ops-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .signup-command,
  .panel {
    padding: 18px;
  }

  .command-main h1 {
    font-size: 28px;
  }

  .command-number strong {
    font-size: 42px;
  }

  .detail-row,
  .battle-line {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .record-metrics,
  .ops-grid {
    grid-template-columns: 1fr;
  }
}
</style>
