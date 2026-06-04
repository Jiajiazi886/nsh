<template>
  <div class="app-container profile-edit-page" v-loading="loading">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div>
            <div class="title">个人信息编辑</div>
            <div class="subtitle">修改自己的主职业、副职和备注，保存后帮会成员信息会同步更新。</div>
          </div>
          <el-button type="primary" text @click="fetchProfile">刷新</el-button>
        </div>
      </template>

      <el-empty
        v-if="!profile"
        description="当前账号还没有加入帮会，暂无可编辑的帮会成员信息。"
      >
        <el-button type="primary" @click="goJoinGuild">去加入帮会</el-button>
      </el-empty>

      <template v-else>
        <el-descriptions :column="2" border class="profile-summary">
          <el-descriptions-item label="当前帮会">{{ profile.guild_name || '未命名帮会' }}</el-descriptions-item>
          <el-descriptions-item label="玩家名称">{{ profile.player_name || '--' }}</el-descriptions-item>
          <el-descriptions-item label="帮会身份">{{ profile.role_in_guild || '成员' }}</el-descriptions-item>
          <el-descriptions-item label="加入时间">{{ formatDateTime(profile.join_time) }}</el-descriptions-item>
        </el-descriptions>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="90px"
          class="profile-form"
        >
          <el-form-item label="主职业" prop="player_class">
            <el-select
              v-model="form.player_class"
              clearable
              filterable
              placeholder="请选择主职业"
              style="width: 100%"
            >
              <el-option
                v-for="item in professionOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="副职" prop="secondary_class">
            <el-select
              v-model="form.secondary_class"
              clearable
              filterable
              placeholder="请选择副职"
              style="width: 100%"
            >
              <el-option
                v-for="item in secondaryProfessionOptions"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="备注" prop="remark">
            <el-input
              v-model.trim="form.remark"
              type="textarea"
              :rows="4"
              maxlength="500"
              show-word-limit
              placeholder="填写你的补充说明，例如常用流派、出勤时间或管理备注"
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMyMemberProfile, updateMyMemberProfile } from '@/api/guild/member'
import { getProfessionOptions } from '@/api/guild/profession'

const DEFAULT_PROFESSIONS = ['九灵', '沧澜', '潮光', '玄机', '碎梦', '神相', '素问', '血河', '铁衣', '鸿音', '龙吟']

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const saving = ref(false)
const profile = ref(null)
const professionOptions = ref([...DEFAULT_PROFESSIONS])

const form = reactive({
  player_class: '',
  secondary_class: '',
  remark: ''
})

const rules = {
  player_class: [{ max: 20, message: '主职业不能超过20个字符', trigger: 'change' }],
  secondary_class: [{ max: 20, message: '副职不能超过20个字符', trigger: 'change' }],
  remark: [{ max: 500, message: '备注不能超过500个字符', trigger: 'blur' }]
}

const secondaryProfessionOptions = computed(() => {
  return professionOptions.value.filter(item => item !== form.player_class)
})

watch(
  () => form.player_class,
  value => {
    if (value && value === form.secondary_class) {
      form.secondary_class = ''
    }
  }
)

function fillForm(data) {
  form.player_class = data?.player_class || ''
  form.secondary_class = data?.secondary_class || ''
  form.remark = data?.remark || ''
}

function formatDateTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString('zh-CN', { hour12: false })
}

function notifyMemberDataChanged() {
  window.dispatchEvent(new CustomEvent('guild-member-data-changed'))
}

function goJoinGuild() {
  router.push('/personal/join')
}

function resetForm() {
  fillForm(profile.value)
}

async function fetchProfessionOptions() {
  try {
    const res = await getProfessionOptions()
    const rows = res.data || []
    const names = rows.map(item => item.professionName).filter(Boolean)
    professionOptions.value = Array.from(new Set([...names, ...DEFAULT_PROFESSIONS]))
  } catch {
    professionOptions.value = [...DEFAULT_PROFESSIONS]
  }
}

async function fetchProfile() {
  loading.value = true
  try {
    const res = await getMyMemberProfile()
    profile.value = res.data || null
    fillForm(profile.value)
  } catch {
    ElMessage.error('个人信息加载失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate()

  saving.value = true
  try {
    const res = await updateMyMemberProfile({
      player_class: form.player_class,
      secondary_class: form.secondary_class,
      remark: form.remark
    })
    const data = res.data || res
    ElMessage.success(data.msg || '保存成功')
    notifyMemberDataChanged()
    await fetchProfile()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchProfessionOptions()
  fetchProfile()
})
</script>

<style scoped>
.profile-edit-page {
  max-width: 960px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.profile-summary {
  margin-bottom: 22px;
}

.profile-form {
  max-width: 620px;
}

@media (max-width: 768px) {
  .profile-edit-page {
    max-width: none;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
