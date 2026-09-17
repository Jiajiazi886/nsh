<template>
  <main class="activity-leave-page">
    <Card class="activity-leave-card">
      <CardHeader>
        <CardTitle>活动请假</CardTitle>
        <CardDescription v-if="activity">
          {{ activity.orgName }} · {{ activity.name }} · {{ formatTime(activity.startsAt) }}
        </CardDescription>
      </CardHeader>
      <CardContent class="activity-leave-content">
        <p v-if="loading" class="activity-leave-muted">正在读取活动…</p>
        <div v-else-if="error" class="activity-leave-error" role="alert">
          <p>{{ error }}</p>
          <Button variant="outline" @click="loadActivity">重试</Button>
        </div>
        <p v-if="success" class="activity-leave-success" role="status">{{ success }}</p>
        <template v-else-if="activity">
          <p v-if="activity.expired" class="activity-leave-error">该约战已经结束，不能再请假。</p>
          <template v-else>
            <label class="activity-leave-field">
              <span>搜索玩家名字</span>
              <Input v-model="keyword" maxlength="30" placeholder="输入自己的游戏名字" autocomplete="off" />
            </label>
            <p v-if="searching" class="activity-leave-muted">正在搜索…</p>
            <p v-else-if="keyword.trim() && !members.length" class="activity-leave-muted">没有找到匹配的帮会成员</p>
            <div v-else class="activity-leave-results">
              <button
                v-for="member in members"
                :key="member.memberId"
                type="button"
                class="activity-leave-member"
                :class="{ selected: selected?.memberId === member.memberId }"
                :disabled="member.hasLeft"
                @click="selected = member"
              >
                <span><strong>{{ member.name }}</strong><ProfessionTag :name="member.profession" /></span>
                <Badge variant="outline">{{ member.hasLeft ? '已请假' : '选择' }}</Badge>
              </button>
            </div>
            <div v-if="selected" class="activity-leave-submit">
              <p>请假成员：<strong>{{ selected.name }}</strong></p>
              <label class="activity-leave-field">
                <span>可选：请假说明</span>
                <Textarea v-model="remark" maxlength="200" placeholder="不填写也可以提交" />
              </label>
              <AlertDialog>
                <AlertDialogTrigger as-child>
                  <Button class="w-full" :disabled="submitting">请假</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>确认请假？</AlertDialogTitle>
                    <AlertDialogDescription>
                      提交后，{{ selected.name }} 会立即从当前活动阵容中移出。
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>取消</AlertDialogCancel>
                    <AlertDialogAction :disabled="submitting" @click="submitLeave">确认请假</AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </template>
        </template>
      </CardContent>
    </Card>
  </main>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { activityApi } from '@/api/activities'
import ProfessionTag from '@/components/ProfessionTag/index.vue'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

const route = useRoute()
const code = String(route.params.leaveCode || '')
const activity = ref(null)
const loading = ref(true)
const error = ref('')
const success = ref('')
const keyword = ref('')
const searching = ref(false)
const members = ref([])
const selected = ref(null)
const remark = ref('')
const submitting = ref(false)
let searchTimer
let searchGeneration = 0

function formatTime(value) {
  return value ? String(value).replace('T', ' ').slice(0, 16) : '时间未设置'
}

async function loadActivity() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    activity.value = await activityApi.activityLeaveInfo(code)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function searchMembers(value) {
  const generation = ++searchGeneration
  const query = value.trim()
  selected.value = null
  members.value = []
  if (!query) return
  searching.value = true
  try {
    const result = await activityApi.activityLeaveMembers(code, query)
    if (generation === searchGeneration) members.value = result
  } catch (e) {
    if (generation === searchGeneration) error.value = e.message
  } finally {
    if (generation === searchGeneration) searching.value = false
  }
}

watch(keyword, value => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => searchMembers(value), 250)
})

async function submitLeave(event) {
  event?.preventDefault?.()
  if (!selected.value || submitting.value) return
  submitting.value = true
  error.value = ''
  success.value = ''
  try {
    await activityApi.submitActivityLeave(code, { memberId: selected.value.memberId, remark: remark.value.trim() })
    const name = selected.value.name
    selected.value = null
    remark.value = ''
    await searchMembers(keyword.value)
    success.value = `${name} 已请假，并已从当前阵容移出。`
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

onMounted(loadActivity)
onBeforeUnmount(() => clearTimeout(searchTimer))
</script>

<style scoped>
.activity-leave-page{min-height:100vh;background:#f5f7fa;padding:24px 12px;color:#172033}.activity-leave-card{width:min(100%,520px);margin:0 auto;background:#fff}.activity-leave-content{display:grid;gap:16px}.activity-leave-field{display:grid;gap:7px;font-size:14px}.activity-leave-field>span{font-weight:600}.activity-leave-muted{margin:0;color:#6b7280;font-size:14px}.activity-leave-error,.activity-leave-success{border:1px solid;border-radius:8px;padding:12px}.activity-leave-error{border-color:#fecaca;background:#fff7f7;color:#b42318}.activity-leave-success{margin:0;border-color:#b9dec7;background:#effaf3;color:#246b3b}.activity-leave-results{display:grid;gap:8px}.activity-leave-member{display:flex;align-items:center;justify-content:space-between;width:100%;min-height:46px;padding:8px 10px;border:1px solid #d8dee8;border-radius:8px;background:#fff;text-align:left;cursor:pointer}.activity-leave-member>span{display:flex;align-items:center;gap:8px;min-width:0}.activity-leave-member.selected{border-color:#2563eb;background:#eff6ff}.activity-leave-member:disabled{cursor:not-allowed;opacity:.6}.activity-leave-submit{display:grid;gap:12px;border-top:1px solid #e5e7eb;padding-top:16px}.activity-leave-submit p{margin:0}@media(max-width:480px){.activity-leave-page{padding:12px 8px}.activity-leave-card{border-radius:10px}}
</style>
