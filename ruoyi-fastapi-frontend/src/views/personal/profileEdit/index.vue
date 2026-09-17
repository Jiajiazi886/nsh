<template>
  <div class="player-center">
    <div class="center-heading">
      <h2>个人中心</h2>
      <Button variant="outline" size="sm" @click="openSecurity">修改登录密码</Button>
    </div>
    <p class="hint">维护你的游戏玩家资料，不需要先加入帮会。登录账号保持不变；微信号是手动填写的联系方式，不是微信绑定。</p>
    <p v-if="loading && !ready" class="hint" role="status">正在读取个人资料…</p>
    <p v-if="error" class="error" role="alert">{{ error }} <Button v-if="!ready" variant="outline" size="sm" @click="fetchProfile">重试</Button></p>
    <p v-if="success" class="success" role="status">{{ success }}</p>

    <form v-if="ready" class="form" @submit.prevent="save">
      <FieldGroup>
        <Field :data-invalid="!!fieldErrors.name">
          <FieldLabel for="player-name">名字</FieldLabel>
          <Input id="player-name" v-model="form.name" maxlength="30" placeholder="游戏玩家名" :aria-invalid="!!fieldErrors.name" @input="fieldErrors.name = ''" />
          <FieldError :errors="[fieldErrors.name]" />
        </Field>
        <Field :data-invalid="!!fieldErrors.playerUid">
          <FieldLabel for="player-uid">玩家 UID</FieldLabel>
          <Input id="player-uid" v-model="form.playerUid" maxlength="64" placeholder="游戏 UID，保留前导零" :aria-invalid="!!fieldErrors.playerUid" @input="fieldErrors.playerUid = ''" />
          <FieldDescription>按字符串保存，前导零不会丢失。</FieldDescription>
          <FieldError :errors="[fieldErrors.playerUid]" />
        </Field>
        <Field :data-invalid="!!fieldErrors.wechatId">
          <FieldLabel for="player-wechat">微信号</FieldLabel>
          <Input id="player-wechat" v-model="form.wechatId" maxlength="64" placeholder="仅本人及本帮会管理员／助手可见" :aria-invalid="!!fieldErrors.wechatId" @input="fieldErrors.wechatId = ''" />
          <FieldError :errors="[fieldErrors.wechatId]" />
        </Field>
        <Field orientation="horizontal" class="orange-weapon-field">
          <div>
            <FieldLabel for="orange-weapon">橙武</FieldLabel>
            <FieldDescription>拥有橙武（不影响报名限制）</FieldDescription>
          </div>
          <Switch id="orange-weapon" v-model="form.hasOrangeWeapon" />
        </Field>
        <Field>
          <FieldLabel>主职业</FieldLabel>
          <Select v-model="professionSelection">
            <SelectTrigger><SelectValue placeholder="可暂不设置"><ProfessionTag v-if="form.profession" :name="form.profession" /></SelectValue></SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="__unset__">暂不设置</SelectItem>
                <SelectItem v-for="profession in professions" :key="profession" :value="profession"><ProfessionTag :name="profession" /></SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <Field>
          <FieldLabel>副职</FieldLabel>
          <Select v-model="secondaryProfessionSelection">
            <SelectTrigger><SelectValue placeholder="可暂不设置"><ProfessionTag v-if="form.secondaryProfession" :name="form.secondaryProfession" /></SelectValue></SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="__unset__">暂不设置</SelectItem>
                <SelectItem v-for="profession in professions" :key="profession" :value="profession"><ProfessionTag :name="profession" /></SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <Field :data-invalid="!!fieldErrors.remark">
          <FieldLabel for="player-remark">备注</FieldLabel>
          <Textarea id="player-remark" v-model="form.remark" maxlength="500" rows="3" :aria-invalid="!!fieldErrors.remark" @input="fieldErrors.remark = ''" />
          <FieldDescription>{{ form.remark.length }} / 500</FieldDescription>
          <FieldError :errors="[fieldErrors.remark]" />
        </Field>
      </FieldGroup>

      <div class="form-actions">
        <Button type="submit" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</Button>
        <Button type="button" variant="outline" :disabled="saving" @click="reset">重置</Button>
        <Button type="button" variant="outline" :disabled="saving" @click="requestReload">重新读取</Button>
      </div>
    </form>
    <p v-if="ready" class="hint">保存会同步本人有效绑定成员的名字、主副职业和备注；历史阵容及战报不变。</p>

    <Dialog v-model:open="securityVisible">
      <DialogContent class="sm:max-w-[480px]" @close-auto-focus="closeSecurity">
        <DialogHeader>
          <DialogTitle>修改登录密码</DialogTitle>
          <DialogDescription>修改网页和小程序共用账号的登录密码。</DialogDescription>
        </DialogHeader>
        <AccountPasswordForm @close="securityVisible = false" />
      </DialogContent>
    </Dialog>

    <AlertDialog v-model:open="reloadConfirmVisible">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>重新读取个人资料</AlertDialogTitle>
          <AlertDialogDescription>重新读取会放弃当前未保存的填写内容，是否继续？</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>取消</AlertDialogCancel>
          <AlertDialogAction @click="confirmReload">重新读取</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { activityApi } from '@/api/activities'
import AccountPasswordForm from '@/components/AccountPasswordForm/index.vue'
import ProfessionTag from '@/components/ProfessionTag/index.vue'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { getToken } from '@/utils/auth'
import { loadGuildClassColors } from '@/utils/guildClassColor'
import useUserStore from '@/store/modules/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()
const securityVisible = ref(false)
const reloadConfirmVisible = ref(false)
const loading = ref(false)
const saving = ref(false)
const ready = ref(false)
const error = ref('')
const success = ref('')
const professions = ref([])
const empty = () => ({ name: '', playerUid: '', wechatId: '', hasOrangeWeapon: false, profession: '', secondaryProfession: '', remark: '' })
const form = reactive(empty())
const baseline = ref(empty())
const fieldErrors = reactive({ name: '', playerUid: '', wechatId: '', remark: '' })
const dirty = computed(() => JSON.stringify(form) !== JSON.stringify(baseline.value))
const professionSelection = computed({ get: () => form.profession || '__unset__', set: value => { form.profession = value === '__unset__' ? '' : value } })
const secondaryProfessionSelection = computed({ get: () => form.secondaryProfession || '__unset__', set: value => { form.secondaryProfession = value === '__unset__' ? '' : value } })
let generation = 0
let loadedToken = ''

function openSecurity() {
  router.replace({ path: route.path, query: { ...route.query, security: 'password' }, hash: route.hash })
}
function closeSecurity() {
  if (route.query.security === 'password') {
    const query = { ...route.query }
    delete query.security
    router.replace({ path: route.path, query, hash: route.hash })
  }
}
watch(() => route.query.security, value => { securityVisible.value = value === 'password' }, { immediate: true })

function clearFieldErrors() {
  Object.keys(fieldErrors).forEach(key => { fieldErrors[key] = '' })
}
function validateForm() {
  clearFieldErrors()
  const name = form.name.trim()
  if (!name) fieldErrors.name = '请输入名字'
  else if (name.length > 30) fieldErrors.name = '名字最多 30 字'
  if (form.playerUid.length > 64) fieldErrors.playerUid = 'UID 最多 64 字'
  if (form.wechatId.length > 64) fieldErrors.wechatId = '微信号最多 64 字'
  if (form.remark.length > 500) fieldErrors.remark = '备注最多 500 字'
  return !Object.values(fieldErrors).some(Boolean)
}

async function fetchProfile() {
  const current = ++generation
  const token = getToken()
  loading.value = true
  error.value = ''
  success.value = ''
  loadGuildClassColors(true)
  try {
    const [data, enabled] = await Promise.all([activityApi.playerProfile(), activityApi.activityProfessions()])
    if (current !== generation || getToken() !== token) return
    baseline.value = data
    Object.assign(form, data)
    professions.value = enabled
    loadedToken = token
    ready.value = true
    clearFieldErrors()
  } catch (loadError) {
    if (current === generation) error.value = loadError.message
  } finally {
    if (current === generation) loading.value = false
  }
}
function reset() {
  Object.assign(form, baseline.value)
  error.value = ''
  success.value = ''
  clearFieldErrors()
}
function requestReload() {
  if (dirty.value) reloadConfirmVisible.value = true
  else fetchProfile()
}
function confirmReload() {
  reloadConfirmVisible.value = false
  fetchProfile()
}
async function save() {
  if (saving.value || !validateForm()) return
  if (loadedToken !== getToken()) {
    error.value = '账号已切换，请重新读取个人资料'
    return
  }
  saving.value = true
  error.value = ''
  success.value = ''
  const token = getToken()
  const payload = { ...form, name: form.name.trim() }
  try {
    const data = await activityApi.savePlayerProfile(payload)
    if (getToken() !== token) return
    baseline.value = data
    Object.assign(form, data)
    window.dispatchEvent(new CustomEvent('guild-member-data-changed'))
    success.value = '玩家资料已保存，网页和小程序已共享。'
  } catch (saveError) {
    error.value = saveError.message + '；填写内容已保留，可重试保存。'
  } finally {
    saving.value = false
  }
}

watch(() => user.id, () => {
  generation++
  ready.value = false
  loadedToken = ''
  Object.assign(form, empty())
  baseline.value = empty()
  clearFieldErrors()
  if (getToken()) fetchProfile()
})
onMounted(fetchProfile)
</script>

<style scoped>
.player-center{min-height:70vh;max-width:760px;padding:20px;background:#fff;color:#253044}.center-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}.center-heading h2{margin:0;font-size:20px}.hint{font-size:13px;line-height:1.6;color:#647084}.form{max-width:600px;margin-top:20px}.form-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.orange-weapon-field{justify-content:space-between;border:1px solid #e1e5eb;border-radius:8px;padding:12px}.error,.success{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px;border:1px solid;border-radius:6px}.error{border-color:#efc3bd;background:#fff1ef;color:#a32626}.success{border-color:#b9dec7;background:#effaf3;color:#246b3b}
</style>
