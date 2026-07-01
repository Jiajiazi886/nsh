<template>
  <div ref="pageRef" class="app-container guild-dashboard" v-loading="pageLoading">
    <template v-if="isMemberDashboard">
      <section class="member-command" data-guild-motion="hero">
        <div class="member-command-main">
          <div class="section-kicker">
            <el-icon><Flag /></el-icon>
            <span>个人养成台</span>
          </div>
          <h1>{{ memberHeroTitle }}</h1>
          <div class="member-meta">
            <span>{{ memberGuildText }}</span>
            <span>{{ memberClassText }}</span>
            <el-tag :type="vipTagType" effect="light">{{ vipStatusLabel }}</el-tag>
          </div>
          <div class="invite-actions">
            <el-button type="primary" :icon="Grid" @click="goTo('/personal/skill')">内功管理</el-button>
            <el-button :icon="Tickets" @click="goToSkillAction('recognize')">图片识别</el-button>
            <el-button :icon="Refresh" @click="refreshMemberDashboard">刷新</el-button>
          </div>
        </div>

        <div class="member-ai-panel">
          <span>AI识图次数</span>
          <strong>{{ aiRecognitionTotalText }}</strong>
          <small>VIP {{ formatNumber(userStore.vipAiImageRecognitionCount) }} / 普通 {{ formatNumber(userStore.aiImageRecognitionCount) }}</small>
        </div>
      </section>

      <section class="member-metric-grid">
        <article class="metric-card member-metric" data-guild-reveal>
          <div class="metric-icon green"><el-icon><Grid /></el-icon></div>
          <div>
            <span>内功数量</span>
            <strong>{{ powerQuotaText }}</strong>
            <el-progress
              class="member-progress"
              :percentage="powerQuotaPercent"
              :show-text="false"
              :stroke-width="7"
            />
          </div>
        </article>
        <article class="metric-card member-metric" data-guild-reveal>
          <div class="metric-icon amber"><el-icon><Flag /></el-icon></div>
          <div>
            <span>最高总增益</span>
            <strong>{{ bestPowerBonusText }}</strong>
            <small>{{ bestPower?.name || '暂无内功' }}</small>
          </div>
        </article>
        <article class="metric-card member-metric" data-guild-reveal>
          <div class="metric-icon blue"><el-icon><UserFilled /></el-icon></div>
          <div>
            <span>灵韵内功</span>
            <strong>{{ formatNumber(lingyunPowerCount) }}</strong>
            <small>已启用灵韵勾选</small>
          </div>
        </article>
        <article class="metric-card member-metric" data-guild-reveal>
          <div class="metric-icon red"><el-icon><Bell /></el-icon></div>
          <div>
            <span>识别记录</span>
            <strong>{{ formatNumber(recognitionHistory.length) }}</strong>
            <small>{{ recognitionSummaryText }}</small>
          </div>
        </article>
      </section>

      <section class="member-content-grid">
        <article class="panel" data-guild-reveal>
          <div class="panel-head">
            <div>
              <span class="eyebrow">Internal Power</span>
              <h2>最近内功</h2>
            </div>
            <el-button text type="primary" :icon="Right" @click="goTo('/personal/skill')">查看全部</el-button>
          </div>
          <div v-if="recentPowers.length" class="member-power-list">
            <div v-for="power in recentPowers" :key="power.id || power.powerId" class="member-power-row">
              <div>
                <strong>{{ power.name || '未命名内功' }}</strong>
                <span>{{ power.category || '未设置种类' }} · {{ formatDateTime(power.updatedAt) }}</span>
              </div>
              <el-tag effect="light">{{ formatPercent(power.totalBonusPercent) }}</el-tag>
            </div>
          </div>
          <el-empty v-else description="还没有保存内功" :image-size="86">
            <el-button type="primary" @click="goToSkillAction('create')">新增内功</el-button>
          </el-empty>
        </article>

        <article class="panel" data-guild-reveal>
          <div class="panel-head">
            <div>
              <span class="eyebrow">Recognition</span>
              <h2>识别记录</h2>
            </div>
            <el-button text type="primary" :icon="Right" @click="goToSkillAction('history')">打开记录</el-button>
          </div>
          <div v-if="recentRecognition.length" class="member-recognition-list">
            <div v-for="item in recentRecognition" :key="item.recordId" class="member-recognition-row">
              <div>
                <strong>{{ item.fileName || '剪贴板图片' }}</strong>
                <span>{{ formatDateTime(item.updateTime || item.createTime) }}</span>
              </div>
              <el-tag :type="recognitionStatusTagType(item.status)" effect="light">
                {{ recognitionStatusLabel(item.status) }}
              </el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无识别记录" :image-size="86">
            <el-button @click="goToSkillAction('recognize')">去识别图片</el-button>
          </el-empty>
        </article>
      </section>

      <section class="member-content-grid">
        <article class="panel" data-guild-reveal>
          <div class="panel-head">
            <div>
              <span class="eyebrow">Guild Status</span>
              <h2>我的帮会状态</h2>
            </div>
            <el-button text type="primary" :icon="Right" @click="goTo(memberProfile ? '/personal/profile-edit' : '/personal/join')">
              {{ memberProfile ? '编辑资料' : '加入帮会' }}
            </el-button>
          </div>
          <div class="member-status-list">
            <div class="member-status-row">
              <span>当前帮会</span>
              <strong>{{ memberGuildText }}</strong>
            </div>
            <div class="member-status-row">
              <span>当前报名</span>
              <strong>{{ activeInvite ? activeInvite.battle_name || '当前约战' : '暂无生效报名' }}</strong>
            </div>
            <div class="member-status-row">
              <span>我的排表</span>
              <strong>{{ memberScheduleText }}</strong>
            </div>
            <div class="member-status-row">
              <span>申请状态</span>
              <strong>{{ memberApplicationText }}</strong>
            </div>
          </div>
        </article>

        <article class="panel" data-guild-reveal>
          <div class="panel-head">
            <div>
              <span class="eyebrow">Quick Actions</span>
              <h2>常用入口</h2>
            </div>
          </div>
          <div class="member-action-grid">
            <el-button type="primary" :icon="Grid" @click="goTo('/personal/skill')">内功管理</el-button>
            <el-button :icon="Tickets" @click="goToSkillAction('recognize')">图片识别</el-button>
            <el-button :icon="Bell" @click="goToSkillAction('history')">识别记录</el-button>
            <el-button :icon="UserFilled" @click="goTo('/personal/profile-edit')">个人信息</el-button>
            <el-button :icon="Link" @click="goTo('/personal/join')">加入帮会</el-button>
          </div>
        </article>
      </section>
    </template>

    <template v-else>
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
            <span>{{ formatDateTimeWithWeek(activeInvite.battle_time) }}</span>
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
        <div class="command-stat">
          <span>已报名</span>
          <strong>{{ formatNumber(activeInvite?.registration_count) }}</strong>
        </div>
        <div class="command-stat">
          <span>已请假</span>
          <strong>{{ formatNumber(activeInvite?.leave_count) }}</strong>
        </div>
        <small>包含待审核、已通过、已拒绝，已取消不计入</small>
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
        <div class="battle-class-stack">
          <div class="battle-class-block">
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
                  <div class="class-card signup-class-card" :style="getGuildClassTokenStyle(item.class_name)">
                    <span class="class-chip">{{ item.class_name }}</span>
                    <strong>{{ formatNumber(item.count) }}</strong>
                    <small>{{ item.percent || 0 }}%</small>
                    <div class="class-meter">
                      <i :style="{ width: classWidth(item.percent) }"></i>
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
            <el-empty v-else description="当前链接还没有报名记录" :image-size="64" />
          </div>

          <div class="battle-class-block leave-block">
            <div class="panel-subhead">
              <div>
                <span class="eyebrow">Leave Classes</span>
                <h2>请假职业人数</h2>
              </div>
              <span class="panel-note">{{ formatNumber(activeInvite?.leave_count) }} 人</span>
            </div>
            <div v-if="leaveClasses.length" class="class-card-grid compact">
              <el-popover
                v-for="item in leaveClasses"
                :key="item.class_name"
                placement="top"
                trigger="hover"
                :width="240"
                popper-class="guild-player-popover"
              >
                <template #reference>
                  <div class="class-card leave-class-card" :style="getGuildClassTokenStyle(item.class_name)">
                    <span class="class-chip">{{ item.class_name }}</span>
                    <strong>{{ formatNumber(item.count) }}</strong>
                    <small>{{ item.percent || 0 }}%</small>
                    <div class="class-meter">
                      <i :style="{ width: classWidth(item.percent) }"></i>
                    </div>
                  </div>
                </template>
                <div class="player-popover">
                  <div class="popover-title">{{ item.class_name }} · {{ formatNumber(item.count) }} 人请假</div>
                  <div v-if="item.players?.length" class="player-list">
                    <span v-for="player in item.players" :key="player.registration_id">{{ player.player_name }}</span>
                  </div>
                  <span v-else class="muted-text">暂无请假玩家明细</span>
                </div>
              </el-popover>
            </div>
            <el-empty v-else description="当前链接还没有请假记录" :image-size="64" />
          </div>
        </div>
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
              <div class="class-card roster-card" :style="getGuildClassTokenStyle(item.class_name)">
                <span class="class-chip">{{ item.class_name }}</span>
                <strong>{{ formatNumber(item.count) }}</strong>
                <small>{{ item.percent || 0 }}%</small>
                <div class="class-meter">
                  <i :style="{ width: classWidth(item.percent) }"></i>
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
            <span class="class-chip" :style="getGuildClassTokenStyle(item.player_class)">{{ item.player_class || '未设置' }}</span>
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
            <span class="class-chip" :style="getGuildClassTokenStyle(item.player_class)">{{ item.player_class || '未设置' }}</span>
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
    </template>
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
import { listInternalPowers, listInternalPowerRecognitionHistory } from '@/api/personal/internalPower'
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
const memberLoading = ref(false)
const memberPowers = ref([])
const memberQuota = ref({ count: 0, maxCount: 20, unlimited: false })
const recognitionHistory = ref([])
const { getGuildClassTokenStyle, loadGuildClassColors } = useGuildClassColors()

useGuildPageMotion(pageRef)

const scope = computed(() => dashboard.value.scope || {})
const isMemberDashboard = computed(() => scope.value.type === 'user')
const pageLoading = computed(() => loading.value || (isMemberDashboard.value && memberLoading.value))
const scopeLabel = computed(() => scope.value.label || '当前数据')
const guild = computed(() => dashboard.value.guild || {})
const guildName = computed(() => guild.value.guild_name || '')
const memberProfile = computed(() => guild.value.membership || null)
const memberHeroTitle = computed(() => {
  if (memberProfile.value?.player_name) return `${memberProfile.value.player_name}的个人养成台`
  return '先加入帮会，开始养成记录'
})
const memberGuildText = computed(() => guildName.value || '暂未加入帮会')
const memberClassText = computed(() => {
  const mainClass = memberProfile.value?.player_class || '未设置主职'
  const secondaryClass = memberProfile.value?.secondary_class || '未设置副职'
  return `${mainClass} / ${secondaryClass}`
})
const vipStatusLabel = computed(() => {
  if (userStore.effectiveVipType === 'sponsored') return '赞助VIP'
  if (userStore.effectiveVipType === 'manual' || userStore.isVipEffective) return 'VIP'
  return '普通用户'
})
const vipTagType = computed(() => vipStatusLabel.value === '普通用户' ? 'info' : 'success')
const aiRecognitionTotalText = computed(() => {
  const total = Number(userStore.aiImageRecognitionCount || 0) + Number(userStore.vipAiImageRecognitionCount || 0)
  return formatNumber(total)
})
const activeInvite = computed(() => dashboard.value.active_invite_summary || null)
const signupClasses = computed(() => activeInvite.value?.registration_class_distribution || [])
const leaveClasses = computed(() => activeInvite.value?.leave_class_distribution || [])
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
const memberApplications = computed(() => reviewSummary.value.my_applications || [])
const latestMemberApplication = computed(() => memberApplications.value[0] || null)
const memberApplicationText = computed(() => {
  if (memberProfile.value) return '已加入帮会'
  if (!latestMemberApplication.value) return '暂无申请'
  return reviewStatusLabel(latestMemberApplication.value.review_status)
})
const memberScheduleText = computed(() => {
  const assignment = scheduleSummary.value.my_assignment
  if (!assignment) return '暂无排表'
  return [assignment.team_name, assignment.squad_name].filter(Boolean).join(' / ') || '已分配'
})
const powerCount = computed(() => Number(memberQuota.value.count ?? memberPowers.value.length))
const powerMaxCount = computed(() => Number(memberQuota.value.maxCount || 20))
const powerQuotaText = computed(() => {
  if (memberQuota.value.unlimited) return `${formatNumber(powerCount.value)} / 不限`
  return `${formatNumber(powerCount.value)} / ${formatNumber(powerMaxCount.value)}`
})
const powerQuotaPercent = computed(() => {
  if (memberQuota.value.unlimited) return 100
  if (!powerMaxCount.value) return 0
  return Math.min(100, Math.round((powerCount.value / powerMaxCount.value) * 100))
})
const sortedPowers = computed(() => {
  return [...memberPowers.value].sort((a, b) => getPowerScore(b) - getPowerScore(a))
})
const bestPower = computed(() => sortedPowers.value[0] || null)
const bestPowerBonusText = computed(() => bestPower.value ? formatPercent(bestPower.value.totalBonusPercent) : '0.00000%')
const lingyunPowerCount = computed(() => memberPowers.value.filter(item => item.lingyunEnabled).length)
const recentPowers = computed(() => {
  return [...memberPowers.value]
    .sort((a, b) => new Date(b.updatedAt || b.updateTime || 0).getTime() - new Date(a.updatedAt || a.updateTime || 0).getTime())
    .slice(0, 5)
})
const recentRecognition = computed(() => recognitionHistory.value.slice(0, 4))
const recognitionSummaryText = computed(() => {
  const failed = recognitionHistory.value.filter(item => item.status === 'failed').length
  if (failed) return `${failed} 条失败需查看`
  const saved = recognitionHistory.value.filter(item => item.savedPowerId).length
  return saved ? `${saved} 条已新增` : '最近50条'
})

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
    if (dashboard.value.scope?.type === 'user') {
      await fetchMemberCultivationData()
    }
  } finally {
    loading.value = false
  }
}

async function fetchMemberCultivationData() {
  memberLoading.value = true
  try {
    const [powerResult, historyResult] = await Promise.allSettled([
      listInternalPowers(),
      listInternalPowerRecognitionHistory()
    ])

    if (powerResult.status === 'fulfilled') {
      const response = powerResult.value || {}
      memberPowers.value = (response.powers || response.data?.powers || []).map(normalizeMemberPower)
      memberQuota.value = {
        count: response.quota?.count ?? response.data?.quota?.count ?? memberPowers.value.length,
        maxCount: response.quota?.maxCount ?? response.data?.quota?.maxCount ?? 20,
        unlimited: !!(response.quota?.unlimited ?? response.data?.quota?.unlimited)
      }
    }

    if (historyResult.status === 'fulfilled') {
      const response = historyResult.value || {}
      recognitionHistory.value = response.items || response.data?.items || []
    }
  } finally {
    memberLoading.value = false
  }
}

async function refreshMemberDashboard() {
  await fetchDashboard()
  ElMessage.success('个人首页已刷新')
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

function goToSkillAction(action) {
  router.push({
    path: '/personal/skill',
    query: { action }
  })
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

function getPowerScore(power) {
  return Number(power?.totalBonusPercent || power?.bonusPercent || 0)
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(5)}%`
}

function normalizeMemberPower(power = {}) {
  return {
    ...power,
    id: power.id || String(power.powerId || ''),
    powerId: power.powerId,
    name: power.name || '',
    category: power.category || '',
    totalBonusPercent: Number(power.totalBonusPercent || 0),
    bonusPercent: Number(power.bonusPercent || 0),
    lingyunEnabled: !!power.lingyunEnabled,
    updatedAt: power.updatedAt || power.updateTime || power.updated_at || ''
  }
}

function recognitionStatusLabel(status) {
  return {
    recognizing: '识别中',
    recognized: '已识别',
    saved: '已新增',
    failed: '失败'
  }[String(status || '')] || '未记录'
}

function recognitionStatusTagType(status) {
  return {
    recognizing: 'warning',
    recognized: 'success',
    saved: 'success',
    failed: 'danger'
  }[String(status || '')] || 'info'
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

function formatDateTimeWithWeek(value) {
  const date = normalizeDate(value)
  if (!date) return '未记录时间'
  const dateText = date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'long'
  })
  const timeText = date.toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit'
  })
  return `${dateText} ${timeText}`
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
  gap: 12px;
  color: #172033;
  background:
    linear-gradient(180deg, rgba(250, 252, 255, 0.97), rgba(244, 248, 250, 0.97)),
    repeating-linear-gradient(90deg, rgba(23, 32, 51, 0.025) 0, rgba(23, 32, 51, 0.025) 1px, transparent 1px, transparent 84px);
}

.signup-command,
.panel,
.metric-card {
  border: 1px solid rgba(23, 32, 51, 0.09);
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(250, 252, 253, 0.9));
  box-shadow: 0 10px 26px rgba(23, 32, 51, 0.06);
}

.signup-command {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 0.36fr);
  gap: 16px;
  min-height: 148px;
  padding: 20px 22px;
  overflow: hidden;
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.96), rgba(247, 251, 249, 0.92)),
    linear-gradient(90deg, rgba(47, 111, 99, 0.08), rgba(232, 215, 84, 0.08));
}

.member-command {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 0.28fr);
  gap: 16px;
  min-height: 168px;
  padding: 22px;
  overflow: hidden;
  border: 1px solid rgba(23, 32, 51, 0.09);
  border-radius: 8px;
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.97), rgba(246, 251, 249, 0.93)),
    linear-gradient(90deg, rgba(47, 111, 99, 0.1), rgba(39, 118, 199, 0.08));
  box-shadow: 0 10px 26px rgba(23, 32, 51, 0.06);
}

.member-command-main {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.member-command-main h1 {
  margin: 10px 0 8px;
  color: #121826;
  font-size: 30px;
  line-height: 1.12;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.member-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  color: #5f6f86;
  font-weight: 800;
}

.member-ai-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  padding: 18px;
  border-radius: 8px;
  background:
    linear-gradient(135deg, #11261f, #1e473d),
    #11261f;
  color: #e8fff5;
}

.member-ai-panel span,
.member-ai-panel small {
  color: rgba(232, 255, 245, 0.76);
  font-size: 13px;
}

.member-ai-panel strong {
  display: block;
  margin: 8px 0;
  font-size: 38px;
  line-height: 1;
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
  margin: 10px 0 8px;
  color: #121826;
  font-size: 28px;
  line-height: 1.14;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}

.empty-copy {
  max-width: 620px;
  margin: 0 0 12px;
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
  margin-top: 14px;
}

.command-number {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  justify-content: center;
  gap: 12px;
  min-width: 0;
  padding: 16px;
  border-radius: 8px;
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

.command-stat strong {
  display: block;
  margin-top: 6px;
  font-size: 34px;
  line-height: 1;
}

.command-number small {
  grid-column: 1 / -1;
  margin-top: 0;
  color: rgba(232, 255, 245, 0.72);
}

.signup-grid,
.detail-grid,
.history-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
  align-items: start;
  gap: 12px;
}

.member-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.member-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.9fr);
  align-items: start;
  gap: 12px;
}

.member-metric {
  min-width: 0;
}

.member-metric > div:last-child {
  min-width: 0;
  flex: 1;
}

.member-progress {
  width: 100%;
  margin-top: 8px;
}

.member-power-list,
.member-recognition-list,
.member-status-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.member-power-row,
.member-recognition-row,
.member-status-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  min-height: 54px;
  padding: 10px 12px;
  border: 1px solid rgba(23, 32, 51, 0.07);
  border-radius: 8px;
  background: #fbfcfd;
}

.member-power-row strong,
.member-recognition-row strong,
.member-status-row strong {
  display: block;
  color: #121826;
  overflow-wrap: anywhere;
}

.member-power-row span,
.member-recognition-row span,
.member-status-row span {
  display: block;
  margin-top: 3px;
  color: #64748b;
  font-size: 13px;
}

.member-status-row strong {
  text-align: right;
}

.member-action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.member-action-grid .el-button {
  width: 100%;
  min-height: 42px;
  margin-left: 0;
}

.detail-grid {
  grid-template-columns: minmax(0, 1fr) minmax(380px, 0.9fr);
}

.panel {
  min-width: 0;
  padding: 16px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 12px;
}

.panel-subhead {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin: 0 0 12px;
  padding-top: 0;
  border-top: 0;
}

.battle-class-stack {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.battle-class-block {
  min-width: 0;
}

.leave-block {
  padding-left: 14px;
  border-left: 1px solid rgba(23, 32, 51, 0.08);
}

.panel-head-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-shrink: 0;
}

.panel-head h2,
.panel-subhead h2 {
  margin: 3px 0 0;
  color: #121826;
  font-size: 17px;
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
  grid-template-columns: repeat(auto-fit, minmax(112px, 1fr));
  gap: 8px;
}

.class-card-grid.compact {
  grid-template-columns: repeat(auto-fit, minmax(108px, 1fr));
}

.class-card {
  position: relative;
  min-height: 86px;
  padding: 11px;
  border: 1px solid rgba(23, 32, 51, 0.08);
  border-radius: 8px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.92));
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
  will-change: transform;
}

.class-card::before {
  display: none;
}

.class-card:hover {
  border-color: rgba(23, 32, 51, 0.16);
  box-shadow:
    0 10px 20px rgba(23, 32, 51, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.72) inset;
  transform: translate3d(0, -2px, 0);
}

.class-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  min-height: 28px;
  padding: 4px 10px;
  border: 1px solid rgba(23, 32, 51, 0.08);
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(246, 248, 250, 0.68));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.82),
    0 1px 2px rgba(15, 23, 42, 0.04);
  color: #263242;
  font-size: 14px;
  font-weight: 800;
  line-height: 1;
  backdrop-filter: blur(12px);
}

.class-chip::before {
  display: inline-block;
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--guild-class-accent, #2f6f63);
  box-shadow: 0 0 0 4px var(--guild-class-accent-soft, rgba(47, 111, 99, 0.12));
  content: "";
}

.class-card strong {
  display: block;
  margin-top: 8px;
  color: #121826;
  font-size: 21px;
  line-height: 1;
}

.class-card small {
  display: block;
  margin-top: 3px;
  color: #64748b;
  font-size: 12px;
}

.class-meter {
  height: 6px;
  margin-top: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf1f5;
}

.class-meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #8a97a8, #445066);
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 12px;
  min-height: 52px;
  padding: 9px 10px;
  border: 1px solid rgba(23, 32, 51, 0.07);
  border-radius: 8px;
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
  font-size: 20px;
}

.ops-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.metric-card {
  display: flex;
  gap: 12px;
  align-items: center;
  min-height: 82px;
  padding: 13px 14px;
}

.metric-card strong {
  display: block;
  margin: 3px 0;
  color: #121826;
  font-size: 23px;
  line-height: 1.1;
}

.metric-icon {
  display: grid;
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 8px;
  font-size: 18px;
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
  min-height: 58px;
  padding: 9px 10px;
  border: 1px solid rgba(23, 32, 51, 0.07);
  border-radius: 8px;
  background: #fbfcfd;
}

.battle-date {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 8px;
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
  gap: 8px;
}

.record-metric {
  min-height: 64px;
  padding: 10px;
  border-radius: 8px;
  background: #f4f8f7;
}

.record-metric span {
  color: #64748b;
  font-size: 13px;
}

.record-metric strong {
  display: block;
  margin-top: 7px;
  color: #121826;
  font-size: 20px;
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
  .member-command,
  .signup-grid,
  .detail-grid,
  .history-grid,
  .ops-grid,
  .member-content-grid {
    grid-template-columns: 1fr;
  }

  .ops-grid,
  .member-metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .signup-command,
  .member-command,
  .panel {
    padding: 18px;
  }

  .command-main h1,
  .member-command-main h1 {
    font-size: 28px;
  }

  .command-stat strong {
    font-size: 30px;
  }

  .battle-class-stack {
    grid-template-columns: 1fr;
  }

  .leave-block {
    padding-top: 14px;
    padding-left: 0;
    border-top: 1px solid rgba(23, 32, 51, 0.08);
    border-left: 0;
  }

  .detail-row,
  .battle-line {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .record-metrics,
  .ops-grid,
  .member-metric-grid,
  .member-action-grid {
    grid-template-columns: 1fr;
  }

  .member-power-row,
  .member-recognition-row,
  .member-status-row {
    grid-template-columns: 1fr;
  }

  .member-status-row strong {
    text-align: left;
  }
}
</style>
