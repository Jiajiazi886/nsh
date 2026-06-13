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
          <el-tab-pane label="约战报名" name="signup">
            <div class="member-picker">
              <el-input
                v-model="memberKeyword"
                placeholder="输入帮会内成员名字后自动搜索"
                clearable
                class="member-search"
              />

              <div v-if="showMemberDropdown" class="member-dropdown">
                <div v-if="memberSearching" class="member-dropdown-status">搜索中...</div>
                <div v-else-if="!memberList.length" class="member-dropdown-status">没有匹配的帮会成员</div>
                <template v-else>
                  <button
                    v-for="member in memberList"
                    :key="member.member_id"
                    type="button"
                    class="member-option"
                    @click="handleMemberSelect(member)"
                  >
                    <span class="member-option-main">
                      <strong>{{ member.player_name }}</strong>
                      <span>{{ member.role_in_guild || '成员' }}</span>
                    </span>
                    <el-tag v-if="member.current_registration_type" class="member-state-tag" size="small" :type="member.current_registration_type === 'leave' ? 'warning' : 'success'">
                      {{ registrationTypeLabel(member.current_registration_type) }} · {{ registrationStatusLabel(member.current_registration_status) }}
                    </el-tag>
                    <span class="member-option-meta">
                      <span>主职业：{{ member.player_class || '未设置' }}</span>
                      <span>副职：{{ member.secondary_class || '未设置' }}</span>
                    </span>
                    <span v-if="member.remark" class="member-option-remark">{{ member.remark }}</span>
                  </button>
                </template>
              </div>
            </div>

            <el-form :model="signupForm" label-width="96px" class="signup-form">
              <el-alert
                class="mode-rule-alert"
                type="info"
                :closable="false"
                title="提交约战报名时，如果你当前已经请假，系统会自动取消请假申请。已报名时不能重复报名。"
              />
              <el-form-item label="已选择">
                <el-input :model-value="selectedMember?.player_name || ''" placeholder="请先选择成员" disabled />
              </el-form-item>
              <el-alert
                v-if="selectedHasRegistration"
                class="selected-state-alert"
                type="warning"
                :closable="false"
                :title="selectedRegistrationTip"
              />
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
              <el-form-item label="备注">
                <el-input v-model="signupForm.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :disabled="isSignupSubmitDisabled" :loading="signupLoading" @click="submitSignup">
                  确认报名
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="请假申请" name="leave">
            <div class="member-picker">
              <el-input
                v-model="memberKeyword"
                placeholder="输入帮会内成员名字后自动搜索"
                clearable
                class="member-search"
              />

              <div v-if="showMemberDropdown" class="member-dropdown">
                <div v-if="memberSearching" class="member-dropdown-status">搜索中...</div>
                <div v-else-if="!memberList.length" class="member-dropdown-status">没有匹配的帮会成员</div>
                <template v-else>
                  <button
                    v-for="member in memberList"
                    :key="member.member_id"
                    type="button"
                    class="member-option"
                    @click="handleMemberSelect(member)"
                  >
                    <span class="member-option-main">
                      <strong>{{ member.player_name }}</strong>
                      <span>{{ member.role_in_guild || '成员' }}</span>
                    </span>
                    <el-tag v-if="member.current_registration_type" class="member-state-tag" size="small" :type="member.current_registration_type === 'leave' ? 'warning' : 'success'">
                      {{ registrationTypeLabel(member.current_registration_type) }} · {{ registrationStatusLabel(member.current_registration_status) }}
                    </el-tag>
                    <span class="member-option-meta">
                      <span>主职业：{{ member.player_class || '未设置' }}</span>
                      <span>副职：{{ member.secondary_class || '未设置' }}</span>
                    </span>
                    <span v-if="member.remark" class="member-option-remark">{{ member.remark }}</span>
                  </button>
                </template>
              </div>
            </div>

            <el-form :model="leaveForm" label-width="96px" class="signup-form">
              <el-alert
                class="mode-rule-alert"
                type="info"
                :closable="false"
                title="提交请假申请时，如果你当前已经报名，系统会自动取消约战报名。已请假时不能重复请假。"
              />
              <el-form-item label="已选择">
                <el-input :model-value="selectedMember?.player_name || ''" placeholder="请先选择成员" disabled />
              </el-form-item>
              <el-alert
                v-if="selectedHasRegistration"
                class="selected-state-alert"
                type="warning"
                :closable="false"
                :title="selectedRegistrationTip"
              />
              <el-form-item label="请假说明">
                <el-input v-model="leaveForm.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
              </el-form-item>
              <el-form-item>
                <el-button type="warning" :disabled="isLeaveSubmitDisabled" :loading="leaveLoading" @click="submitLeave">
                  提交请假
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

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
        </el-tabs>
      </el-card>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getPublicBattleInvite,
  getPublicBattleProfessions,
  searchPublicBattleMembers,
  submitPublicBattleJoin,
  submitPublicBattleLeave,
  submitPublicBattleSignup
} from '@/api/guild/battle'

const route = useRoute()
const inviteCode = route.params.inviteCode
const invite = ref({})
const pageError = ref('')
const activeTab = ref('signup')
const joinFormRef = ref(null)
const joinLoading = ref(false)
const leaveLoading = ref(false)
const signupLoading = ref(false)
const memberLoading = ref(false)
const memberPending = ref(false)
const memberKeyword = ref('')
const memberList = ref([])
const selectedMember = ref(null)
const professionOptions = ref([])
let searchTimer = null

const showMemberDropdown = computed(() => memberKeyword.value.trim().length > 0 && !selectedMember.value)
const memberSearching = computed(() => memberPending.value || memberLoading.value)
const selectedRegistrationType = computed(() => selectedMember.value?.current_registration_type || '')
const selectedRegistrationLabel = computed(() => registrationTypeLabel(selectedRegistrationType.value))
const selectedHasRegistration = computed(() => Boolean(selectedRegistrationType.value))
const selectedRegistrationTip = computed(() => {
  if (!selectedHasRegistration.value) return ''
  const targetType = activeTab.value === 'leave' ? 'leave' : 'signup'
  const targetLabel = registrationTypeLabel(targetType)
  const currentStatus = registrationStatusLabel(selectedMember.value?.current_registration_status)
  if (selectedRegistrationType.value === targetType) {
    return `该成员已提交${selectedRegistrationLabel.value}，状态为${currentStatus}，不能重复提交。`
  }
  return `该成员当前是${selectedRegistrationLabel.value}，状态为${currentStatus}。提交${targetLabel}后，系统会自动取消${selectedRegistrationLabel.value}。`
})
const isSignupSubmitDisabled = computed(() => !selectedMember.value || selectedRegistrationType.value === 'signup')
const isLeaveSubmitDisabled = computed(() => !selectedMember.value || selectedRegistrationType.value === 'leave')

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
  remark: ''
})

const leaveForm = reactive({
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
    memberPending.value = false
    return
  }
  memberPending.value = false
  memberLoading.value = true
  try {
    const res = await searchPublicBattleMembers(inviteCode, keyword)
    memberList.value = res.data || []
    selectedMember.value = null
  } finally {
    memberLoading.value = false
  }
}

function registrationTypeLabel(type) {
  return type === 'leave' ? '请假申请' : '约战报名'
}

function registrationStatusLabel(status) {
  return { 0: '待审核', 1: '已通过', 2: '已拒绝' }[String(status)] || '未记录'
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
    const res = await submitPublicBattleSignup(inviteCode, {
      member_id: selectedMember.value.member_id,
      player_class: signupForm.player_class,
      secondary_class: signupForm.secondary_class,
      remark: signupForm.remark
    })
    ElMessage.success(res.msg || '约战报名已提交，请等待审核')
    signupForm.player_class = ''
    signupForm.secondary_class = ''
    signupForm.remark = ''
    clearMemberPicker()
  } finally {
    signupLoading.value = false
  }
}

async function submitLeave() {
  if (!selectedMember.value) return
  leaveLoading.value = true
  try {
    const res = await submitPublicBattleLeave(inviteCode, {
      member_id: selectedMember.value.member_id,
      remark: leaveForm.remark
    })
    ElMessage.success(res.msg || '请假申请已提交，请等待审核')
    leaveForm.remark = ''
    clearMemberPicker()
  } finally {
    leaveLoading.value = false
  }
}

function clearMemberPicker() {
  memberKeyword.value = ''
  memberList.value = []
  selectedMember.value = null
}

watch(memberKeyword, () => {
  if (searchTimer) clearTimeout(searchTimer)
  memberPending.value = memberKeyword.value.trim().length > 0
  searchTimer = setTimeout(searchMembers, 300)
})

watch(activeTab, () => {
  clearMemberPicker()
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

.member-picker {
  position: relative;
}

.member-search {
  margin-bottom: 0;
}

.member-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  z-index: 20;
  max-height: 268px;
  overflow: auto;
  padding: 8px;
  border: 1px solid rgba(38, 50, 69, 0.16);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.18);
}

.member-dropdown-status {
  padding: 14px 16px;
  color: #64748b;
  font-size: 14px;
}

.member-option {
  display: flex;
  width: 100%;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: #263245;
  text-align: left;
  cursor: pointer;
}

.member-option:hover {
  background: linear-gradient(90deg, rgba(105, 71, 242, 0.12), rgba(232, 215, 84, 0.16));
}

.member-option-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.member-option-main strong {
  font-size: 14px;
}

.member-option-main span {
  color: #6947f2;
  font-size: 12px;
}

.member-state-tag {
  align-self: flex-start;
}

.member-option-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  color: #64748b;
  font-size: 12px;
}

.member-option-remark {
  overflow: hidden;
  color: #526071;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.signup-form {
  margin-top: 14px;
}

.selected-state-alert {
  margin: 0 0 14px;
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
