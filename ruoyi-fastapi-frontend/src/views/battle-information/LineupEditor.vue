<template>
  <div v-if="draft" class="battle-page">
    <h2>{{ activity.name }} · 约战排表</h2>
    <div class="battle-toolbar">
      <Button variant="outline" :disabled="busy" @click="router.push('/battle-information/detail/' + activity.activityId)">查看活动</Button>
      <Button :disabled="busy" @click="save">{{ busy ? '保存中…' : '保存' }}</Button>
      <Button variant="outline" :disabled="busy" @click="refresh">重新读取后端</Button>
      <Button variant="outline" :disabled="busy" @click="addTeam">创建团队</Button>
      <Button variant="outline" :disabled="busy" @click="tempVisible = true">临时替补</Button>
      <Button variant="outline" :disabled="busy" @click="loadSnapshots">本活动快照</Button>
      <Button variant="outline" :disabled="busy" @click="templatesVisible = true">历史排表</Button>
      <Button v-if="activity.leavePath" variant="outline" :disabled="busy" @click="copyLeaveLink">复制请假链接</Button>
      <Button v-if="activity.leavePath" variant="outline" :disabled="busy" @click="loadLeaves">请假名单</Button>
      <Button v-if="org?.orgType === 'club' && org.role === 'owner'" variant="outline" @click="grantVisible = true">俱乐部成员授权</Button>
    </div>
    <p v-if="reuseNotice" class="battle-muted">{{ reuseNotice }}</p>
    <p v-if="feedback" class="battle-success" role="status">{{ feedback }}</p>
    <p class="battle-muted" role="status">{{ busy ? '正在保存到后端…' : draft.dirty ? '未提交后端 · ' + (persistedRevision === draft.localRevision ? '本地已保存' : '等待本地保存') : '已与后端同步' }}。每 10 秒只保存本地草稿；点击“保存”才更新成员可见阵容。</p>
    <p v-if="error" class="battle-error" role="alert">{{ error }}</p>
    <p v-if="localError" class="battle-error" role="alert">{{ localError }}；请勿关闭页面。<Button variant="outline" size="sm" @click="persist">重试本地保存</Button></p>

    <div class="battle-editor-grid">
      <aside class="battle-panel battle-candidates">
        <h3>候选玩家</h3>
        <Input v-model="keyword" placeholder="搜索玩家／职业" />
        <Accordion v-model="openProfession" type="single" collapsible class="battle-candidate-tree">
          <AccordionItem v-for="folder in folders" :key="folder.profession" :value="folder.profession">
            <AccordionTrigger>
              <span class="battle-candidate-folder"><ProfessionTag :name="folder.profession" /><strong>{{ folder.remaining }} / {{ folder.total }}</strong></span>
            </AccordionTrigger>
            <AccordionContent>
              <div v-for="player in folder.players" :key="playerKey(player)" class="battle-player" draggable="true" @dragstart="drag = player" @dragend="drag = null">
                <span class="truncate">{{ player.name }}{{ player.isTemporary ? '（临时）' : '' }}</span>
                <small>{{ placed.has(playerKey(player)) ? '已排' : '待排' }}</small>
                <Button v-if="activity.orgType === 'guild' && player.accountId" variant="ghost" size="xs" @click.stop="viewPrivateProfile(player)">资料</Button>
              </div>
              <p v-if="!folder.players.length" class="battle-muted">没有匹配的玩家</p>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
        <p v-if="!candidates.length" class="battle-muted">暂无组织成员，可先授权绑定成员或创建当前活动临时替补。</p>
      </aside>

      <div class="battle-teams">
        <article v-for="team in draft.teams" :key="team.id" class="battle-team">
          <header>
            <strong>{{ team.name }}</strong>
            <Button variant="ghost" size="xs" @click="rename(team)">改名</Button>
            <Button variant="ghost" size="xs" @click="toggleTeam(team.id)">{{ collapsed.has(team.id) ? '展开' : '收起' }}</Button>
            <Button variant="destructive" size="xs" @click="removeTeam(team)">删除</Button>
          </header>
          <div v-show="!collapsed.has(team.id)">
            <section v-for="squad in team.squads" :key="squad.id" class="battle-squad">
              <header>
                <strong>{{ squad.name }}</strong>
                <small>{{ squad.seats.filter(seat => seat.player).length }} / 6</small>
                <Button variant="ghost" size="xs" @click="rename(squad)">改名</Button>
                <Button variant="destructive" size="xs" @click="removeSquad(team, squad)">删除小队</Button>
              </header>
              <div class="battle-seats">
                <div
                  v-for="seat in squad.seats"
                  :key="seat.position"
                  class="battle-seat battle-edit-seat"
                  :class="{ 'battle-seat-empty': !seat.player }"
                  :data-squad-id="squad.id"
                  :data-position="seat.position"
                  @click="openSeatNotes(squad, seat)"
                  @dragover.prevent
                  @drop.prevent="drop(squad, seat)"
                >
                  <small :title="'位置 ' + seat.position">{{ seat.position }}</small>
                  <div
                    class="battle-occupant"
                    :data-member-id="seat.player?.memberId || seat.player?.temporaryId || ''"
                    :draggable="!!seat.player && !busy"
                    :title="seat.player?.name || '空缺：从候选区拖入'"
                    @click.stop="openSeatNotes(squad, seat)"
                    @dragstart="drag = seat.player"
                    @dragend="drag = null"
                  >
                    <strong>{{ seat.player?.name || '空缺' }}</strong>
                    <ProfessionTag v-if="seat.player" :name="seat.player.profession" />
                  </div>
                  <div v-if="seat.notes?.length" class="battle-seat-notes" :title="seat.notes.join('、')">{{ seat.notes.join(' · ') }}</div>
                  <Button v-if="seat.player" variant="destructive" size="xs" :disabled="busy" @click.stop="assign(squad.id, seat.position, null)">移出</Button>
                  <Select :model-value="seat.requiredProfession || '__any__'" :disabled="busy" @update:model-value="value => requirement(squad, seat, value === '__any__' ? '' : value)">
                    <SelectTrigger class="battle-seat-profession" @click.stop>
                      <SelectValue placeholder="不限职业"><ProfessionTag :name="seat.requiredProfession" /></SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="__any__"><ProfessionTag name="" /></SelectItem>
                        <SelectItem v-for="profession in professions" :key="profession" :value="profession"><ProfessionTag :name="profession" /></SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </section>
            <Button variant="ghost" :disabled="busy" @click="addSquad(team)">＋ 创建小队</Button>
          </div>
        </article>
      </div>
    </div>

    <Dialog v-model:open="privateVisible">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader><DialogTitle>本帮会成员玩家资料</DialogTitle><DialogDescription>仅本帮会管理员／助手可查看。</DialogDescription></DialogHeader>
        <p v-if="privateLoading" class="battle-muted" role="status">正在读取资料…</p>
        <p v-if="privateError" class="battle-error" role="alert">{{ privateError }}</p>
        <dl v-if="privateProfile" class="battle-profile-list">
          <div><dt>名字</dt><dd>{{ privateProfile.name }}</dd></div>
          <div><dt>玩家 UID</dt><dd>{{ privateProfile.playerUid || '未填写' }}</dd></div>
          <div><dt>微信号</dt><dd>{{ privateProfile.wechatId || '未填写' }}</dd></div>
          <div><dt>橙武</dt><dd>{{ privateProfile.hasOrangeWeapon ? '有' : '无' }}</dd></div>
          <div><dt>主职业</dt><dd><ProfessionTag :name="privateProfile.profession" /></dd></div>
          <div><dt>副职</dt><dd><ProfessionTag :name="privateProfile.secondaryProfession" /></dd></div>
        </dl>
        <DialogFooter><Button variant="outline" @click="privateVisible = false">关闭</Button></DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="notesVisible">
      <DialogContent class="sm:max-w-[520px]">
        <DialogHeader><DialogTitle>{{ seatNotesTitle }}</DialogTitle><DialogDescription>备注可以组合。保存阵容后，网页和小程序都会显示这些备注。</DialogDescription></DialogHeader>
        <div class="battle-note-options">
          <label v-for="note in allNotePresets" :key="note" :class="{ selected: seatNotes.includes(note) }"><input v-model="seatNotes" type="checkbox" :value="note">{{ note }}</label>
        </div>
        <div class="battle-note-preset-editor"><Input v-model="newNote" maxlength="20" placeholder="新增自定义预设" @keyup.enter="addNotePreset" /><Button variant="outline" size="sm" @click="addNotePreset">添加预设</Button></div>
        <div v-if="customNotePresets.length" class="battle-custom-note-list"><span v-for="note in customNotePresets" :key="note"><Badge variant="outline">{{ note }}</Badge><Button variant="ghost" size="icon-xs" :aria-label="'删除预设 ' + note" @click="removeNotePreset(note)">×</Button></span></div>
        <DialogFooter><Button variant="outline" @click="notesVisible = false">取消</Button><Button @click="saveSeatNotes">保存备注</Button></DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="tempVisible">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader><DialogTitle>当前活动临时替补</DialogTitle><DialogDescription>仅本活动有效，不进入帮会成员名册。</DialogDescription></DialogHeader>
        <FieldGroup>
          <Field><FieldLabel for="temp-player-name">玩家名称</FieldLabel><Input id="temp-player-name" v-model="tempName" maxlength="30" /></Field>
          <Field><FieldLabel>职业</FieldLabel><Select v-model="tempProfession"><SelectTrigger><SelectValue placeholder="选择职业"><ProfessionTag v-if="tempProfession" :name="tempProfession" /></SelectValue></SelectTrigger><SelectContent><SelectGroup><SelectItem v-for="profession in professions" :key="profession" :value="profession"><ProfessionTag :name="profession" /></SelectItem></SelectGroup></SelectContent></Select></Field>
        </FieldGroup>
        <DialogFooter><Button variant="outline" @click="tempVisible = false">取消</Button><Button @click="addTemporary">创建替补</Button></DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="snapshotsVisible">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader><DialogTitle>本活动历史快照</DialogTitle><DialogDescription>加载仅修改本地草稿，再次保存后才更新其他成员可见版本。</DialogDescription></DialogHeader>
        <div class="battle-dialog-list"><div v-for="snapshot in snapshots" :key="snapshot.snapshotId" class="battle-card"><span>版本 {{ snapshot.version }} · {{ snapshot.savedAt?.replace('T', ' ') }}</span><Button variant="ghost" size="sm" @click="applySnapshot(snapshot)">加载到草稿</Button></div><p v-if="!snapshots.length" class="battle-empty-note">暂无快照</p></div>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="templatesVisible">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader><DialogTitle>历史排表</DialogTitle><DialogDescription>新活动首次打开会默认沿用本组织最近一次保存的排表。临时替补和已请假／已离开组织的玩家不会带入。</DialogDescription></DialogHeader>
        <div class="battle-dialog-list"><div v-for="item in templates" :key="item.snapshotId" class="battle-card"><div><strong>{{ item.activityName }}</strong><p class="battle-muted">版本 {{ item.version }} · {{ formatDateTime(item.savedAt) }}</p></div><Button variant="ghost" size="sm" @click="applyTemplate(item)">使用此排表</Button></div><p v-if="!templates.length" class="battle-empty-note">暂无可复用排表</p></div>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="leavesVisible">
      <DialogContent class="sm:max-w-[560px]">
        <DialogHeader><DialogTitle>请假名单</DialogTitle><DialogDescription>成员通过活动请假链接提交；提交后会立即从当前阵容移出。</DialogDescription></DialogHeader>
        <div class="battle-dialog-list"><div v-for="item in leaves" :key="item.memberId" class="battle-card"><div><strong>{{ item.name }}</strong> <ProfessionTag :name="item.profession" /><p class="battle-muted">{{ formatDateTime(item.leftAt) }}<span v-if="item.remark"> · {{ item.remark }}</span></p></div></div><p v-if="!leaves.length" class="battle-empty-note">暂无成员请假</p></div>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="grantVisible">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader><DialogTitle>授权俱乐部成员</DialogTitle><DialogDescription>输入真实已绑定角色的成员 ID，不通过昵称绑定账号。</DialogDescription></DialogHeader>
        <FieldGroup>
          <Field><FieldLabel for="grant-member-id">成员 ID</FieldLabel><Input id="grant-member-id" v-model="grantId" /></Field>
          <Field><FieldLabel>角色</FieldLabel><Select v-model="grantRole"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectGroup><SelectItem value="member">成员</SelectItem><SelectItem value="assistant">助手</SelectItem></SelectGroup></SelectContent></Select></Field>
        </FieldGroup>
        <DialogFooter><Button variant="outline" @click="grantVisible = false">取消</Button><Button :disabled="busy" @click="grant">{{ busy ? '授权中…' : '确认授权' }}</Button></DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="promptVisible">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader><DialogTitle>{{ promptTitle }}</DialogTitle><DialogDescription>名称不能为空，最多 30 个字。</DialogDescription></DialogHeader>
        <Field :data-invalid="!!promptError"><FieldLabel for="lineup-name">名称</FieldLabel><Input id="lineup-name" v-model="promptValue" maxlength="30" autofocus @keyup.enter="submitPrompt" /><FieldError :errors="[promptError]" /></Field>
        <DialogFooter><Button variant="outline" @click="resolvePrompt(null)">取消</Button><Button @click="submitPrompt">确认</Button></DialogFooter>
      </DialogContent>
    </Dialog>

    <AlertDialog v-model:open="confirmVisible">
      <AlertDialogContent>
        <AlertDialogHeader><AlertDialogTitle>{{ confirmTitle }}</AlertDialogTitle><AlertDialogDescription>{{ confirmDescription }}</AlertDialogDescription></AlertDialogHeader>
        <AlertDialogFooter><AlertDialogCancel @click="resolveConfirm(false)">取消</AlertDialogCancel><AlertDialogAction :variant="confirmDestructive ? 'destructive' : 'default'" @click="resolveConfirm(true)">确认</AlertDialogAction></AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { activityApi } from '@/api/activities'
import ProfessionTag from '@/components/ProfessionTag/index.vue'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import useUserStore from '@/store/modules/user'
import { getToken } from '@/utils/auth'
import { loadGuildClassColors } from '@/utils/guildClassColor'
import { draftStorageKey, readScheduleDraft, writeScheduleDraft } from '@/views/guild/schedule/utils/scheduleDraftDb'
import { assignPlayer, changeDraft, clone, initialTeams, makeDraft, makeSquad, playerKey, professionFolders, setRequirement, setSeatNotes, toSaveRequest } from './model.mjs'
import './activity.css'

const props = defineProps({ activity: { type: Object, required: true } })
const emit = defineEmits(['saved', 'reload'])
const router = useRouter()
const user = useUserStore()
const draft = ref(null)
const candidates = ref([])
const busy = ref(false)
const error = ref('')
const feedback = ref('')
const localError = ref('')
const persistedRevision = ref(-1)
const keyword = ref('')
const drag = ref(null)
const collapsed = ref(new Set())
const org = ref(null)
const openProfession = ref('')
const tempVisible = ref(false)
const tempName = ref('')
const tempProfession = ref('')
const snapshotsVisible = ref(false)
const snapshots = ref([])
const templatesVisible = ref(false)
const templates = ref([])
const reuseNotice = ref('')
const leavesVisible = ref(false)
const leaves = ref([])
const grantVisible = ref(false)
const grantId = ref('')
const grantRole = ref('member')
const professions = ref([])
const privateVisible = ref(false)
const privateLoading = ref(false)
const privateProfile = ref(null)
const privateError = ref('')
const promptVisible = ref(false)
const promptTitle = ref('')
const promptValue = ref('')
const promptError = ref('')
const confirmVisible = ref(false)
const confirmTitle = ref('')
const confirmDescription = ref('')
const confirmDestructive = ref(false)
let promptResolver = null
let confirmResolver = null

const DEFAULT_NOTE_PRESETS = ['指挥', '保镖', '增益绝', '奶绝', '抗拆', '防守', '约定', '落霞', '击杀']
const notePresetStorageKey = `activity-seat-note-presets:${String(user.id || user.userId || 'anonymous')}`
const customNotePresets = ref(loadNotePresets())
const notesVisible = ref(false)
const seatNotes = ref([])
const noteTarget = ref(null)
const newNote = ref('')
const allNotePresets = computed(() => [...new Set([...DEFAULT_NOTE_PRESETS, ...customNotePresets.value])])
const seatNotesTitle = computed(() => noteTarget.value ? `${noteTarget.value.squadName} · 位置 ${noteTarget.value.position}备注` : '位置备注')
let privateGeneration = 0

async function viewPrivateProfile(player) {
  const current = ++privateGeneration
  privateVisible.value = true
  privateLoading.value = true
  privateProfile.value = null
  privateError.value = ''
  try {
    sameActor()
    const data = await activityApi.organizationPlayerProfile(props.activity.orgId, player.accountId)
    sameActor()
    if (current === privateGeneration) privateProfile.value = data
  } catch (loadError) {
    if (current === privateGeneration) privateError.value = loadError.message
  } finally {
    if (current === privateGeneration) privateLoading.value = false
  }
}

const owner = String(user.id || user.userId || '')
const sessionToken = getToken()
const storageKey = draftStorageKey(owner, props.activity.activityId, import.meta.env.VITE_APP_BASE_API)
const match = (players, query) => players.filter(player => !query.trim() || (player.name + ' ' + player.profession).toLowerCase().includes(query.trim().toLowerCase()))
const temporaryCandidates = computed(() => draft.value?.temporaryPlayers || [])
const allCandidates = computed(() => {
  const map = new Map([...candidates.value, ...temporaryCandidates.value, ...(draft.value?.teams || []).flatMap(team => team.squads).flatMap(squad => squad.seats).map(seat => seat.player).filter(player => player?.isTemporary)].map(player => [playerKey(player), player]))
  return [...map.values()]
})
const placed = computed(() => new Set((draft.value?.teams || []).flatMap(team => team.squads).flatMap(squad => squad.seats).map(seat => playerKey(seat.player)).filter(Boolean)))
const folders = computed(() => professionFolders(allCandidates.value).map(folder => ({
  ...folder,
  total: folder.players.length,
  remaining: folder.players.filter(player => !placed.value.has(playerKey(player))).length,
  players: match(folder.players, keyword.value),
})).filter(folder => folder.players.length || !keyword.value.trim()))
const id = prefix => prefix + '_' + crypto.randomUUID()
let interval
let active = true
let persisting = Promise.resolve()

function showError(message) {
  feedback.value = ''
  error.value = message
}
function showFeedback(message) {
  error.value = ''
  feedback.value = message
}
function toggleTeam(teamId) {
  const next = new Set(collapsed.value)
  if (next.has(teamId)) next.delete(teamId)
  else next.add(teamId)
  collapsed.value = next
}
function sameActor() {
  if (String(user.id) !== owner || getToken() !== sessionToken) throw Error('账号或会话已切换，请重新打开活动')
}
function ensure() {
  sameActor()
  if (busy.value) throw Error('正在提交，请稍后再编辑')
  if (draft.value?.pending) throw Error('上次提交结果尚未确认，请先再次保存或重新读取后端，不能修改待确认请求')
}
function change(fn) {
  try {
    ensure()
    draft.value = changeDraft(draft.value, fn)
    error.value = ''
  } catch (changeError) {
    showError(changeError.message)
  }
}
function assign(squadId, position, player) {
  try {
    ensure()
    draft.value = assignPlayer(draft.value, squadId, position, player)
    error.value = ''
    return true
  } catch (assignError) {
    showError(assignError.message)
    return false
  }
}
function requirement(squad, seat, profession) {
  try {
    ensure()
    draft.value = setRequirement(draft.value, squad.id, seat.position, profession)
    error.value = ''
  } catch (requirementError) {
    showError(requirementError.message)
  }
}
function loadNotePresets() {
  try {
    const value = JSON.parse(localStorage.getItem(notePresetStorageKey) || '[]')
    return Array.isArray(value) ? value.filter(item => typeof item === 'string' && item.trim()).slice(0, 30) : []
  } catch {
    return []
  }
}
function persistNotePresets() { localStorage.setItem(notePresetStorageKey, JSON.stringify(customNotePresets.value)) }
function openSeatNotes(squad, seat) {
  if (busy.value) return
  noteTarget.value = { squadId: squad.id, squadName: squad.name, position: seat.position }
  seatNotes.value = [...(seat.notes || [])]
  newNote.value = ''
  notesVisible.value = true
}
function addNotePreset() {
  const note = newNote.value.trim()
  if (!note) return
  if (DEFAULT_NOTE_PRESETS.includes(note) || customNotePresets.value.includes(note)) {
    newNote.value = ''
    return
  }
  customNotePresets.value = [...customNotePresets.value, note]
  persistNotePresets()
  newNote.value = ''
}
function removeNotePreset(note) {
  customNotePresets.value = customNotePresets.value.filter(item => item !== note)
  seatNotes.value = seatNotes.value.filter(item => item !== note)
  persistNotePresets()
}
function saveSeatNotes() {
  if (!noteTarget.value) return
  try {
    ensure()
    draft.value = setSeatNotes(draft.value, noteTarget.value.squadId, noteTarget.value.position, seatNotes.value)
    notesVisible.value = false
  } catch (saveError) {
    showError(saveError.message)
  }
}
function drop(squad, seat) {
  if (drag.value) assign(squad.id, seat.position, drag.value)
  drag.value = null
}

function promptName(title, initial = '') {
  promptTitle.value = title
  promptValue.value = initial
  promptError.value = ''
  promptVisible.value = true
  return new Promise(resolve => { promptResolver = resolve })
}
function resolvePrompt(value) {
  const resolver = promptResolver
  promptResolver = null
  promptVisible.value = false
  if (resolver) resolver(value)
}
function submitPrompt() {
  const value = promptValue.value.trim()
  if (!value) {
    promptError.value = '名称不能为空'
    return
  }
  resolvePrompt(value)
}
function askConfirm(description, title = '确认操作', destructive = false) {
  confirmTitle.value = title
  confirmDescription.value = description
  confirmDestructive.value = destructive
  confirmVisible.value = true
  return new Promise(resolve => { confirmResolver = resolve })
}
function resolveConfirm(value) {
  const resolver = confirmResolver
  confirmResolver = null
  confirmVisible.value = false
  if (resolver) resolver(value)
}
watch(promptVisible, value => { if (!value && promptResolver) resolvePrompt(null) })
watch(confirmVisible, value => { if (!value && confirmResolver) resolveConfirm(false) })

async function addTeam() {
  const name = await promptName('创建团队')
  if (name) change(teams => {
    if (teams.some(team => team.name === name)) throw Error('团队名称重复')
    teams.push({ id: id('team'), name, squads: [] })
  })
}
async function addSquad(team) {
  const name = await promptName('创建小队')
  if (name) change(teams => {
    const targetTeam = teams.find(item => item.id === team.id)
    if (targetTeam.squads.some(squad => squad.name === name)) throw Error('小队名称重复')
    targetTeam.squads.push(makeSquad(id('squad'), name))
  })
}
async function rename(row) {
  const name = await promptName('改名', row.name)
  if (name) change(teams => {
    const target = teams.find(team => team.id === row.id) || teams.flatMap(team => team.squads).find(squad => squad.id === row.id)
    target.name = name
  })
}
async function confirmDelete() { return askConfirm('移除后玩家回到候选区，只有保存后才更新其他成员阵容。', '确认删除', true) }
async function removeTeam(team) {
  if (await confirmDelete()) change(teams => teams.splice(teams.findIndex(item => item.id === team.id), 1))
}
async function removeSquad(team, squad) {
  if (await confirmDelete()) change(teams => {
    const targetTeam = teams.find(item => item.id === team.id)
    targetTeam.squads.splice(targetTeam.squads.findIndex(item => item.id === squad.id), 1)
  })
}
function addTemporary() {
  if (!tempName.value.trim() || !tempProfession.value) {
    showError('请填写姓名和职业')
    return
  }
  try {
    ensure()
    draft.value = changeDraft(draft.value, () => {})
    draft.value.temporaryPlayers = [...(draft.value.temporaryPlayers || []), { temporaryId: id('temp'), name: tempName.value.trim(), profession: tempProfession.value, isTemporary: true }]
    tempVisible.value = false
    tempName.value = ''
    tempProfession.value = ''
    error.value = ''
  } catch (temporaryError) {
    showError(temporaryError.message)
  }
}
function persist() {
  if (!draft.value) return Promise.resolve()
  const value = clone(draft.value)
  persisting = persisting.catch(() => {}).then(async () => {
    try {
      await writeScheduleDraft(storageKey, value)
      if (active) {
        persistedRevision.value = value.localRevision
        localError.value = ''
      }
    } catch (persistError) {
      if (active) localError.value = persistError.message
      throw persistError
    }
  })
  return persisting
}
function sanitizeTemplateTeams(value, players) {
  const allowed = new Set(players.map(playerKey))
  const teams = clone(value || [])
  for (const team of teams) for (const squad of team.squads || []) for (const seat of squad.seats || []) {
    if (seat.player && (seat.player.isTemporary || !allowed.has(playerKey(seat.player)))) seat.player = null
  }
  return teams
}
async function init() {
  try {
    const [stored, players, organizations, enabled, history] = await Promise.all([
      readScheduleDraft(storageKey),
      activityApi.activityProfiles(props.activity.orgId, props.activity.activityId),
      activityApi.organizations(),
      activityApi.activityProfessions(),
      activityApi.activityLineupTemplates(props.activity.orgId),
    ])
    if (!active) return
    org.value = organizations.find(item => item.orgId === props.activity.orgId)
    candidates.value = players
    professions.value = enabled
    templates.value = history
    const hasStored = stored?.activityId === props.activity.activityId && (stored.dirty || stored.pending)
    draft.value = hasStored ? stored : makeDraft(props.activity)
    if (stored?.dirty && stored.baseRevision !== props.activity.revision) error.value = '后端已更新，本地草稿保留；请重新读取或逐项确认后再保存，不会自动覆盖。'
    if (!hasStored && !props.activity.snapshot && !draft.value.teams.length && templates.value.length) {
      const latest = templates.value[0]
      draft.value = changeDraft(draft.value, teams => teams.push(...sanitizeTemplateTeams(latest.teams, players)))
      reuseNotice.value = `已默认沿用上次排表：${latest.activityName} · 版本 ${latest.version}，点击保存后才会提交。`
    }
    if (!draft.value.teams.length) draft.value = changeDraft(draft.value, teams => teams.push(...initialTeams(id('team'), id('squad'))))
    persistedRevision.value = stored?.localRevision ?? -1
  } catch (initError) {
    error.value = initError.message
    draft.value = null
  }
}
async function save() {
  if (busy.value || !draft.value) return
  busy.value = true
  error.value = ''
  feedback.value = ''
  try {
    sameActor()
    if (!draft.value.pending) draft.value.pending = toSaveRequest(draft.value, id('save'))
    await persist()
    sameActor()
    const result = await activityApi.saveLineup(props.activity.activityId, draft.value.pending)
    draft.value.baseRevision = result.revision
    draft.value.dirty = false
    draft.value.localRevision++
    delete draft.value.pending
    await persist()
    emit('saved', result)
    showFeedback('已保存，网页和小程序成员可查看此版本。')
  } catch (saveError) {
    if (saveError.status >= 400 && saveError.status !== 500 && saveError.status !== 503) delete draft.value.pending
    error.value = saveError.message + '；草稿已保留。网络异常时再次保存使用同一操作标识；版本冲突请重新读取后端确认。'
    try { await persist() } catch {}
  } finally {
    busy.value = false
  }
}
async function refresh() {
  if (busy.value) return
  if (!await askConfirm('将用后端已保存阵容替换当前本地草稿，未提交修改会丢失。', '重新读取后端', true)) return
  try {
    const nextActivity = await activityApi.activity(props.activity.activityId)
    draft.value = makeDraft(nextActivity)
    await persist()
    error.value = ''
    feedback.value = '已重新读取后端保存的阵容。'
    emit('saved', { revision: nextActivity.revision })
  } catch (refreshError) {
    error.value = refreshError.message
  }
}
async function loadSnapshots() {
  try {
    snapshots.value = await activityApi.activitySnapshots(props.activity.activityId)
    snapshotsVisible.value = true
  } catch (loadError) {
    error.value = loadError.message
  }
}
function formatDateTime(value) { return value ? String(value).replace('T', ' ').slice(0, 19) : '时间未知' }
async function copyLeaveLink() {
  try {
    const url = window.location.origin + props.activity.leavePath
    await navigator.clipboard.writeText(url)
    showFeedback('请假链接已复制。')
  } catch {
    showError('复制失败，请检查浏览器剪贴板权限')
  }
}
async function loadLeaves() {
  try {
    leaves.value = await activityApi.activityLeaves(props.activity.activityId)
    leavesVisible.value = true
  } catch (loadError) {
    error.value = loadError.message
  }
}
async function applySnapshot(snapshot) {
  if (!await askConfirm('用此版本替换本地草稿？不会立即修改后端。', '加载快照')) return
  change(teams => teams.splice(0, teams.length, ...clone(snapshot.teams)))
  snapshotsVisible.value = false
}
async function applyTemplate(item) {
  if (!await askConfirm(`使用“${item.activityName}”版本 ${item.version} 的排表？不会立即修改后端。`, '使用历史排表')) return
  change(teams => teams.splice(0, teams.length, ...sanitizeTemplateTeams(item.teams, candidates.value)))
  reuseNotice.value = `已加载历史排表：${item.activityName} · 版本 ${item.version}，点击保存后才会提交。`
  templatesVisible.value = false
}
async function grant() {
  busy.value = true
  try {
    await activityApi.grantOrganizationMember(props.activity.orgId, { memberId: grantId.value.trim(), role: grantRole.value })
    candidates.value = await activityApi.activityProfiles(props.activity.orgId, props.activity.activityId)
    grantVisible.value = false
    showFeedback('俱乐部成员授权已保存。')
  } catch (grantError) {
    error.value = grantError.message
  } finally {
    busy.value = false
  }
}
function unload(event) {
  if (busy.value || (draft.value?.dirty && persistedRevision.value !== draft.value.localRevision)) {
    event.preventDefault()
    event.returnValue = ''
  }
}

onMounted(() => {
  loadGuildClassColors(true)
  init()
  interval = setInterval(() => {
    if (!busy.value && draft.value?.dirty && persistedRevision.value !== draft.value.localRevision) persist().catch(() => {})
  }, 10000)
  window.addEventListener('beforeunload', unload)
})
onBeforeRouteLeave(async () => {
  if (busy.value) return false
  try {
    await persist()
    return true
  } catch {
    return askConfirm('本地保存失败，离开会丢失最新修改。仍然离开？', '草稿未保存', true)
  }
})
onBeforeUnmount(() => {
  active = false
  clearInterval(interval)
  window.removeEventListener('beforeunload', unload)
  persist().catch(() => {})
})
</script>

<style scoped>
.battle-success{margin:8px 0;padding:9px 12px;border:1px solid #b9dec7;border-radius:6px;background:#effaf3;color:#246b3b;font-size:13px}.battle-profile-list{display:grid;gap:0;border:1px solid #e1e5eb;border-radius:7px;overflow:hidden}.battle-profile-list div{display:grid;grid-template-columns:100px 1fr;border-bottom:1px solid #e8ebf0}.battle-profile-list div:last-child{border-bottom:0}.battle-profile-list dt,.battle-profile-list dd{margin:0;padding:9px 10px}.battle-profile-list dt{background:#f7f8fa;color:#5c6676}.battle-note-options{display:flex;flex-wrap:wrap;gap:8px}.battle-note-options label{cursor:pointer;border:1px solid #d8dde5;border-radius:6px;padding:6px 10px;font-size:13px}.battle-note-options label.selected{border-color:#2563eb;background:#eff6ff;color:#1d4ed8}.battle-note-options input{position:absolute;opacity:0;pointer-events:none}.battle-dialog-list{max-height:60vh;overflow:auto}.battle-seat-profession{height:26px;min-height:26px;padding:2px 6px;font-size:12px}
</style>
