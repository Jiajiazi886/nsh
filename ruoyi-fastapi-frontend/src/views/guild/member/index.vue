<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>帮会成员管理（共 {{ totalCount }} 人）</span>
            <span class="class-summary">{{ classSummary }}</span>
          </div>
          <div class="header-actions">
            <el-button v-hasPermi="['guild:member:add']" type="primary" @click="openAddDialog">添加帮会成员</el-button>
            <el-button v-hasPermi="['guild:member:import']" type="primary" @click="openImportDialog">从历史数据导入</el-button>
            <el-button v-hasPermi="['guild:member:remove']" type="danger" @click="handleBatchDelete">批量删除</el-button>
          </div>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        class="page-alert"
        title="当前成员列表仅展示已审核通过且仍有效的成员。待审核或已拒绝的申请不会出现在这里。"
      />

      <div class="filter-bar">
        <el-button :type="showAll ? 'primary' : ''" size="small" @click="handleShowAll">显示全部</el-button>
        <el-checkbox-group v-model="selectedClasses" @change="onClassChange" class="class-checkboxes">
          <el-tooltip v-for="c in availableClasses" :key="c" :content="`${c}：${classCountMap[c] || 0} 人`" placement="top">
              <el-checkbox :label="c" :value="c" size="small">{{ c }}</el-checkbox>
            </el-tooltip>
        </el-checkbox-group>
      </div>

      <el-table :data="filteredMemberList" @selection-change="handleSelectionChange" v-loading="loading" border stripe>
        <el-table-column type="selection" width="50" />
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="player_name" label="玩家名" min-width="120" />
        <el-table-column prop="player_class" label="主职业" width="100">
          <template #default="scope">
            <el-dropdown
              trigger="click"
              :disabled="quickClassLoading || !hasEditPermission"
              @command="value => handleQuickClassChange(scope.row, 'player_class', value)"
            >
              <span
                class="class-tag editable-class-tag"
                :style="getClassStyle(scope.row.player_class)"
              >{{ scope.row.player_class || '未设置' }}</span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="">未设置</el-dropdown-item>
                  <el-dropdown-item v-for="c in classOptions" :key="c" :command="c">{{ c }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
        <el-table-column prop="secondary_class" label="副职" width="100">
          <template #default="scope">
            <el-dropdown
              trigger="click"
              :disabled="quickClassLoading || !hasEditPermission"
              @command="value => handleQuickClassChange(scope.row, 'secondary_class', value)"
            >
              <span
                class="class-tag editable-class-tag"
                :style="getClassStyle(scope.row.secondary_class)"
              >{{ scope.row.secondary_class || '未设置' }}</span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="">未设置</el-dropdown-item>
                  <el-dropdown-item v-for="c in classOptions" :key="c" :command="c">{{ c }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="来源" width="110" align="center">
          <template #default="scope">
            <el-tag :type="getSourceTagType(scope.row.source_type)">
              {{ getSourceLabel(scope.row.source_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="role_in_guild" label="帮会身份" width="100" />
        <el-table-column label="加入时间" min-width="170">
          <template #default="scope">
            {{ formatDateTime(scope.row.join_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="scope">
            <el-button
              v-hasPermi="['guild:member:edit']"
              type="primary"
              link
              size="small"
              @click="handleEdit(scope.row)"
            >
              编辑
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="当前没有已生效成员，可手动添加、从历史导入，或先到成员报名审核中通过申请。" />
        </template>
      </el-table>

      <el-dialog v-model="showAddDialog" title="添加帮会成员" width="500px">
        <el-form :model="addForm" label-width="80px">
          <el-form-item label="玩家名" required>
            <el-input v-model="addForm.player_name" placeholder="请输入玩家角色名" />
          </el-form-item>
          <el-form-item label="主职业">
            <el-select v-model="addForm.player_class" placeholder="请选择主职业" clearable style="width: 100%">
              <el-option v-for="c in classOptions" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
          <el-form-item label="副职">
            <el-select v-model="addForm.secondary_class" placeholder="请选择副职" clearable style="width: 100%">
              <el-option v-for="c in classOptions" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="addForm.remark" type="textarea" :rows="3" placeholder="请输入备注" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAdd" :loading="addLoading">确认添加</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showImportDialog" title="从历史数据导入成员" width="500px">
        <el-form label-width="100px">
          <el-form-item label="选择战斗">
            <el-select v-model="importForm.battle_id" placeholder="请选择历史战斗" @change="onBattleChange" style="width: 100%">
              <el-option v-for="b in battleList" :key="b.battle_id" :label="b.battle_name" :value="b.battle_id" />
            </el-select>
          </el-form-item>
          <el-form-item label="选择帮会">
            <el-select v-model="importForm.guild_name" placeholder="请选择帮会" :disabled="!importForm.battle_id" style="width: 100%">
              <el-option v-for="g in guildNames" :key="g" :label="g" :value="g" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showImportDialog = false">取消</el-button>
          <el-button type="primary" @click="handleImport" :disabled="!importForm.guild_name" :loading="importLoading">确认导入</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showEditDialog" title="编辑成员信息" width="500px">
        <el-form :model="editForm" label-width="80px">
          <el-form-item label="玩家名">
            <el-input :model-value="editForm.player_name" disabled />
          </el-form-item>
          <el-form-item label="主职业">
            <el-select v-model="editForm.player_class" placeholder="请选择主职业" clearable style="width: 100%">
              <el-option v-for="c in classOptions" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
          <el-form-item label="副职">
            <el-select v-model="editForm.secondary_class" placeholder="请选择副职" clearable style="width: 100%">
              <el-option v-for="c in classOptions" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="editForm.remark" type="textarea" :rows="3" placeholder="请输入备注" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSaveEdit" :loading="editLoading">保存</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMemberList, addMember, editMember, batchDeleteMembers, importFromBattle, getBattleListForImport, getBattleGuilds } from '@/api/guild/member'
import { getClassColors } from '@/api/guild/classColor'
import { checkPermi } from '@/utils/permission'

const loading = ref(false)
const memberList = ref([])
const selectedMembers = ref([])

const showAddDialog = ref(false)
const showImportDialog = ref(false)
const showEditDialog = ref(false)
const addLoading = ref(false)
const importLoading = ref(false)
const editLoading = ref(false)
const quickClassLoading = ref(false)

const battleList = ref([])
const guildNames = ref([])

const showAll = ref(true)
const selectedClasses = ref([])
const classColorMap = ref({})
const hasEditPermission = ref(checkPermi(['guild:member:edit']))

function getClassStyle(className) {
  if (!className) return {}
  const c = classColorMap.value[className]
  if (!c || c.bg_color === '#FFFFFF') return {}
  return {
    backgroundColor: c.bg_color,
    color: c.text_color,
  }
}

function getSourceLabel(sourceType) {
  if (sourceType === 'application') return '审核入会'
  if (sourceType === 'import') return '历史导入'
  return '手动添加'
}

function getSourceTagType(sourceType) {
  if (sourceType === 'application') return 'success'
  if (sourceType === 'import') return 'warning'
  return 'info'
}

function formatDateTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString('zh-CN', { hour12: false })
}

const addForm = reactive({
  player_name: '',
  player_class: '',
  secondary_class: '',
  remark: ''
})

const importForm = reactive({
  battle_id: null,
  guild_name: ''
})

const editForm = reactive({
  member_id: null,
  player_name: '',
  player_class: '',
  secondary_class: '',
  remark: ''
})

const classOptions = computed(() => {
  return Object.keys(classColorMap.value).sort()
})

const availableClasses = computed(() => {
  const classes = new Set()
  memberList.value.forEach(m => {
    if (m.player_class) classes.add(m.player_class)
  })
  return Array.from(classes).sort()
})

const totalCount = computed(() => memberList.value.length)

const classCountMap = computed(() => {
  const map = {}
  memberList.value.forEach(m => {
    if (m.player_class) {
      map[m.player_class] = (map[m.player_class] || 0) + 1
    }
  })
  return map
})

const classSummary = computed(() => {
  return availableClasses.value
    .map(c => `${c} ${classCountMap.value[c] || 0}`)
    .join(' | ')
})

const filteredMemberList = computed(() => {
  if (showAll.value || selectedClasses.value.length === 0) {
    return memberList.value
  }
  return memberList.value.filter(m => selectedClasses.value.includes(m.player_class))
})

function handleShowAll() {
  showAll.value = true
  selectedClasses.value = []
}

function onClassChange() {
  showAll.value = false
}

watch(showImportDialog, (val) => {
  if (val) {
    importForm.battle_id = null
    importForm.guild_name = ''
    guildNames.value = []
    fetchBattleList()
  }
})

function handleSelectionChange(selection) {
  selectedMembers.value = selection
}

async function fetchMemberList() {
  loading.value = true
  try {
    const res = await getMemberList()
    memberList.value = res.data || []
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleExternalMemberRefresh() {
  fetchMemberList()
}

async function fetchBattleList() {
  try {
    const res = await getBattleListForImport()
    battleList.value = res.data || []
  } catch {
    ElMessage.error('加载战斗列表失败')
  }
}

async function onBattleChange(battleId) {
  if (!battleId) {
    guildNames.value = []
    importForm.guild_name = ''
    return
  }
  try {
    const res = await getBattleGuilds(battleId)
    guildNames.value = res.data || []
  } catch {
    ElMessage.error('加载帮会列表失败')
  }
}

function openAddDialog() {
  addForm.player_name = ''
  addForm.player_class = ''
  addForm.secondary_class = ''
  addForm.remark = ''
  showAddDialog.value = true
}

async function handleAdd() {
  if (!addForm.player_name.trim()) {
    ElMessage.warning('请输入玩家名')
    return
  }
  addLoading.value = true
  try {
    const res = await addMember({
      player_name: addForm.player_name.trim(),
      player_class: addForm.player_class,
      secondary_class: addForm.secondary_class,
      remark: addForm.remark
    })
    const data = res.data || res
    ElMessage.success(data.msg || '添加成功')
    showAddDialog.value = false
    await fetchMemberList()
  } catch {
    ElMessage.error('添加失败')
  } finally {
    addLoading.value = false
  }
}

function openImportDialog() {
  showImportDialog.value = true
}

async function handleImport() {
  importLoading.value = true
  try {
    const res = await importFromBattle({ battle_id: importForm.battle_id, guild_name: importForm.guild_name })
    const data = res.data || res
    ElMessage.success(data.msg || '导入成功')
    showImportDialog.value = false
    await fetchMemberList()
  } catch {
    ElMessage.error('导入失败')
  } finally {
    importLoading.value = false
  }
}

function handleEdit(row) {
  editForm.member_id = row.member_id
  editForm.player_name = row.player_name
  editForm.player_class = row.player_class || ''
  editForm.secondary_class = row.secondary_class || ''
  editForm.remark = row.remark || ''
  showEditDialog.value = true
}

async function handleSaveEdit() {
  editLoading.value = true
  try {
    await editMember({
      member_id: editForm.member_id,
      player_class: editForm.player_class,
      secondary_class: editForm.secondary_class,
      remark: editForm.remark
    })
    ElMessage.success('保存成功')
    showEditDialog.value = false
    await fetchMemberList()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    editLoading.value = false
  }
}

async function handleQuickClassChange(row, field, value) {
  if (quickClassLoading.value || row[field] === value) {
    return
  }
  const oldValue = row[field]
  row[field] = value
  quickClassLoading.value = true
  try {
    await editMember({
      member_id: row.member_id,
      player_class: field === 'player_class' ? value : row.player_class,
      secondary_class: field === 'secondary_class' ? value : row.secondary_class,
      remark: row.remark || ''
    })
    ElMessage.success('保存成功')
  } catch {
    row[field] = oldValue
    ElMessage.error('保存失败')
  } finally {
    quickClassLoading.value = false
  }
}

async function handleBatchDelete() {
  if (selectedMembers.value.length === 0) {
    ElMessage.warning('请先选择要删除的成员')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedMembers.value.length} 条成员吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const ids = selectedMembers.value.map(m => m.member_id)
    const res = await batchDeleteMembers(ids)
    const data = res.data || res
    ElMessage.success(data.msg || '删除成功')
    await fetchMemberList()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function fetchClassColors() {
  try {
    const res = await getClassColors()
    const data = res.data || res
    const map = {}
    ;(data || []).forEach(item => { map[item.class_name] = item })
    classColorMap.value = map
  } catch {
    // 静默处理
  }
}

onMounted(() => {
  fetchMemberList()
  fetchClassColors()
  window.addEventListener('guild-member-data-changed', handleExternalMemberRefresh)
})

onBeforeUnmount(() => {
  window.removeEventListener('guild-member-data-changed', handleExternalMemberRefresh)
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.class-summary {
  font-size: 13px;
  color: #909399;
}

.page-alert {
  margin-bottom: 16px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.class-checkboxes {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.class-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
}

.editable-class-tag {
  cursor: pointer;
  min-width: 44px;
  text-align: center;
}

.editable-class-tag:hover {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}
</style>
