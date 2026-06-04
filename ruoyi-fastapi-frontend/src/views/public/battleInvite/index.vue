<template>
  <div class="public-battle-page">
    <main class="public-shell">
      <section class="invite-summary">
        <div>
          <span class="eyebrow">{{ invite.guild_name || '帮会约战' }}</span>
          <h1>{{ invite.battle_name || '约战报名' }}</h1>
          <p>{{ invite.remark || '选择入会申请或约战报名，提交后等待管理员审核。' }}</p>
        </div>
        <div class="summary-meta">
          <span>约战时间：{{ formatDateTime(invite.battle_time) }}</span>
          <span>链接有效至：{{ formatDateTime(invite.expire_time) }}</span>
        </div>
      </section>

      <el-alert v-if="pageError" type="error" :closable="false" :title="pageError" class="page-alert" />

      <el-card v-else shadow="never" class="action-card">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="申请加入帮会" name="join">
            <el-form ref="joinFormRef" :model="joinForm" :rules="joinRules" label-width="96px">
              <el-form-item label="玩家名" prop="player_name">
                <el-input v-model="joinForm.player_name" placeholder="请输入游戏内角色名" maxlength="30" />
              </el-form-item>
              <el-form-item label="主职业">
                <el-select v-model="joinForm.player_class" placeholder="请选择主职业" clearable filterable style="width: 100%">
                  <el-option
                    v-for="item in professionOptions"
                    :key="item.professionId"
                    :label="item.professionName"
                    :value="item.professionName"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="副职">
                <el-input v-model="joinForm.secondary_class" placeholder="可选" maxlength="20" />
              </el-form-item>
              <el-form-item label="申请人">
                <el-input v-model="joinForm.applicant_name" placeholder="称呼，可选" maxlength="50" />
              </el-form-item>
              <el-form-item label="联系方式">
                <el-input v-model="joinForm.applicant_contact" placeholder="QQ、微信或其他联系方式，可选" maxlength="100" />
              </el-form-item>
              <el-form-item label="备注">
                <el-input v-model="joinForm.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="joinLoading" @click="submitJoin">提交入会申请</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="约战报名" name="signup">
            <el-input
              v-model="memberKeyword"
              placeholder="输入帮会内成员名字后自动搜索"
              clearable
              class="member-search"
            />

            <el-table
              v-loading="memberLoading"
              :data="memberList"
              border
              stripe
              class="member-table"
              highlight-current-row
              @current-change="handleMemberSelect"
            >
              <el-table-column prop="player_name" label="玩家名" min-width="120" />
              <el-table-column prop="player_class" label="主职业" width="100" />
              <el-table-column prop="secondary_class" label="副职" width="100" />
              <el-table-column prop="role_in_guild" label="帮会身份" width="110" />
              <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
              <template #empty>
                <el-empty :description="memberKeyword ? '没有匹配的帮会成员' : '输入名字搜索帮会成员'" />
              </template>
            </el-table>

            <el-form :model="signupForm" label-width="96px" class="signup-form">
              <el-form-item label="已选择">
                <el-input :model-value="selectedMember?.player_name || ''" placeholder="请先选择成员" disabled />
              </el-form-item>
              <el-form-item label="报名职业">
                <el-select
                  v-model="signupForm.player_class"
                  placeholder="可临时调整本次约战职业"
                  clearable
                  filterable
                  style="width: 100%"
                >
                  <el-option
                    v-for="item in professionOptions"
                    :key="item.professionId"
                    :label="item.professionName"
                    :value="item.professionName"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="报名副职">
                <el-input v-model="signupForm.secondary_class" placeholder="可临时调整本次约战副职" maxlength="20" />
              </el-form-item>
              <el-form-item label="报名人">
                <el-input v-model="signupForm.applicant_name" placeholder="称呼，可选" maxlength="50" />
              </el-form-item>
              <el-form-item label="联系方式">
                <el-input v-model="signupForm.applicant_contact" placeholder="QQ、微信或其他联系方式，可选" maxlength="100" />
              </el-form-item>
              <el-form-item label="备注">
                <el-input v-model="signupForm.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :disabled="!selectedMember" :loading="signupLoading" @click="submitSignup">
                  确认报名
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </main>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getPublicBattleInvite,
  getPublicBattleProfessions,
  searchPublicBattleMembers,
  submitPublicBattleJoin,
  submitPublicBattleSignup
} from '@/api/guild/battle'

const route = useRoute()
const inviteCode = route.params.inviteCode
const invite = ref({})
const pageError = ref('')
const activeTab = ref('join')
const joinFormRef = ref(null)
const joinLoading = ref(false)
const signupLoading = ref(false)
const memberLoading = ref(false)
const memberKeyword = ref('')
const memberList = ref([])
const selectedMember = ref(null)
const professionOptions = ref([])
let searchTimer = null

const joinForm = reactive({
  player_name: '',
  player_class: '',
  secondary_class: '',
  applicant_name: '',
  applicant_contact: '',
  remark: ''
})

const signupForm = reactive({
  player_class: '',
  secondary_class: '',
  applicant_name: '',
  applicant_contact: '',
  remark: ''
})

const joinRules = {
  player_name: [{ required: true, message: '请输入玩家角色名', trigger: 'blur' }]
}

function formatDateTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString('zh-CN', { hour12: false })
}

async function fetchInvite() {
  try {
    const res = await getPublicBattleInvite(inviteCode)
    invite.value = res.data || {}
    if (invite.value.expired || invite.value.status === '1') {
      pageError.value = '链接已过期或已停用'
    }
  } catch (error) {
    pageError.value = error.message || '链接不可访问'
  }
}

async function fetchProfessions() {
  try {
    const res = await getPublicBattleProfessions(inviteCode)
    professionOptions.value = res.data || []
  } catch {
    professionOptions.value = []
  }
}

async function searchMembers() {
  const keyword = memberKeyword.value.trim()
  if (!keyword) {
    memberList.value = []
    selectedMember.value = null
    return
  }
  memberLoading.value = true
  try {
    const res = await searchPublicBattleMembers(inviteCode, keyword)
    memberList.value = res.data || []
    selectedMember.value = null
  } finally {
    memberLoading.value = false
  }
}

function handleMemberSelect(member) {
  selectedMember.value = member
  signupForm.player_class = member?.player_class || ''
  signupForm.secondary_class = member?.secondary_class || ''
}

async function submitJoin() {
  await joinFormRef.value?.validate()
  joinLoading.value = true
  try {
    await submitPublicBattleJoin(inviteCode, { ...joinForm })
    ElMessage.success('入会申请已提交，请等待审核')
    joinForm.player_name = ''
    joinForm.player_class = ''
    joinForm.secondary_class = ''
    joinForm.applicant_name = ''
    joinForm.applicant_contact = ''
    joinForm.remark = ''
  } finally {
    joinLoading.value = false
  }
}

async function submitSignup() {
  if (!selectedMember.value) return
  signupLoading.value = true
  try {
    await submitPublicBattleSignup(inviteCode, {
      member_id: selectedMember.value.member_id,
      ...signupForm
    })
    ElMessage.success('约战报名已提交，请等待审核')
    signupForm.player_class = ''
    signupForm.secondary_class = ''
    signupForm.applicant_name = ''
    signupForm.applicant_contact = ''
    signupForm.remark = ''
    selectedMember.value = null
    await searchMembers()
  } finally {
    signupLoading.value = false
  }
}

watch(memberKeyword, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(searchMembers, 300)
})

onMounted(() => {
  fetchInvite()
  fetchProfessions()
})

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})
</script>

<style scoped>
.public-battle-page {
  min-height: 100vh;
  background:
    linear-gradient(135deg, rgba(18, 42, 62, 0.88), rgba(13, 18, 28, 0.94)),
    url('@/assets/images/profile.jpg') center/cover;
  color: #f5f7fa;
  padding: 40px 16px;
}

.public-shell {
  max-width: 980px;
  margin: 0 auto;
}

.invite-summary {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
}

.invite-summary h1 {
  margin: 8px 0;
  font-size: 34px;
  font-weight: 700;
}

.invite-summary p {
  margin: 0;
  color: rgba(245, 247, 250, 0.78);
}

.eyebrow {
  color: #8cc5ff;
  font-size: 14px;
}

.summary-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 260px;
  color: rgba(245, 247, 250, 0.82);
}

.action-card {
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.page-alert {
  margin-top: 20px;
}

.member-search {
  margin-bottom: 12px;
}

.member-table,
.signup-form {
  margin-top: 14px;
}

@media (max-width: 760px) {
  .invite-summary,
  .summary-meta {
    flex-direction: column;
  }

  .invite-summary h1 {
    font-size: 28px;
  }
}
</style>
