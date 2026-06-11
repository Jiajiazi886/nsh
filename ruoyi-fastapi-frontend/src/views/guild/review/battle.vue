<template>
  <div class="app-container battle-review-page">
    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>创建报名链接</span>
            </div>
          </template>

          <el-form ref="inviteFormRef" :model="inviteForm" :rules="inviteRules" label-width="90px">
            <el-form-item label="约战名称" prop="battle_name">
              <el-input v-model="inviteForm.battle_name" placeholder="例如：周六据点约战" maxlength="100" />
            </el-form-item>
            <el-form-item label="约战时间">
              <el-date-picker
                v-model="inviteForm.battle_time"
                type="datetime"
                placeholder="选择约战时间"
                value-format="YYYY-MM-DDTHH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="有效期">
              <el-input-number v-model="inviteForm.expire_hours" :min="1" :max="720" controls-position="right" />
              <span class="unit-text">小时</span>
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="inviteForm.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="createLoading" @click="handleCreateInvite">生成链接</el-button>
              <el-button @click="resetInviteForm">重置</el-button>
            </el-form-item>
          </el-form>

          <el-alert v-if="latestUrl" type="success" :closable="false" class="link-alert">
            <div class="link-row">
              <span>{{ latestUrl }}</span>
              <el-button type="primary" link @click="copyText(latestUrl)">复制</el-button>
            </div>
          </el-alert>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>报名链接</span>
              <el-button text type="primary" :loading="inviteLoading" @click="fetchInvites">刷新</el-button>
            </div>
          </template>

          <el-table v-loading="inviteLoading" :data="inviteList" border stripe>
            <el-table-column prop="battle_name" label="约战名称" min-width="150" />
            <el-table-column prop="guild_name" label="帮会" min-width="130" />
            <el-table-column label="约战时间" min-width="160">
              <template #default="{ row }">{{ formatDateTime(row.battle_time) }}</template>
            </el-table-column>
            <el-table-column label="过期时间" min-width="160">
              <template #default="{ row }">{{ formatDateTime(row.expire_time) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="getInviteStatusType(row)">
                  {{ getInviteStatusText(row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="registration_count" label="报名人数" width="90" align="center" />
            <el-table-column prop="approved_count" label="通过人数" width="90" align="center" />
            <el-table-column label="操作" width="190" align="center" fixed="right">
              <template #default="{ row }">
                <el-button v-if="isActiveInvite(row)" link type="primary" @click="copyText(buildPublicUrl(row.public_path))">复制链接</el-button>
                <el-button
                  v-if="isActiveInvite(row)"
                  link
                  type="danger"
                  :loading="disableInviteId === row.invite_id"
                  @click="handleDisableInvite(row)"
                >
                  强制失效
                </el-button>
                <template v-else>
                  <el-button
                    link
                    type="danger"
                    :loading="deleteInviteId === row.invite_id"
                    @click="handleDeleteInvite(row)"
                  >
                    删除
                  </el-button>
                  <span class="muted-text">保留</span>
                </template>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无报名链接记录" />
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="review-card">
      <template #header>
        <div class="card-header">
          <div>
            <span>约战报名审核</span>
            <span class="header-tip">通过后会保留在约战报名表中，供约战排表使用。</span>
          </div>
          <div class="header-actions">
            <el-button
              type="primary"
              :disabled="!selectedRegistrations.length || !!bulkActionType"
              :loading="bulkActionType === 'approve'"
              @click="handleBatchReview('approve')"
            >
              批量通过
            </el-button>
            <el-button
              type="danger"
              plain
              :disabled="!selectedRegistrations.length || !!bulkActionType"
              :loading="bulkActionType === 'reject'"
              @click="handleBatchReview('reject')"
            >
              批量拒绝
            </el-button>
            <el-radio-group v-model="statusFilter" size="small" @change="fetchRegistrations">
              <el-radio-button label="0">待审核</el-radio-button>
              <el-radio-button label="1">已通过</el-radio-button>
              <el-radio-button label="2">已拒绝</el-radio-button>
              <el-radio-button label="">全部</el-radio-button>
            </el-radio-group>
            <el-button text type="primary" :loading="registrationLoading" @click="fetchRegistrations">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table
        ref="registrationTableRef"
        v-loading="registrationLoading"
        :data="registrationList"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" :selectable="isPendingRegistration" />
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="player_name" label="玩家名" min-width="120" />
        <el-table-column prop="player_class" label="主职业" width="100">
          <template #default="{ row }">
            <span class="class-tag" :style="getGuildClassStyle(row.player_class)">
              {{ row.player_class || '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="secondary_class" label="副职" width="100">
          <template #default="{ row }">
            <span v-if="row.secondary_class" class="class-tag" :style="getGuildClassStyle(row.secondary_class)">
              {{ row.secondary_class }}
            </span>
            <span v-else class="muted-text">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="role_in_guild" label="帮会身份" width="110" />
        <el-table-column prop="applicant_name" label="报名人" min-width="110" />
        <el-table-column prop="applicant_contact" label="联系方式" min-width="130" show-overflow-tooltip />
        <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.approval_status)">{{ getStatusText(row.approval_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="报名时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.apply_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <template v-if="row.approval_status === '0'">
              <el-button link type="primary" :loading="actionId === row.registration_id && actionType === 'approve'" @click="handleReview(row, 'approve')">通过</el-button>
              <el-button link type="danger" :loading="actionId === row.registration_id && actionType === 'reject'" @click="handleReview(row, 'reject')">拒绝</el-button>
            </template>
            <span v-else class="muted-text">已处理</span>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="当前没有约战报名记录" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  approveBattleRegistration,
  createBattleInvite,
  deleteBattleInvite,
  disableBattleInvite,
  getBattleInvites,
  getBattleRegistrations,
  rejectBattleRegistration
} from '@/api/guild/battle'
import { useGuildClassColors } from '@/utils/guildClassColor'

const inviteFormRef = ref(null)
const createLoading = ref(false)
const inviteLoading = ref(false)
const registrationLoading = ref(false)
const actionId = ref(null)
const actionType = ref('')
const bulkActionType = ref('')
const registrationTableRef = ref(null)
const disableInviteId = ref(null)
const deleteInviteId = ref(null)
const inviteList = ref([])
const registrationList = ref([])
const selectedRegistrations = ref([])
const latestUrl = ref('')
const statusFilter = ref('0')
const { getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()

const inviteForm = reactive({
  battle_name: '',
  battle_time: '',
  expire_hours: 24,
  remark: ''
})

const inviteRules = {
  battle_name: [{ required: true, message: '请输入约战名称', trigger: 'blur' }]
}

function buildPublicUrl(path) {
  return `${window.location.origin}${path}`
}

function formatDateTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString('zh-CN', { hour12: false })
}

function getStatusText(status) {
  return ({ 0: '待审核', 1: '已通过', 2: '已拒绝' })[status] || '未知'
}

function getStatusType(status) {
  return ({ 0: 'warning', 1: 'success', 2: 'danger' })[status] || 'info'
}

function isActiveInvite(row) {
  return !row.expired && row.status !== '1'
}

function getInviteStatusText(row) {
  if (row.expired) return '已过期'
  return row.status === '1' ? '已失效' : '当前生效'
}

function getInviteStatusType(row) {
  if (row.expired) return 'warning'
  return row.status === '1' ? 'info' : 'success'
}

function isPendingRegistration(row) {
  return row.approval_status === '0'
}

function handleSelectionChange(selection) {
  selectedRegistrations.value = selection
}

async function copyText(text) {
  await navigator.clipboard.writeText(text)
  ElMessage.success('链接已复制')
}

function resetInviteForm() {
  inviteForm.battle_name = ''
  inviteForm.battle_time = ''
  inviteForm.expire_hours = 24
  inviteForm.remark = ''
}

async function handleCreateInvite() {
  await inviteFormRef.value?.validate()
  createLoading.value = true
  try {
    const res = await createBattleInvite({ ...inviteForm })
    latestUrl.value = buildPublicUrl(res.data.public_path)
    ElMessage.success('报名链接已生成，旧的生效链接已自动失效')
    resetInviteForm()
    await fetchInvites()
    await fetchRegistrations()
  } finally {
    createLoading.value = false
  }
}

async function handleDisableInvite(row) {
  try {
    await ElMessageBox.confirm(
      `确认让「${row.battle_name || '未命名约战'}」的报名链接立即失效吗？`,
      '强制失效报名链接',
      {
        confirmButtonText: '强制失效',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
  disableInviteId.value = row.invite_id
  try {
    await disableBattleInvite(row.invite_id)
    ElMessage.success('报名链接已失效')
    await fetchInvites()
    await fetchRegistrations()
  } finally {
    disableInviteId.value = null
  }
}

async function handleDeleteInvite(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除「${row.battle_name || '未命名约战'}」的报名链接记录吗？删除后不会再显示在列表里。`,
      '删除报名链接',
      {
        confirmButtonText: '删除',
        cancelButtonText: '保留',
        type: 'warning'
      }
    )
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    throw error
  }
  deleteInviteId.value = row.invite_id
  try {
    await deleteBattleInvite(row.invite_id)
    ElMessage.success('报名链接记录已删除')
    await fetchInvites()
    await fetchRegistrations()
  } finally {
    deleteInviteId.value = null
  }
}

async function fetchInvites() {
  inviteLoading.value = true
  try {
    const res = await getBattleInvites()
    inviteList.value = res.data || []
  } finally {
    inviteLoading.value = false
  }
}

async function fetchRegistrations() {
  registrationLoading.value = true
  try {
    const params = statusFilter.value === '' ? {} : { status: statusFilter.value }
    const res = await getBattleRegistrations(params)
    registrationList.value = res.data || []
    selectedRegistrations.value = []
    registrationTableRef.value?.clearSelection?.()
  } finally {
    registrationLoading.value = false
  }
}

async function reviewRegistration(row, type, comment = '') {
  if (type === 'approve') {
    await approveBattleRegistration(row.registration_id, comment)
    return
  }
  await rejectBattleRegistration(row.registration_id, comment)
}

async function handleReview(row, type) {
  const isApprove = type === 'approve'
  const actionLabel = isApprove ? '通过' : '拒绝'
  const commentPlaceholder = isApprove ? '可填写排表备注' : '可填写拒绝原因'
  const { value } = await ElMessageBox.prompt(
    `确认${actionLabel} ${row.player_name} 的约战报名吗？`,
    `${actionLabel}约战报名`,
    {
      confirmButtonText: actionLabel,
      cancelButtonText: '取消',
      inputPlaceholder: commentPlaceholder,
      inputType: 'textarea'
    }
  )

  actionId.value = row.registration_id
  actionType.value = type
  try {
    await reviewRegistration(row, type, value || '')
    ElMessage.success(isApprove ? '约战报名已通过' : '已拒绝约战报名')
    await fetchRegistrations()
    await fetchInvites()
  } finally {
    actionId.value = null
    actionType.value = ''
  }
}

async function handleBatchReview(type) {
  const targets = selectedRegistrations.value.filter(isPendingRegistration)
  if (!targets.length) {
    ElMessage.warning('请先选择待审核的约战报名')
    return
  }

  const isApprove = type === 'approve'
  const actionLabel = isApprove ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(
      `确认批量${actionLabel}选中的 ${targets.length} 条约战报名吗？`,
      `批量${actionLabel}约战报名`,
      {
        confirmButtonText: `批量${actionLabel}`,
        cancelButtonText: '取消',
        type: isApprove ? 'success' : 'warning'
      }
    )

    bulkActionType.value = type
    await Promise.all(targets.map(row => reviewRegistration(row, type)))
    ElMessage.success(`已${actionLabel} ${targets.length} 条约战报名`)
    await fetchRegistrations()
    await fetchInvites()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      throw error
    }
  } finally {
    bulkActionType.value = ''
  }
}

onMounted(() => {
  fetchInvites()
  fetchRegistrations()
  loadGuildClassColors()
})
</script>

<style scoped>
.battle-review-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-tip,
.muted-text,
.unit-text {
  color: #909399;
}

.unit-text {
  margin-left: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.link-alert {
  margin-top: 12px;
}

.link-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  word-break: break-all;
}

.review-card {
  margin-top: 0;
}

.class-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  padding: 2px 8px;
  border: 1px solid currentColor;
  border-radius: 999px;
  background: var(--el-fill-color-light);
  font-size: 13px;
  font-weight: 700;
}

@media (max-width: 900px) {
  .card-header,
  .header-actions,
  .card-header > div {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
