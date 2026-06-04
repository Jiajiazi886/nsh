<template>
  <div class="app-container battle-review-page">
    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>创建约战链接</span>
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
              <span>临时链接</span>
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
                <el-tag :type="row.expired || row.status === '1' ? 'info' : 'success'">
                  {{ row.expired || row.status === '1' ? '已失效' : '可访问' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="approved_count" label="通过人数" width="90" align="center" />
            <el-table-column label="操作" width="120" align="center" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="copyText(buildPublicUrl(row.public_path))">复制链接</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="还没有创建约战链接" />
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

      <el-table v-loading="registrationLoading" :data="registrationList" border stripe>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="player_name" label="玩家名" min-width="120" />
        <el-table-column prop="player_class" label="主职业" width="100" />
        <el-table-column prop="secondary_class" label="副职" width="100" />
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
  getBattleInvites,
  getBattleRegistrations,
  rejectBattleRegistration
} from '@/api/guild/battle'

const inviteFormRef = ref(null)
const createLoading = ref(false)
const inviteLoading = ref(false)
const registrationLoading = ref(false)
const actionId = ref(null)
const actionType = ref('')
const inviteList = ref([])
const registrationList = ref([])
const latestUrl = ref('')
const statusFilter = ref('0')

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
    ElMessage.success('约战链接已生成')
    resetInviteForm()
    await fetchInvites()
  } finally {
    createLoading.value = false
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
  } finally {
    registrationLoading.value = false
  }
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
    if (isApprove) {
      await approveBattleRegistration(row.registration_id, value || '')
      ElMessage.success('约战报名已通过')
    } else {
      await rejectBattleRegistration(row.registration_id, value || '')
      ElMessage.success('已拒绝约战报名')
    }
    await fetchRegistrations()
    await fetchInvites()
  } finally {
    actionId.value = null
    actionType.value = ''
  }
}

onMounted(() => {
  fetchInvites()
  fetchRegistrations()
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

@media (max-width: 900px) {
  .card-header,
  .header-actions,
  .card-header > div {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
