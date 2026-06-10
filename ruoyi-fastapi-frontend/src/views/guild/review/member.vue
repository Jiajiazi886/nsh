<template>
  <div class="app-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>成员报名审核</span>
            <span class="header-tip">通过后自动进入成员管理，拒绝后不会写入成员表。</span>
          </div>
          <div class="header-actions">
            <el-button
              v-if="canApprove"
              type="primary"
              :disabled="!selectedApplications.length || !!bulkActionType"
              :loading="bulkActionType === 'approve'"
              @click="handleBatchReview('approve')"
            >
              批量同意
            </el-button>
            <el-button
              v-if="canReject"
              type="danger"
              plain
              :disabled="!selectedApplications.length || !!bulkActionType"
              :loading="bulkActionType === 'reject'"
              @click="handleBatchReview('reject')"
            >
              批量拒绝
            </el-button>
            <el-button type="primary" plain :loading="loading" @click="fetchPendingApplications">刷新</el-button>
          </div>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        title="当前列表仅展示待审核申请。大当家只会看到自己帮会的申请，管理员可查看全部。"
        class="page-alert"
      />

      <el-table
        ref="applicationTableRef"
        v-loading="loading"
        :data="applicationList"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column v-if="showActionColumn" type="selection" width="50" />
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="guild_name" label="目标帮会" min-width="140" />
        <el-table-column v-if="!isCommonRole" prop="applicant_user_name" label="申请账号" min-width="130" />
        <el-table-column v-if="!isCommonRole" prop="applicant_nick_name" label="申请人昵称" min-width="130" />
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
        <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default>
            <el-tag type="warning">待审核</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.apply_time) }}
          </template>
        </el-table-column>
        <el-table-column v-if="showActionColumn" label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              v-if="canApprove"
              link
              type="primary"
              :disabled="!!bulkActionType"
              :loading="actionLoadingId === row.application_id && actionType === 'approve'"
              @click="handleReview(row, 'approve')"
            >
              同意
            </el-button>
            <el-button
              v-if="canReject"
              link
              type="danger"
              :disabled="!!bulkActionType"
              :loading="actionLoadingId === row.application_id && actionType === 'reject'"
              @click="handleReview(row, 'reject')"
            >
              拒绝
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="当前没有待审核的入会申请" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  approveJoinApplication,
  getPendingJoinApplications,
  rejectJoinApplication
} from '@/api/guild/join'
import useUserStore from '@/store/modules/user'
import { useGuildClassColors } from '@/utils/guildClassColor'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const actionLoadingId = ref(null)
const actionType = ref('')
const bulkActionType = ref('')
const applicationTableRef = ref(null)
const applicationList = ref([])
const selectedApplications = ref([])
const { getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()
const canReviewByRole = computed(() => {
  const roles = userStore.roles || []
  return roles.includes('admin') || roles.includes('common')
})
const canApprove = computed(() => canReviewByRole.value)
const canReject = computed(() => canReviewByRole.value)
const showActionColumn = computed(() => canApprove.value || canReject.value)
const isCommonRole = computed(() => {
  const roles = userStore.roles || []
  return roles.includes('common') && !roles.includes('admin')
})

function formatDateTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString('zh-CN', { hour12: false })
}

function notifyMemberDataChanged() {
  window.dispatchEvent(new CustomEvent('guild-member-data-changed'))
}

function handleSelectionChange(selection) {
  selectedApplications.value = selection
}

async function fetchPendingApplications() {
  loading.value = true
  try {
    const res = await getPendingJoinApplications()
    applicationList.value = res.data || []
    selectedApplications.value = []
    applicationTableRef.value?.clearSelection?.()
  } finally {
    loading.value = false
  }
}

async function reviewApplication(row, type) {
  if (type === 'approve') {
    await approveJoinApplication(row.application_id)
    return
  }
  await rejectJoinApplication(row.application_id)
}

async function handleReview(row, type) {
  const isApprove = type === 'approve'
  const actionLabel = isApprove ? '同意' : '拒绝'
  const confirmText = isApprove
    ? `确认同意 ${row.player_name} 加入 ${row.guild_name} 吗？通过后会自动加入成员管理。`
    : `确认拒绝 ${row.player_name} 的入会申请吗？拒绝后不会进入成员管理。`

  try {
    await ElMessageBox.confirm(confirmText, `${actionLabel}申请`, {
      confirmButtonText: actionLabel,
      cancelButtonText: '取消',
      type: isApprove ? 'success' : 'warning'
    })

    actionLoadingId.value = row.application_id
    actionType.value = type

    await reviewApplication(row, type)
    ElMessage.success(isApprove ? '审核通过' : '已拒绝该申请')

    notifyMemberDataChanged()
    await fetchPendingApplications()
    if (isApprove) {
      await router.push('/guild/member')
    }
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      throw error
    }
  } finally {
    actionLoadingId.value = null
    actionType.value = ''
  }
}

async function handleBatchReview(type) {
  const targets = selectedApplications.value.slice()
  if (!targets.length) {
    ElMessage.warning('请先选择要审核的申请')
    return
  }

  const isApprove = type === 'approve'
  const actionLabel = isApprove ? '同意' : '拒绝'
  const confirmText = isApprove
    ? `确认同意选中的 ${targets.length} 条入会申请吗？通过后会自动加入成员管理。`
    : `确认拒绝选中的 ${targets.length} 条入会申请吗？拒绝后不会进入成员管理。`

  try {
    await ElMessageBox.confirm(confirmText, `批量${actionLabel}申请`, {
      confirmButtonText: `批量${actionLabel}`,
      cancelButtonText: '取消',
      type: isApprove ? 'success' : 'warning'
    })

    bulkActionType.value = type
    await Promise.all(targets.map(row => reviewApplication(row, type)))
    ElMessage.success(`已${actionLabel} ${targets.length} 条申请`)
    notifyMemberDataChanged()
    await fetchPendingApplications()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      throw error
    }
  } finally {
    bulkActionType.value = ''
  }
}

onMounted(() => {
  fetchPendingApplications()
  loadGuildClassColors()
})
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-tip {
  font-size: 13px;
  color: #909399;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-alert {
  margin-bottom: 16px;
}

.muted-text {
  color: var(--el-text-color-secondary);
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
</style>
