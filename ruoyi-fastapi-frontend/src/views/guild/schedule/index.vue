<template>
  <div ref="pageRef" class="app-container schedule-page">
    <div class="schedule-layout">
      <section class="member-panel" data-guild-motion="hero">
        <div class="panel-header">
          <div>
            <h3>帮会成员</h3>
            <span>{{ filteredMembers.length }} / {{ members.length }} 人</span>
          </div>
          <el-button text type="primary" @click="fetchData">刷新</el-button>
        </div>

        <div class="member-tools">
          <el-input
            v-model="keyword"
            placeholder="搜索成员"
            clearable
          />
          <el-checkbox v-model="onlyApprovedBattleMembers">
            仅显示约战审核通过
          </el-checkbox>

          <el-checkbox v-model="excludeLeaveMembers">
            排除请假申请
          </el-checkbox>

          <div class="tree-toolbar">
            <span>职业文件夹</span>
            <div>
              <el-button text type="primary" @click="expandAllFolders">展开</el-button>
              <el-button text type="primary" @click="collapseAllFolders">收起</el-button>
            </div>
          </div>
        </div>

        <div class="member-list">
          <div
            v-for="folder in groupedMemberFolders"
            :key="folder.className"
            class="class-folder"
            :class="{ collapsed: isClassFolderCollapsed(folder.className) }"
          >
            <button
              type="button"
              class="folder-header"
              :aria-expanded="!isClassFolderCollapsed(folder.className)"
              @click="toggleClassFolder(folder.className)"
            >
              <span class="folder-left">
                <el-icon class="folder-caret"><ArrowRightBold /></el-icon>
                <el-icon class="folder-icon">
                  <Folder v-if="isClassFolderCollapsed(folder.className)" />
                  <FolderOpened v-else />
                </el-icon>
                <span class="folder-name">{{ folder.className }}</span>
              </span>
              <span class="folder-right">
                <span class="folder-progress">{{ folder.assignedCount }} / {{ folder.members.length }}</span>
                <span class="folder-swatch" :style="getClassStyle(folder.className)"></span>
              </span>
            </button>

            <div
              v-show="!isClassFolderCollapsed(folder.className)"
              :ref="el => setFolderBodyRef(el, folder.className)"
              class="folder-body"
            >
              <div
                v-for="member in folder.members"
                :key="member.member_id"
                class="folder-member-row"
                :class="{ assigned: getMemberAssignment(member.member_id) }"
                draggable="true"
                @dragstart="onDragStart(member, $event)"
                @dragend="onDragEnd"
              >
                <span class="member-file-dot" :style="getClassStyle(member.player_class)"></span>
                <span class="member-file-main">
                  <span class="member-name">{{ member.player_name }}</span>
                  <span class="member-meta-line">
                    <span>{{ getAssignedText(member.member_id) || '未排表' }}</span>
                    <template v-if="member.secondary_class">
                      <span class="member-meta-divider">·</span>
                      <span>副职 {{ member.secondary_class }}</span>
                    </template>
                  </span>
                </span>
                <span class="member-file-status" :class="{ assigned: getMemberAssignment(member.member_id) }">
                  {{ getMemberAssignment(member.member_id) ? '已排' : '待排' }}
                </span>
              </div>
            </div>
          </div>

          <el-empty v-if="!groupedMemberFolders.length" description="暂无成员" />
        </div>
      </section>

      <section class="schedule-panel" data-guild-reveal>
        <div class="panel-header">
          <div>
            <h3>约战排表</h3>
            <span>团队和小队会保存到数据库，每个小队最多 6 人</span>
          </div>
          <div class="schedule-actions">
            <el-button type="primary" @click="createTeam">创建团队</el-button>
            <el-button @click="saveHistorySnapshot">保存历史</el-button>
            <el-button @click="openHistory">历史查询</el-button>
          </div>
        </div>

        <div v-loading="loading" class="team-board">
          <div v-if="schedule.teams.length" class="team-list">
            <section v-for="team in schedule.teams" :key="team.team_id" class="team-section">
              <div class="team-header">
                <div>
                  <h4>{{ team.team_name }}</h4>
                  <span>{{ getTeamMemberCount(team) }} 人 / {{ team.squads.length }} 小队</span>
                </div>
                <div class="team-actions">
                  <el-button size="small" type="primary" @click="createSquad(team)">创建小队</el-button>
                  <el-button size="small" text type="danger" @click="removeTeam(team)">删除</el-button>
                </div>
              </div>

              <div v-if="team.squads.length" class="squad-grid">
                <div
                  v-for="squad in team.squads"
                  :key="squad.squad_id"
                  class="squad-box"
                  :class="{ 'is-over': dragOverKey === getSquadKey(team.team_id, squad.squad_id) }"
                  @dragover.prevent="dragOverKey = getSquadKey(team.team_id, squad.squad_id)"
                  @dragleave="dragOverKey = ''"
                  @drop="onDrop(team, squad)"
                >
                  <div class="squad-header">
                    <strong>{{ squad.squad_name }}</strong>
                    <div class="squad-actions">
                      <span>{{ squad.members.length }} / {{ squad.max_members }}</span>
                      <button type="button" title="删除小队" @click.stop="removeSquad(team, squad)">x</button>
                    </div>
                  </div>

                  <div class="squad-members">
                    <div
                      v-for="member in squad.members"
                      :key="member.member_id"
                      class="schedule-chip"
                      :style="getClassStyle(member.player_class)"
                      draggable="true"
                      @dragstart="onDragStart(member, $event)"
                      @dragend="onDragEnd"
                    >
                      <span>{{ member.player_name }}</span>
                      <button type="button" title="移出排表" @click.stop="clearMember(member)">x</button>
                    </div>
                    <span v-if="!squad.members.length" class="drop-hint">拖入成员</span>
                  </div>
                </div>
              </div>

              <el-empty
                v-else
                description="这个团队还没有小队"
              >
                <el-button type="primary" @click="createSquad(team)">创建小队</el-button>
              </el-empty>
            </section>
          </div>

          <el-empty
            v-else
            class="empty-board-canvas"
            description="还没有团队"
          >
            <el-button type="primary" @click="createTeam">创建团队</el-button>
          </el-empty>
        </div>
      </section>
    </div>

    <el-dialog
      v-model="historyVisible"
      title="历史查询"
      width="820px"
      append-to-body
    >
      <div class="history-layout">
        <div class="history-list">
          <div
            v-for="item in historyRows"
            :key="item.schedule_id"
            class="history-item"
            :class="{ active: historyPreview?.schedule_id === item.schedule_id }"
            @click="viewHistory(item)"
          >
            <strong>{{ item.schedule_name }}</strong>
            <span>{{ item.create_time }}</span>
          </div>
          <el-empty v-if="!historyRows.length" description="暂无历史" />
        </div>

        <div class="history-preview">
          <template v-if="historyPreview">
            <div class="preview-header">
              <h4>{{ historyPreview.schedule_name }}</h4>
              <el-button type="primary" @click="useHistoryConfiguration">应用配置</el-button>
            </div>
            <section
              v-for="team in historyPreview.teams"
              :key="team.team_id"
              class="preview-team"
            >
              <strong>{{ team.team_name }}</strong>
              <div
                v-for="squad in team.squads"
                :key="squad.squad_id"
                class="preview-squad"
              >
                <span>{{ squad.squad_name }}: {{ squad.members.length }} / {{ squad.max_members }}</span>
                <div class="preview-members">
                  <span
                    v-for="member in squad.members"
                    :key="member.assignment_id || member.member_id"
                    class="preview-chip"
                    :style="getClassStyle(member.player_class)"
                  >
                    {{ member.player_name }}
                  </span>
                </div>
              </div>
            </section>
          </template>
          <el-empty v-else description="选择一条历史查看详情" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRightBold, Folder, FolderOpened } from '@element-plus/icons-vue'
import { getApprovedBattleRegistrationsForSchedule, getBattleLeaveRegistrationsForSchedule } from '@/api/guild/battle'
import {
  addScheduleSquad,
  addScheduleTeam,
  applyScheduleHistory,
  clearScheduleAssignment,
  deleteScheduleSquad,
  deleteScheduleTeam,
  getCurrentSchedule,
  getScheduleDetail,
  getScheduleHistory,
  saveScheduleAssignment,
  saveScheduleSnapshot
} from '@/api/guild/schedule'
import useGuildMemberStore from '@/store/modules/guildMember'
import { useGuildClassColors } from '@/utils/guildClassColor'
import { useGuildPageMotion } from '@/composables/useGuildPageMotion'

let scheduleGsapLoader = null
function loadScheduleGsap() {
  if (!scheduleGsapLoader) {
    scheduleGsapLoader = import('gsap').then(gsapModule => gsapModule.gsap || gsapModule.default || gsapModule)
  }
  return scheduleGsapLoader
}

const guildMemberStore = useGuildMemberStore()
const pageRef = ref(null)
const loading = ref(false)
const members = computed(() => guildMemberStore.members)
const schedule = ref({ teams: [] })
const { getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()

useGuildPageMotion(pageRef)
const keyword = ref('')
const onlyApprovedBattleMembers = ref(true)
const excludeLeaveMembers = ref(true)
const approvedBattleMemberIds = ref([])
const leaveMemberIds = ref([])
const draggingMember = ref(null)
const dragOverKey = ref('')
const historyVisible = ref(false)
const historyRows = ref([])
const historyPreview = ref(null)
const collapsedClassFolders = ref(new Set())
const folderBodyRefs = new Map()

const UNSET_CLASS_NAME = '未设置'

const assignedByMemberId = computed(() => {
  const map = {}
  ;(schedule.value.teams || []).forEach(team => {
    ;(team.squads || []).forEach(squad => {
      ;(squad.members || []).forEach(member => {
        map[member.member_id] = {
          teamName: team.team_name,
          squadName: squad.squad_name,
          teamId: team.team_id,
          squadId: squad.squad_id
        }
      })
    })
  })
  return map
})

const filteredMembers = computed(() => {
  const value = keyword.value.trim().toLowerCase()
  const approvedSet = new Set(approvedBattleMemberIds.value)
  const leaveSet = new Set(leaveMemberIds.value)
  return members.value.filter(member => {
    const matchesKeyword = !value || [member.player_name, member.player_class, member.secondary_class]
      .filter(Boolean)
      .some(text => String(text).toLowerCase().includes(value))
    const matchesBattle = !onlyApprovedBattleMembers.value || approvedSet.has(member.member_id)
    const matchesLeave = !excludeLeaveMembers.value || !leaveSet.has(member.member_id)
    return matchesKeyword && matchesBattle && matchesLeave
  })
})

const groupedMemberFolders = computed(() => {
  const assignedMap = assignedByMemberId.value
  const groups = new Map()
  filteredMembers.value.forEach(member => {
    const className = String(member.player_class || '').trim() || UNSET_CLASS_NAME
    if (!groups.has(className)) {
      groups.set(className, [])
    }
    groups.get(className).push(member)
  })

  return Array.from(groups.entries())
    .sort(([classA], [classB]) => classA.localeCompare(classB, 'zh-Hans-CN'))
    .map(([className, groupMembers]) => {
      const sortedMembers = [...groupMembers].sort((memberA, memberB) => {
        const assignedA = assignedMap[memberA.member_id] ? 1 : 0
        const assignedB = assignedMap[memberB.member_id] ? 1 : 0
        if (assignedA !== assignedB) return assignedA - assignedB
        return String(memberA.player_name || '').localeCompare(String(memberB.player_name || ''), 'zh-Hans-CN')
      })
      return {
        className,
        members: sortedMembers,
        assignedCount: sortedMembers.reduce((total, member) => total + (assignedMap[member.member_id] ? 1 : 0), 0)
      }
    })
})

function getSquadKey(teamId, squadId) {
  return `${teamId}-${squadId}`
}

function getMemberAssignment(memberId) {
  return assignedByMemberId.value[memberId]
}

function getAssignedText(memberId) {
  const assignment = getMemberAssignment(memberId)
  if (!assignment) return ''
  return `${assignment.teamName} / ${assignment.squadName}`
}

function getClassStyle(className) {
  return getGuildClassStyle(className)
}

function setFolderBodyRef(el, className) {
  if (el) {
    folderBodyRefs.set(className, el)
  } else {
    folderBodyRefs.delete(className)
  }
}

function isClassFolderCollapsed(className) {
  return collapsedClassFolders.value.has(className)
}

async function toggleClassFolder(className) {
  const nextCollapsed = new Set(collapsedClassFolders.value)
  const willOpen = nextCollapsed.has(className)
  if (willOpen) {
    nextCollapsed.delete(className)
  } else {
    nextCollapsed.add(className)
  }
  collapsedClassFolders.value = nextCollapsed

  if (willOpen) {
    await nextTick()
    animateFolderOpen(className)
  }
}

async function animateFolderOpen(className) {
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  const body = folderBodyRefs.get(className)
  if (!body) return
  const gsap = await loadScheduleGsap()
  const rows = gsap.utils.toArray('.folder-member-row', body).slice(0, 32)
  const staggerStep = gsap.utils.clamp(0.012, 0.035, rows.length ? 0.18 / rows.length : 0.018)
  gsap.fromTo(
    rows,
    { autoAlpha: 0, y: -4 },
    {
      autoAlpha: 1,
      y: 0,
      duration: 0.22,
      ease: 'power2.out',
      stagger: staggerStep,
      overwrite: true
    }
  )
}

async function expandAllFolders() {
  collapsedClassFolders.value = new Set()
  await nextTick()
  groupedMemberFolders.value.slice(0, 8).forEach(folder => animateFolderOpen(folder.className))
}

function collapseAllFolders() {
  collapsedClassFolders.value = new Set(groupedMemberFolders.value.map(folder => folder.className))
}

function getTeamMemberCount(team) {
  return (team.squads || []).reduce((total, squad) => total + (squad.members || []).length, 0)
}

function normalizeSchedule(data) {
  schedule.value = {
    ...data,
    teams: (data?.teams || []).map(team => ({
      ...team,
      squads: team.squads || []
    }))
  }
}

function onDragStart(member, event) {
  draggingMember.value = member
  if (event?.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(member.member_id))
  }
}

function onDragEnd() {
  draggingMember.value = null
  dragOverKey.value = ''
}

async function onDrop(team, squad) {
  dragOverKey.value = ''
  if (!draggingMember.value) return
  if (squad.members.some(member => member.member_id === draggingMember.value.member_id)) {
    draggingMember.value = null
    return
  }
  if (squad.members.length >= squad.max_members) {
    ElMessage.warning('每个小队最多 6 人')
    draggingMember.value = null
    return
  }
  try {
    await saveScheduleAssignment({
      member_id: draggingMember.value.member_id,
      team_id: team.team_id,
      squad_id: squad.squad_id
    })
    ElMessage.success('排表已保存')
    await fetchSchedule()
  } catch {
    ElMessage.error('排表保存失败')
  } finally {
    draggingMember.value = null
  }
}

async function createTeam() {
  try {
    const { value } = await ElMessageBox.prompt('请输入团队名称', '创建团队', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：一团'
    })
    await addScheduleTeam({ team_name: value })
    ElMessage.success('团队创建成功')
    await fetchSchedule()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('创建团队失败')
    }
  }
}

async function createSquad(team) {
  try {
    const { value } = await ElMessageBox.prompt('请输入小队名称', '创建小队', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPlaceholder: `第 ${team.squads.length + 1} 小队`
    })
    await addScheduleSquad(team.team_id, { squad_name: value })
    ElMessage.success('小队创建成功')
    await fetchSchedule()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('创建小队失败')
    }
  }
}

async function removeTeam(team) {
  try {
    await ElMessageBox.confirm(`删除团队 "${team.team_name}" 会同时移出其中所有成员，确定继续吗？`, '删除团队', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await deleteScheduleTeam(team.team_id)
    ElMessage.success('团队已删除')
    await fetchSchedule()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除团队失败')
    }
  }
}

async function removeSquad(team, squad) {
  try {
    await ElMessageBox.confirm(`删除 "${squad.squad_name}" 会同时移出其中所有成员，确定继续吗？`, '删除小队', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await deleteScheduleSquad(team.team_id, squad.squad_id)
    ElMessage.success('小队已删除')
    await fetchSchedule()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除小队失败')
    }
  }
}

async function clearMember(member) {
  try {
    await clearScheduleAssignment(member.member_id)
    ElMessage.success('已移出排表')
    await fetchSchedule()
  } catch {
    ElMessage.error('移出失败')
  }
}

async function saveHistorySnapshot() {
  const defaultName = `约战排表 ${new Date().toLocaleString()}`
  try {
    const { value } = await ElMessageBox.prompt('请输入历史名称', '保存历史', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: defaultName
    })
    await saveScheduleSnapshot({ schedule_name: value })
    ElMessage.success('历史已保存')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('保存历史失败')
    }
  }
}

async function openHistory() {
  historyVisible.value = true
  historyPreview.value = null
  await fetchHistory()
}

async function viewHistory(item) {
  try {
    const res = await getScheduleDetail(item.schedule_id)
    historyPreview.value = res.data || null
  } catch {
    ElMessage.error('加载历史详情失败')
  }
}

async function useHistoryConfiguration() {
  if (!historyPreview.value) return
  try {
    await ElMessageBox.confirm('应用该历史配置会替换当前约战排表，确定继续吗？', '应用配置', {
      type: 'warning',
      confirmButtonText: '应用配置',
      cancelButtonText: '取消'
    })
    await applyScheduleHistory(historyPreview.value.schedule_id)
    ElMessage.success('历史配置已应用')
    historyVisible.value = false
    await fetchSchedule()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('应用历史配置失败')
    }
  }
}

async function fetchMembers() {
  await guildMemberStore.load({ silent: guildMemberStore.hasReadyCache })
}

async function fetchApprovedBattleMembers() {
  const res = await getApprovedBattleRegistrationsForSchedule()
  approvedBattleMemberIds.value = (res.data || []).map(item => item.member_id).filter(Boolean)
}

async function fetchLeaveMembers() {
  const res = await getBattleLeaveRegistrationsForSchedule()
  leaveMemberIds.value = [...new Set((res.data || []).map(item => item.member_id).filter(Boolean))]
}

async function fetchSchedule() {
  const res = await getCurrentSchedule()
  normalizeSchedule(res.data || { teams: [] })
}

async function fetchHistory() {
  const res = await getScheduleHistory()
  historyRows.value = res.data || []
}

async function fetchClassColors() {
  await loadGuildClassColors()
}

async function fetchData() {
  loading.value = true
  try {
    await Promise.all([fetchMembers(), fetchApprovedBattleMembers(), fetchLeaveMembers(), fetchSchedule(), fetchClassColors()])
  } catch {
    ElMessage.error('加载排表数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.schedule-page {
  height: calc(100vh - 84px);
  overflow: hidden;
}

.schedule-layout {
  display: grid;
  grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
  gap: 12px;
  height: 100%;
}

.member-panel,
.schedule-panel {
  min-height: 0;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  display: flex;
  flex-direction: column;
}

.panel-header {
  min-height: 56px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-header h3,
.team-header h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
}

.panel-header span,
.team-header span {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.member-tools {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.tree-toolbar {
  min-height: 28px;
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.tree-toolbar > div {
  display: flex;
  align-items: center;
  gap: 2px;
}

.member-list {
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 8px 10px 12px;
  background:
    linear-gradient(90deg, rgba(99, 102, 241, 0.07) 1px, transparent 1px) 0 0 / 18px 18px,
    linear-gradient(180deg, rgba(99, 102, 241, 0.04) 1px, transparent 1px) 0 0 / 18px 18px;
}

.class-folder {
  position: relative;
  margin-bottom: 6px;
}

.folder-header {
  width: 100%;
  min-height: 34px;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 0 7px 0 5px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
  will-change: transform;
}

.folder-header:hover {
  border-color: rgba(99, 102, 241, 0.28);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 10px 24px rgba(88, 99, 122, 0.08);
  transform: translateY(-1px);
}

.folder-left,
.folder-right {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.folder-caret {
  color: var(--el-text-color-secondary);
  font-size: 11px;
  transform: rotate(90deg);
  transition: transform 0.18s ease;
}

.class-folder.collapsed .folder-caret {
  transform: rotate(0deg);
}

.folder-icon {
  color: #7c5cff;
  font-size: 16px;
  filter: drop-shadow(0 4px 8px rgba(124, 92, 255, 0.18));
}

.folder-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 700;
}

.folder-progress {
  color: var(--el-text-color-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
}

.folder-swatch,
.member-file-dot {
  border: 1px solid currentColor;
  border-radius: 999px;
  flex: 0 0 auto;
}

.folder-swatch {
  width: 13px;
  height: 13px;
}

.folder-body {
  position: relative;
  margin: 2px 0 6px 17px;
  padding-left: 10px;
}

.folder-body::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 6px;
  left: 0;
  width: 1px;
  background: linear-gradient(180deg, rgba(124, 92, 255, 0.28), rgba(124, 92, 255, 0.04));
}

.folder-member-row {
  min-height: 42px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 6px;
  padding: 6px 8px;
  margin-top: 5px;
  cursor: grab;
  background: rgba(255, 255, 255, 0.86);
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  transition: transform 0.15s ease, border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
  will-change: transform, opacity;
}

.folder-member-row:hover {
  border-color: rgba(124, 92, 255, 0.35);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 8px 18px rgba(88, 99, 122, 0.08);
  transform: translateX(2px);
}

.folder-member-row:active {
  cursor: grabbing;
}

.folder-member-row.assigned {
  border-style: solid;
  background: rgba(245, 247, 251, 0.78);
}

.member-file-dot {
  width: 10px;
  height: 10px;
}

.member-file-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.member-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 700;
}

.member-meta-line {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.member-meta-divider {
  margin: 0 4px;
  color: var(--el-text-color-placeholder);
}

.member-file-status {
  border-radius: 999px;
  padding: 2px 6px;
  background: rgba(124, 92, 255, 0.09);
  color: #5b45d9;
  font-size: 11px;
  font-weight: 700;
}

.member-file-status.assigned {
  background: rgba(34, 197, 94, 0.12);
  color: #168a45;
}

.class-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  padding: 2px 8px;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-size: 12px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.mini-class-tag {
  min-width: 0;
  padding: 1px 7px;
  font-size: 12px;
}

.secondary-class-line {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.schedule-actions,
.team-actions,
.squad-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.team-board {
  position: relative;
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 14px;
  background:
    linear-gradient(90deg, rgba(99, 102, 241, 0.08) 1px, transparent 1px) 0 0 / 28px 28px,
    linear-gradient(180deg, rgba(99, 102, 241, 0.06) 1px, transparent 1px) 0 0 / 28px 28px,
    radial-gradient(circle at 24px 24px, rgba(124, 92, 255, 0.12) 1px, transparent 1px) 0 0 / 56px 56px,
    linear-gradient(180deg, rgba(248, 250, 252, 0.94), rgba(241, 245, 249, 0.82));
}

.team-board::before {
  content: "";
  position: sticky;
  top: 0;
  z-index: 1;
  display: block;
  height: 0;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.2), 0 14px 30px rgba(15, 23, 42, 0.08);
  pointer-events: none;
}

.team-list {
  min-width: 760px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.team-section {
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(8px);
}

.team-header {
  min-height: 48px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.82));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 8px 8px 0 0;
}

.squad-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
  padding: 12px;
}

.squad-box {
  min-height: 150px;
  border: 1px dashed rgba(100, 116, 139, 0.34);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.86)),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px) 0 0 / 18px 18px;
  display: flex;
  flex-direction: column;
  transition: transform 0.15s ease, background 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.squad-box.is-over {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  box-shadow: inset 0 0 0 1px var(--el-color-primary), 0 12px 28px rgba(64, 158, 255, 0.18);
  transform: translateY(-1px);
}

.squad-header {
  min-height: 36px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.squad-header strong {
  font-size: 14px;
  font-weight: 600;
}

.squad-header span {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.squad-actions button {
  width: 16px;
  height: 16px;
  border: 0;
  padding: 0;
  border-radius: 50%;
  line-height: 16px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  cursor: pointer;
}

.squad-members {
  min-height: 110px;
  flex: 1;
  padding: 8px;
  position: relative;
}

.schedule-chip {
  min-height: 26px;
  margin-bottom: 6px;
  padding: 3px 6px 3px 8px;
  border: 1px solid currentColor;
  border-radius: 999px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 12px;
  cursor: grab;
}

.schedule-chip button {
  width: 16px;
  height: 16px;
  border: 0;
  padding: 0;
  border-radius: 50%;
  line-height: 16px;
  color: inherit;
  background: rgba(0, 0, 0, 0.12);
  cursor: pointer;
}

.drop-hint {
  position: absolute;
  inset: 8px;
  border: 1px dashed rgba(148, 163, 184, 0.36);
  border-radius: 6px;
  background: rgba(248, 250, 252, 0.58);
  display: grid;
  place-items: center;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  pointer-events: none;
}

.empty-board-canvas {
  min-height: 360px;
  border: 1px dashed rgba(100, 116, 139, 0.32);
  border-radius: 10px;
  background:
    linear-gradient(90deg, rgba(148, 163, 184, 0.1) 1px, transparent 1px) 0 0 / 36px 36px,
    linear-gradient(180deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px) 0 0 / 36px 36px,
    rgba(255, 255, 255, 0.64);
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 12px;
  min-height: 420px;
}

.history-list,
.history-preview {
  min-height: 0;
  overflow: auto;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  padding: 10px;
}

.history-item {
  padding: 9px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-item:hover,
.history-item.active {
  background: var(--el-fill-color-light);
}

.history-item span,
.preview-squad span {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.preview-header {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.preview-header h4 {
  margin: 0;
}

.preview-team {
  border-top: 1px solid var(--el-border-color-lighter);
  padding: 10px 0;
}

.preview-squad {
  margin-top: 8px;
}

.preview-members {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 5px;
}

.preview-chip {
  padding: 2px 7px;
  border: 1px solid currentColor;
  border-radius: 999px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  font-size: 12px;
}

@media (max-width: 900px) {
  .schedule-page {
    height: auto;
    overflow: visible;
  }

  .schedule-layout,
  .history-layout {
    grid-template-columns: 1fr;
  }

  .member-panel {
    max-height: 460px;
  }

  .team-list {
    min-width: 0;
  }

  .panel-header,
  .team-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
