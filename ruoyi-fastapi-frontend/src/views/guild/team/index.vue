<template>
  <div ref="pageRef" class="app-container">
    <el-card data-guild-motion="hero">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>分团管理（共 {{ allMembers.length }} 人）</span>
            <div class="team-tags">
              <el-tag
                v-for="team in teams"
                :key="team.id"
                closable
                type="primary"
                size="small"
                @close="handleDeleteTeam(team)"
              >
                {{ team.team_name }}
              </el-tag>
            </div>
          </div>
          <el-button type="primary" @click="openTeamDialog">添加团队</el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="allMembers"
        border
        stripe
      >
        <el-table-column type="selection" width="50" />
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="player_name" label="玩家名" min-width="120" />
        <el-table-column prop="player_class" label="主职业" width="100">
          <template #default="{ row }">
            <span
              class="class-tag"
              :style="getClassStyle(row.player_class)"
            >{{ row.player_class }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="团队分配" width="220">
          <template #default="{ row }">
            <el-select
              :model-value="row.team_id"
              clearable
              placeholder="未分配"
              size="small"
              style="width: 200px"
              @change="(val) => onTeamChange(row, val)"
            >
              <el-option
                v-for="t in teams"
                :key="t.id"
                :label="t.team_name"
                :value="t.id"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="队内序号" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.squad_number"
              :min="1"
              size="small"
              controls-position="right"
              style="width: 100px"
              @blur="onSquadBlur(row)"
            />
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="showTeamDialog" title="添加团队" width="400px">
        <el-form :model="teamForm" label-width="80px">
          <el-form-item label="团队名称" required>
            <el-input v-model="teamForm.team_name" placeholder="请输入团队名称" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showTeamDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAddTeam" :loading="teamLoading">确认添加</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { editMember } from '@/api/guild/member'
import { getTeams, addTeam, deleteTeam } from '@/api/guild/team'
import { ElMessage, ElMessageBox } from 'element-plus'
import useGuildMemberStore from '@/store/modules/guildMember'
import { useGuildClassColors } from '@/utils/guildClassColor'
import { useGuildPageMotion } from '@/composables/useGuildPageMotion'

const guildMemberStore = useGuildMemberStore()
const pageRef = ref(null)
const loading = computed(() => guildMemberStore.loading)
const teamLoading = ref(false)
const showTeamDialog = ref(false)
const allMembers = ref([])
const teams = ref([])
const { getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()

useGuildPageMotion(pageRef)

const teamForm = reactive({
  team_name: ''
})

function getClassStyle(className) {
  return getGuildClassStyle(className)
}

function syncMembersFromCache(list = guildMemberStore.members) {
  const currentRows = new Map(allMembers.value.map(row => [row.member_id, row]))
  allMembers.value = (list || []).map(member => {
    const current = currentRows.get(member.member_id)
    return {
      ...member,
      squad_number: current?.squad_number || member.squad_number || 1
    }
  })
}

function emitMemberDataChanged() {
  window.dispatchEvent(new CustomEvent('guild-member-data-changed', {
    detail: { membersAlreadyRefreshed: true }
  }))
}

async function fetchMembers(options = {}) {
  try {
    const list = await guildMemberStore.load({
      force: options.force === true,
      silent: options.silent === true
    })
    syncMembersFromCache(list)
  } catch {
    ElMessage.error('加载成员列表失败')
  }
}

async function fetchTeams() {
  try {
    const res = await getTeams()
    teams.value = res.data || []
  } catch {
    ElMessage.error('加载团队列表失败')
  }
}

async function fetchClassColors() {
  try {
    await loadGuildClassColors()
  } catch {
    // 静默处理
  }
}

function openTeamDialog() {
  teamForm.team_name = ''
  showTeamDialog.value = true
}

async function handleAddTeam() {
  if (!teamForm.team_name.trim()) {
    ElMessage.warning('请输入团队名称')
    return
  }
  teamLoading.value = true
  try {
    await addTeam({
      team_name: teamForm.team_name.trim()
    })
    ElMessage.success('添加团队成功')
    showTeamDialog.value = false
    await fetchTeams()
  } catch {
    ElMessage.error('添加团队失败')
  } finally {
    teamLoading.value = false
  }
}

async function handleDeleteTeam(team) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${team.team_name}」吗？删除后该团队成员分配将被清空。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteTeam(team.id)
    ElMessage.success('删除成功')
    await fetchTeams()
    await fetchMembers({ force: true })
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除团队失败')
    }
  }
}

async function onTeamChange(row, teamId) {
  try {
    const newTeamId = teamId || 0
    await editMember({
      member_id: row.member_id,
      team_id: newTeamId
    })
    row.team_id = newTeamId
    ElMessage.success('团队分配已更新')
    await guildMemberStore.refresh({ silent: true })
    emitMemberDataChanged()
  } catch {
    ElMessage.error('更新团队分配失败')
  }
}

async function onSquadBlur(row) {
  if (!row.team_id || row.team_id === 0) {
    return
  }
  const squadCount = allMembers.value.filter(
    m => m.team_id === row.team_id && m.squad_number === row.squad_number && m.member_id !== row.member_id
  ).length
  if (squadCount >= 6) {
    ElMessage.warning('每个队伍位置最多容纳 6 人')
    return
  }
  try {
    await editMember({
      member_id: row.member_id,
      squad_number: row.squad_number
    })
    ElMessage.success('队内序号已更新')
    await guildMemberStore.refresh({ silent: true })
    emitMemberDataChanged()
  } catch {
    ElMessage.error('更新队内序号失败')
  }
}

onMounted(() => {
  fetchMembers({ silent: guildMemberStore.hasReadyCache })
  fetchTeams()
  fetchClassColors()
})

watch(
  () => guildMemberStore.members,
  list => syncMembersFromCache(list),
  { immediate: true }
)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.team-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.class-tag {
  display: inline-block;
  padding: 2px 8px;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  background: var(--el-fill-color-light);
}
</style>
