<template>
  <div class="app-container join-page" v-loading="pageLoading">
    <el-row :gutter="16">
      <el-col :span="24">
        <el-alert
          type="info"
          :closable="false"
          title="一个账号同一时间只能保有一个有效申请，或加入一个帮会。"
          description="申请通过后会自动进入帮会成员管理；主动退会后，才能再次申请其他帮会。"
        />
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>当前状态</span>
              <el-button text type="primary" @click="fetchStatus">刷新</el-button>
            </div>
          </template>

          <el-alert
            v-if="roleScope !== 'user'"
            type="warning"
            :closable="false"
            title="当前角色不走普通成员入会流程"
            :description="roleScope === 'common' ? '帮会大当家应在帮会管理中维护成员与审核申请。' : '超级管理员不受入会流程约束。'"
          />

          <template v-else-if="currentMembership">
            <el-result icon="success" title="你已加入帮会">
              <template #sub-title>
                <div class="status-summary">
                  <p>当前帮会：{{ currentMembership.guild_name || '未命名帮会' }}</p>
                  <p>玩家名：{{ currentMembership.player_name || '--' }}</p>
                  <p>加入时间：{{ formatDateTime(currentMembership.join_time) }}</p>
                </div>
              </template>
              <template #extra>
                <el-button
                  v-hasPermi="['personal:join:quit']"
                  type="danger"
                  :loading="quitLoading"
                  @click="handleQuitGuild"
                >
                  退出帮会
                </el-button>
              </template>
            </el-result>
          </template>

          <template v-else-if="currentApplication">
            <div class="status-block">
              <el-tag :type="getStatusTagType(currentApplication)" size="large">
                {{ getApplicationStatusText(currentApplication) }}
              </el-tag>

              <el-descriptions :column="1" border class="status-descriptions">
                <el-descriptions-item label="申请帮会">{{ currentApplication.guild_name || '--' }}</el-descriptions-item>
                <el-descriptions-item label="玩家名">{{ currentApplication.player_name || '--' }}</el-descriptions-item>
                <el-descriptions-item label="主职业">{{ currentApplication.player_class || '未填写' }}</el-descriptions-item>
                <el-descriptions-item label="副职">{{ currentApplication.secondary_class || '未填写' }}</el-descriptions-item>
                <el-descriptions-item label="备注">{{ currentApplication.remark || '无' }}</el-descriptions-item>
                <el-descriptions-item label="申请时间">{{ formatDateTime(currentApplication.apply_time) }}</el-descriptions-item>
              </el-descriptions>
            </div>
          </template>

          <el-empty
            v-else
            description="当前还没有有效申请，可先搜索目标帮会并提交入会资料。"
          />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>搜索并申请加入帮会</span>
            </div>
          </template>

          <el-alert
            v-if="roleScope !== 'user'"
            type="info"
            :closable="false"
            title="当前角色无需在此页面提交入会申请"
          />

          <template v-else>
            <el-alert
              v-if="!canSubmitApplication"
              type="warning"
              :closable="false"
              :title="lockReason"
              class="block-alert"
            />

            <div class="search-bar">
              <el-input
                v-model.trim="searchKeyword"
                placeholder="请输入帮会名称"
                clearable
                @keyup.enter="handleSearch"
              />
              <el-button
                type="primary"
                :loading="searchLoading"
                :disabled="!canSearch"
                @click="handleSearch"
              >
                搜索帮会
              </el-button>
            </div>

            <el-table
              v-if="searchResults.length"
              :data="searchResults"
              highlight-current-row
              border
              class="result-table"
              @current-change="handleCurrentGuildChange"
            >
              <el-table-column prop="guild_name" label="帮会名称" min-width="160" />
              <el-table-column prop="owner_user_name" label="会长账号" min-width="140" />
              <el-table-column label="操作" width="120" align="center">
                <template #default="{ row }">
                  <el-button link type="primary" @click="selectGuild(row)">选择</el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-empty
              v-else-if="searchExecuted"
              description="未搜索到匹配帮会，请确认名称后重试。"
            />

            <el-form
              ref="formRef"
              :model="joinForm"
              :rules="joinRules"
              label-width="88px"
              class="join-form"
            >
              <el-form-item label="目标帮会">
                <el-input :model-value="selectedGuild ? selectedGuild.guild_name : ''" placeholder="请先搜索并选择帮会" readonly />
              </el-form-item>
              <el-form-item label="玩家名" prop="player_name">
                <el-input
                  v-model.trim="joinForm.player_name"
                  maxlength="32"
                  show-word-limit
                  placeholder="请输入玩家角色名"
                />
              </el-form-item>
              <el-form-item label="主职业" prop="player_class">
                <el-select
                  v-model="joinForm.player_class"
                  clearable
                  filterable
                  placeholder="请选择主职业"
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in classOptions"
                    :key="item"
                    :label="item"
                    :value="item"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="副职" prop="secondary_class">
                <el-select
                  v-model="joinForm.secondary_class"
                  clearable
                  filterable
                  placeholder="请选择副职"
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in secondaryClassOptions"
                    :key="item"
                    :label="item"
                    :value="item"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="备注" prop="remark">
                <el-input
                  v-model.trim="joinForm.remark"
                  type="textarea"
                  :rows="4"
                  maxlength="200"
                  show-word-limit
                  placeholder="可填写补充说明"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="submitLoading"
                  :disabled="!canSubmitApplication || !selectedGuild"
                  @click="handleSubmit"
                >
                  申请加入
                </el-button>
              </el-form-item>
            </el-form>
          </template>
        </el-card>
      </el-col>

      <el-col :span="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header">
              <span>申请记录</span>
            </div>
          </template>

          <el-table v-if="applications.length" :data="applications" border>
            <el-table-column type="index" label="序号" width="60" />
            <el-table-column prop="guild_name" label="帮会名称" min-width="140" />
            <el-table-column prop="player_name" label="玩家名" min-width="120" />
            <el-table-column prop="player_class" label="主职业" width="100" />
            <el-table-column prop="secondary_class" label="副职" width="100" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row)">{{ getApplicationStatusText(row) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
            <el-table-column label="申请时间" min-width="170">
              <template #default="{ row }">
                {{ formatDateTime(row.apply_time) }}
              </template>
            </el-table-column>
            <el-table-column label="审核时间" min-width="170">
              <template #default="{ row }">
                {{ formatDateTime(row.review_time) }}
              </template>
            </el-table-column>
          </el-table>

          <el-empty
            v-else
            description="暂无申请记录"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import useUserStore from '@/store/modules/user'
import { getClassColors } from '@/api/guild/classColor'
import { getMyJoinStatus, quitGuild, searchGuilds, submitJoinApplication } from '@/api/guild/join'

const DEFAULT_CLASS_OPTIONS = ['九灵', '沧澜', '潮光', '玄机', '碎梦', '神相', '素问', '血河', '铁衣', '鸿音', '龙吟']

const userStore = useUserStore()

const pageLoading = ref(false)
const searchLoading = ref(false)
const submitLoading = ref(false)
const quitLoading = ref(false)
const searchKeyword = ref('')
const searchResults = ref([])
const searchExecuted = ref(false)
const selectedGuild = ref(null)
const currentMembership = ref(null)
const currentApplication = ref(null)
const applications = ref([])
const formRef = ref()
const classOptions = ref([...DEFAULT_CLASS_OPTIONS])

const joinForm = reactive({
  player_name: '',
  player_class: '',
  secondary_class: '',
  remark: ''
})

const joinRules = {
  player_name: [{ required: true, message: '请输入玩家角色名', trigger: 'blur' }]
}

const roleScope = computed(() => {
  const roles = userStore.roles || []
  if (roles.includes('admin')) return 'admin'
  if (roles.includes('common')) return 'common'
  return 'user'
})

const canSubmitApplication = computed(() => roleScope.value === 'user' && !currentMembership.value && !currentApplication.value)
const canSearch = computed(() => canSubmitApplication.value && !!searchKeyword.value.trim())
const secondaryClassOptions = computed(() => classOptions.value.filter(item => item !== joinForm.player_class))

const lockReason = computed(() => {
  if (currentMembership.value) {
    return '你已经加入帮会，需先主动退会后才能重新申请。'
  }
  if (currentApplication.value) {
    return '你已有待处理入会申请，暂不能重复提交。'
  }
  return '当前角色不能通过该页面提交入会申请。'
})

watch(
  () => joinForm.player_class,
  (value) => {
    if (value && value === joinForm.secondary_class) {
      joinForm.secondary_class = ''
    }
  }
)

function formatDateTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString('zh-CN', { hour12: false })
}

function getApplicationStatusText(application) {
  if (!application) return '--'
  if (application.del_flag === '1') return '已失效'
  if (application.review_status === '1') return '已通过'
  if (application.review_status === '2') return '已拒绝'
  return '待审核'
}

function getStatusTagType(application) {
  if (!application) return 'info'
  if (application.del_flag === '1') return 'info'
  if (application.review_status === '1') return 'success'
  if (application.review_status === '2') return 'danger'
  return 'warning'
}

function notifyMemberDataChanged() {
  window.dispatchEvent(new CustomEvent('guild-member-data-changed'))
}

function resetSearchState() {
  searchResults.value = []
  searchExecuted.value = false
  selectedGuild.value = null
}

function resetJoinForm() {
  joinForm.player_name = ''
  joinForm.player_class = ''
  joinForm.secondary_class = ''
  joinForm.remark = ''
}

function handleCurrentGuildChange(row) {
  selectedGuild.value = row || null
}

function selectGuild(row) {
  selectedGuild.value = row
}

function handleExternalGuildChange() {
  fetchStatus()
}

async function fetchClassOptions() {
  try {
    const res = await getClassColors()
    const data = res.data || res || []
    const merged = new Set(DEFAULT_CLASS_OPTIONS)
    ;(data || []).forEach(item => {
      if (item?.class_name) {
        merged.add(item.class_name)
      }
    })
    classOptions.value = Array.from(merged)
  } catch {
    classOptions.value = [...DEFAULT_CLASS_OPTIONS]
  }
}

async function fetchStatus() {
  pageLoading.value = true
  try {
    const res = await getMyJoinStatus()
    const data = res.data || {}
    currentMembership.value = data.current_membership || null
    currentApplication.value = data.current_application || null
    applications.value = data.applications || []
  } finally {
    pageLoading.value = false
  }
}

async function handleSearch() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    ElMessage.warning('请输入帮会名称')
    return
  }
  if (!canSubmitApplication.value) {
    ElMessage.warning(lockReason.value)
    return
  }

  searchLoading.value = true
  try {
    const res = await searchGuilds(keyword)
    searchResults.value = res.data || []
    searchExecuted.value = true
    selectedGuild.value = searchResults.value[0] || null
    if (!searchResults.value.length) {
      ElMessage.warning('未搜索到匹配帮会')
    }
  } finally {
    searchLoading.value = false
  }
}

async function handleSubmit() {
  if (!selectedGuild.value) {
    ElMessage.warning('请先选择目标帮会')
    return
  }
  if (!formRef.value) {
    return
  }

  await formRef.value.validate()

  submitLoading.value = true
  try {
    await submitJoinApplication({
      guild_id: selectedGuild.value.guild_id,
      player_name: joinForm.player_name.trim(),
      player_class: joinForm.player_class,
      secondary_class: joinForm.secondary_class,
      remark: joinForm.remark.trim()
    })
    ElMessage.success('申请已提交，等待审核')
    resetJoinForm()
    resetSearchState()
    searchKeyword.value = ''
    await fetchStatus()
  } finally {
    submitLoading.value = false
  }
}

async function handleQuitGuild() {
  const guildName = currentMembership.value?.guild_name || '当前帮会'
  try {
    await ElMessageBox.confirm(
      `退出 ${guildName} 后，你需要重新申请才能再次加入。是否继续？`,
      '第一次确认',
      {
        confirmButtonText: '继续退出',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await ElMessageBox.confirm(
      '退出后会立即删除你在当前帮会下的成员记录，此操作不可撤销。是否确认退会？',
      '第二次确认',
      {
        confirmButtonText: '确认退会',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    quitLoading.value = true
    await quitGuild()
    notifyMemberDataChanged()
    ElMessage.success('退会成功')
    await fetchStatus()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      throw error
    }
  } finally {
    quitLoading.value = false
  }
}

onMounted(() => {
  fetchStatus()
  fetchClassOptions()
  window.addEventListener('guild-member-data-changed', handleExternalGuildChange)
})

onBeforeUnmount(() => {
  window.removeEventListener('guild-member-data-changed', handleExternalGuildChange)
})
</script>

<style scoped lang="scss">
.join-page {
  .el-row {
    row-gap: 16px;
  }
}

.panel-card {
  min-height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-summary {
  text-align: left;
  line-height: 1.8;
}

.status-summary p {
  margin: 0;
}

.status-block {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-descriptions {
  margin-top: 4px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.result-table {
  margin-bottom: 16px;
}

.join-form {
  margin-top: 8px;
}

.block-alert {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .search-bar {
    flex-direction: column;
  }
}
</style>
