<template>
  <div class="app-container schedule-page">
    <div class="schedule-layout">
      <section class="member-panel">
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

          <div class="class-filter">
            <div class="filter-title">
              <span>职业</span>
              <el-button
                v-if="selectedClasses.length"
                text
                type="primary"
                @click="selectedClasses = []"
              >
                清空
              </el-button>
            </div>
            <el-checkbox-group v-model="selectedClasses" class="class-options">
              <el-checkbox-button
                v-for="className in availableClasses"
                :key="className"
                :label="className"
              >
                {{ className }}
              </el-checkbox-button>
            </el-checkbox-group>
            <span v-if="!availableClasses.length" class="empty-filter">暂无职业</span>
          </div>
        </div>

        <div class="member-list">
          <div
            v-for="member in filteredMembers"
            :key="member.member_id"
            class="member-card"
            :class="{ assigned: getMemberAssignment(member.member_id) }"
            draggable="true"
            @dragstart="onDragStart(member, $event)"
            @dragend="onDragEnd"
          >
            <div class="member-name-row">
              <span class="member-name">{{ member.player_name }}</span>
              <span class="class-tag" :style="getClassStyle(member.player_class)">
                {{ member.player_class || '未设置' }}
              </span>
            </div>
            <div class="member-meta">
              <span v-if="member.secondary_class">副职：{{ member.secondary_class }}</span>
              <span>{{ getAssignedText(member.member_id) || '未排表' }}</span>
            </div>
          </div>

          <el-empty v-if="!filteredMembers.length" description="暂无成员" />
        </div>
      </section>

      <section class="schedule-panel">
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
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMemberList } from '@/api/guild/member'
import { getClassColors } from '@/api/guild/classColor'
import { getApprovedBattleRegistrationsForSchedule } from '@/api/guild/battle'
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

const loading = ref(false)
const members = ref([])
const schedule = ref({ teams: [] })
const classColorMap = ref({})
const keyword = ref('')
const selectedClasses = ref([])
const onlyApprovedBattleMembers = ref(true)
const approvedBattleMemberIds = ref([])
const draggingMember = ref(null)
const dragOverKey = ref('')
const historyVisible = ref(false)
const historyRows = ref([])
const historyPreview = ref(null)

const availableClasses = computed(() => {
  return [...new Set(members.value.map(member => member.player_class).filter(Boolean))].sort()
})

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
  return members.value.filter(member => {
    const matchesKeyword = !value || [member.player_name, member.player_class, member.secondary_class]
      .filter(Boolean)
      .some(text => String(text).toLowerCase().includes(value))
    const matchesClass = !selectedClasses.value.length || selectedClasses.value.includes(member.player_class)
    const matchesBattle = !onlyApprovedBattleMembers.value || approvedSet.has(member.member_id)
    return matchesKeyword && matchesClass && matchesBattle
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
  if (!className) return {}
  const color = classColorMap.value[className]
  if (!color || color.bg_color === '#FFFFFF') return {}
  return {
    backgroundColor: color.bg_color,
    color: color.text_color
  }
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
  const res = await getMemberList()
  members.value = res.data || []
}

async function fetchApprovedBattleMembers() {
  const res = await getApprovedBattleRegistrationsForSchedule()
  approvedBattleMemberIds.value = (res.data || []).map(item => item.member_id).filter(Boolean)
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
  const res = await getClassColors()
  const map = {}
  ;((res.data || res) || []).forEach(item => {
    map[item.class_name] = item
  })
  classColorMap.value = map
}

async function fetchData() {
  loading.value = true
  try {
    await Promise.all([fetchMembers(), fetchApprovedBattleMembers(), fetchSchedule(), fetchClassColors()])
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

.class-filter {
  margin-top: 10px;
}

.filter-title {
  min-height: 24px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.class-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.class-options :deep(.el-checkbox-button__inner) {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 5px 9px;
  box-shadow: none;
}

.empty-filter {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}

.member-list {
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 12px;
}

.member-card {
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
  cursor: grab;
  background: var(--el-fill-color-blank);
  transition: border-color 0.15s, background 0.15s;
}

.member-card:hover {
  border-color: var(--el-color-primary);
}

.member-card:active {
  cursor: grabbing;
}

.member-card.assigned {
  border-style: dashed;
}

.member-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.member-name {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-meta {
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.class-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.schedule-actions,
.team-actions,
.squad-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.team-board {
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 12px;
}

.team-list {
  min-width: 760px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.team-section {
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color-blank);
}

.team-header {
  min-height: 48px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.squad-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
  padding: 12px;
}

.squad-box {
  min-height: 150px;
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  background: var(--el-bg-color);
  display: flex;
  flex-direction: column;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.squad-box.is-over {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  box-shadow: inset 0 0 0 1px var(--el-color-primary);
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
  border-radius: 4px;
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
  border-radius: 4px;
  display: grid;
  place-items: center;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  pointer-events: none;
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
  border-radius: 4px;
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
