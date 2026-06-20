<template>
  <div ref="pageRef" class="app-container schedule-page">
    <div class="schedule-layout">
      <section class="member-panel" data-guild-motion="hero">
        <div class="panel-header">
          <div>
            <h3>帮会成员</h3>
            <span>{{ filteredMembers.length }} / {{ allMembers.length }} 人</span>
          </div>
          <div class="member-header-actions">
            <el-button text type="primary" @click="openTempMemberDialog">临时补人</el-button>
            <el-button text type="primary" @click="fetchData">刷新</el-button>
          </div>
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
                    <span v-if="member.is_temporary" class="temp-member-badge">临时</span>
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
            <el-button @click="exportCurrentSchedule">导出 Excel</el-button>
            <el-button @click="saveHistorySnapshot">保存历史</el-button>
            <el-button @click="openHistory">历史查询</el-button>
          </div>
        </div>

        <ScheduleUniverSheet
          ref="scheduleSheetRef"
          v-loading="loading"
          :schedule="schedule"
          :dragging-member="draggingMember"
          :get-class-style="getClassStyle"
          @assign-member="handleSheetAssignMember"
          @workbook-assignments-change="syncWorkbookAssignments"
          @temp-members-change="syncTempMembers"
        />
      </section>
    </div>

    <el-dialog
      v-model="tempMemberVisible"
      title="临时补人"
      width="420px"
      append-to-body
    >
      <el-form label-width="78px" @submit.prevent>
        <el-form-item label="玩家名字">
          <el-input
            v-model="tempMemberForm.player_name"
            placeholder="输入临时补人的名字"
            maxlength="30"
            clearable
          />
        </el-form-item>
        <el-form-item label="职业">
          <el-select
            v-model="tempMemberForm.player_class"
            placeholder="选择职业"
            filterable
            allow-create
            default-first-option
            style="width: 100%"
          >
            <el-option
              v-for="className in classOptions"
              :key="className"
              :label="className"
              :value="className"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tempMemberVisible = false">取消</el-button>
        <el-button type="primary" @click="addTempMember">加入临时列表</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="historyVisible"
      title="历史查询"
      width="92vw"
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
            <div class="history-item-main">
              <strong>{{ item.schedule_name }}</strong>
              <span>{{ item.create_time }}</span>
            </div>
            <div class="history-item-actions">
              <el-button text type="primary" size="small" @click.stop="renameHistory(item)">重命名</el-button>
              <el-button text type="danger" size="small" @click.stop="deleteHistory(item)">删除</el-button>
            </div>
          </div>
          <el-empty v-if="!historyRows.length" description="暂无历史" />
        </div>

        <div class="history-preview">
          <template v-if="historyPreview">
            <div class="preview-header">
              <h4>{{ historyPreview.schedule_name }}</h4>
              <div class="preview-actions">
                <el-button @click="renameHistory(historyPreview)">重命名</el-button>
                <el-button type="danger" @click="deleteHistory(historyPreview)">删除</el-button>
                <el-button @click="exportHistoryWorkbook">导出 Excel</el-button>
                <el-button type="primary" @click="useHistoryConfiguration">应用配置</el-button>
              </div>
            </div>
            <ScheduleWorkbookTable :workbook="historyWorkbook" />
            <div v-if="historyPreview.teams?.length" class="preview-summary">
              <div class="preview-summary-title">结构化排表摘要</div>
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
            </div>
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
import ScheduleUniverSheet from './components/ScheduleUniverSheet.vue'
import ScheduleWorkbookTable from './components/ScheduleWorkbookTable.vue'
import {
  applyScheduleHistory,
  deleteScheduleHistory,
  getCurrentSchedule,
  getScheduleDetail,
  getScheduleWorkbook,
  getScheduleHistory,
  renameScheduleHistory,
  saveScheduleAssignment,
  saveScheduleSnapshot
} from '@/api/guild/schedule'
import useGuildMemberStore from '@/store/modules/guildMember'
import { useGuildClassColors } from '@/utils/guildClassColor'
import { useGuildPageMotion } from '@/composables/useGuildPageMotion'
import { exportScheduleWorkbook } from './utils/scheduleWorkbook'

let scheduleGsapLoader = null
function loadScheduleGsap() {
  if (!scheduleGsapLoader) {
    scheduleGsapLoader = import('gsap').then(gsapModule => gsapModule.gsap || gsapModule.default || gsapModule)
  }
  return scheduleGsapLoader
}

const guildMemberStore = useGuildMemberStore()
const pageRef = ref(null)
const scheduleSheetRef = ref(null)
const loading = ref(false)
const members = computed(() => guildMemberStore.members)
const schedule = ref({ teams: [] })
const { classOptions, getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()

useGuildPageMotion(pageRef)
const keyword = ref('')
const onlyApprovedBattleMembers = ref(true)
const excludeLeaveMembers = ref(true)
const approvedBattleMemberIds = ref([])
const leaveMemberIds = ref([])
const draggingMember = ref(null)
const historyVisible = ref(false)
const historyRows = ref([])
const historyPreview = ref(null)
const historyWorkbook = ref(null)
const tempMemberVisible = ref(false)
const tempMembers = ref([])
const tempMemberForm = ref({
  player_name: '',
  player_class: ''
})
const workbookAssignedByMemberId = ref({})
const collapsedClassFolders = ref(new Set())
const folderBodyRefs = new Map()

const UNSET_CLASS_NAME = '未设置'

const allMembers = computed(() => [
  ...members.value,
  ...tempMembers.value
])

const assignedByMemberId = computed(() => {
  const map = {}
  ;(schedule.value.teams || []).forEach(team => {
    ;(team.squads || []).forEach(squad => {
      ;(squad.members || []).forEach(member => {
        map[member.member_id] = {
          teamName: team.team_name,
          squadName: squad.squad_name,
          teamId: team.team_id,
          squadId: squad.squad_id,
          source: 'schedule'
        }
      })
    })
  })
  Object.values(workbookAssignedByMemberId.value).forEach((assignment) => {
    if (!assignment?.member_id || map[assignment.member_id]) return
    map[assignment.member_id] = {
      teamName: '自由表格',
      squadName: assignment.cellLabel,
      cellLabel: assignment.cellLabel,
      source: 'workbook'
    }
  })
  return map
})

const filteredMembers = computed(() => {
  const value = keyword.value.trim().toLowerCase()
  const approvedSet = new Set(approvedBattleMemberIds.value)
  const leaveSet = new Set(leaveMemberIds.value)
  return allMembers.value.filter(member => {
    const matchesKeyword = !value || [member.player_name, member.player_class, member.secondary_class]
      .filter(Boolean)
      .some(text => String(text).toLowerCase().includes(value))
    const matchesBattle = member.is_temporary || !onlyApprovedBattleMembers.value || approvedSet.has(member.member_id)
    const matchesLeave = member.is_temporary || !excludeLeaveMembers.value || !leaveSet.has(member.member_id)
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
}

function openTempMemberDialog() {
  tempMemberForm.value = {
    player_name: '',
    player_class: classOptions.value[0] || ''
  }
  tempMemberVisible.value = true
}

async function addTempMember() {
  const playerName = tempMemberForm.value.player_name.trim()
  const playerClass = tempMemberForm.value.player_class.trim()
  if (!playerName) {
    ElMessage.warning('请输入玩家名字')
    return
  }
  if (!playerClass) {
    ElMessage.warning('请选择职业')
    return
  }
  const tempMember = {
    member_id: `temp_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`,
    player_name: playerName,
    player_class: playerClass,
    secondary_class: '',
    is_temporary: true
  }
  await scheduleSheetRef.value?.upsertTempMember?.(tempMember)
  const nextCollapsed = new Set(collapsedClassFolders.value)
  nextCollapsed.delete(playerClass || UNSET_CLASS_NAME)
  collapsedClassFolders.value = nextCollapsed
  tempMemberVisible.value = false
  ElMessage.success('临时玩家已加入')
}

async function exportCurrentSchedule() {
  try {
    await scheduleSheetRef.value?.flushWorkbookSave?.()
    await scheduleSheetRef.value?.exportWorkbook?.(`约战排表-${formatExportTime()}.xlsx`)
  } catch {
    ElMessage.error('导出当前排表失败')
  }
}

async function saveHistorySnapshot() {
  const defaultName = `约战排表 ${new Date().toLocaleString()}`
  try {
    await scheduleSheetRef.value?.flushWorkbookSave?.()
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
  historyWorkbook.value = null
  await fetchHistory()
  if (historyRows.value.length) {
    await viewHistory(historyRows.value[0])
  }
}

async function viewHistory(item) {
  try {
    const [detailRes, workbookRes] = await Promise.all([
      getScheduleDetail(item.schedule_id),
      getScheduleWorkbook(item.schedule_id)
    ])
    historyPreview.value = detailRes.data || null
    historyWorkbook.value = workbookRes.data?.workbook || null
  } catch {
    ElMessage.error('加载历史详情失败')
  }
}

async function exportHistoryWorkbook() {
  if (!historyPreview.value) return
  try {
    if (!historyWorkbook.value) {
      const res = await getScheduleWorkbook(historyPreview.value.schedule_id)
      historyWorkbook.value = res.data?.workbook || null
    }
    if (!historyWorkbook.value) {
      ElMessage.warning('该历史暂无自由表格可导出')
      return
    }
    await exportScheduleWorkbook(
      historyWorkbook.value,
      `${sanitizeFilename(historyPreview.value.schedule_name || '历史排表')}-${formatExportTime()}.xlsx`
    )
  } catch {
    ElMessage.error('导出历史排表失败')
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

async function handleSheetAssignMember({ member, team, squad, orderNum }) {
  if (!member || !team || !squad) return
  try {
    await saveScheduleAssignment({
      member_id: member.member_id,
      team_id: team.team_id,
      squad_id: squad.squad_id,
      order_num: orderNum
    })
    ElMessage.success('排表已保存')
    await fetchSchedule()
  } catch (error) {
    ElMessage.error(error?.message || '排表保存失败')
  } finally {
    draggingMember.value = null
  }
}

function syncWorkbookAssignments(assignments = []) {
  const nextMap = {}
  assignments.forEach((assignment) => {
    if (!assignment?.member_id) return
    const memberId = String(assignment.member_id)
    nextMap[memberId] = {
      ...assignment,
      member_id: memberId
    }
  })
  workbookAssignedByMemberId.value = nextMap
}

function syncTempMembers(list = []) {
  tempMembers.value = list.map(member => ({
    ...member,
    member_id: String(member.member_id),
    is_temporary: true
  }))
}

async function renameHistory(item) {
  if (!item?.schedule_id) return
  try {
    const { value } = await ElMessageBox.prompt('请输入新的历史名称', '重命名历史排表', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: item.schedule_name || '',
      inputPattern: /\S+/,
      inputErrorMessage: '历史名称不能为空'
    })
    await renameScheduleHistory(item.schedule_id, { schedule_name: value })
    ElMessage.success('历史名称已更新')
    await fetchHistory()
    if (historyPreview.value?.schedule_id === item.schedule_id) {
      historyPreview.value = {
        ...historyPreview.value,
        schedule_name: value
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重命名历史失败')
    }
  }
}

async function deleteHistory(item) {
  if (!item?.schedule_id) return
  try {
    await ElMessageBox.confirm(`确定删除历史排表「${item.schedule_name || item.schedule_id}」吗？删除后不可在历史查询中恢复。`, '删除历史排表', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await deleteScheduleHistory(item.schedule_id)
    ElMessage.success('历史排表已删除')
    if (historyPreview.value?.schedule_id === item.schedule_id) {
      historyPreview.value = null
      historyWorkbook.value = null
    }
    await fetchHistory()
    if (!historyPreview.value && historyRows.value.length) {
      await viewHistory(historyRows.value[0])
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除历史失败')
    }
  }
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

function formatExportTime() {
  return new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')
}

function sanitizeFilename(value) {
  return String(value || '约战排表').replace(/[\\/:*?"<>|]/g, '_')
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

.panel-header h3 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
}

.panel-header span {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.member-header-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
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

.temp-member-badge {
  display: inline-flex;
  align-items: center;
  margin-right: 5px;
  border: 1px solid rgba(245, 158, 11, 0.32);
  border-radius: 999px;
  padding: 0 5px;
  background: rgba(245, 158, 11, 0.13);
  color: #a16207;
  font-size: 10px;
  font-weight: 800;
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

.schedule-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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

.history-preview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  padding: 9px;
  border-radius: 4px;
  cursor: pointer;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
}

.history-item:hover,
.history-item.active {
  background: var(--el-fill-color-light);
}

.history-item-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-item-main strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-item-actions {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.16s ease;
}

.history-item:hover .history-item-actions,
.history-item.active .history-item-actions {
  opacity: 1;
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

.preview-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.preview-header h4 {
  margin: 0;
}

.preview-team {
  border-top: 1px solid var(--el-border-color-lighter);
  padding: 10px 0;
}

.preview-summary {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 10px 12px 2px;
  background: var(--el-fill-color-extra-light);
}

.preview-summary-title {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 800;
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

  .panel-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
