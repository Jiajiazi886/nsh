<template>
  <div class="schedule-boxes" :class="{ 'is-preview': readonly }" v-loading="syncing || metadataLoading">
    <p v-if="loadError" class="save-error" role="alert">{{ loadError }} <el-button text @click="reloadWorkbook()">重试</el-button></p>
    <p v-if="localError" class="save-error" role="alert">{{ localError }} <el-button text @click="autosaver.flush(true)">重试本地保存</el-button></p>
    <p v-if="submitError" class="save-error" role="alert">提交失败：{{ submitError }}。草稿已保留，请确认后再次保存。</p>
    <div v-if="!readonly" class="draft-toolbar">
      <span class="draft-status" role="status" :class="{ pending: draft?.dirty }">{{ saveStatus }}</span>
      <span class="usage-hint">每 10 秒仅保存本地草稿；点击上方“保存”才提交后端。</span>
    </div>
    <div class="team-list">
      <article v-for="team in boxes" :key="team.team_id" class="team-box" :data-team-id="team.team_id">
        <header class="team-header">
          <div class="team-title"><strong>{{ team.team_name }}</strong><span>{{ team.count }} 人 · {{ team.squads.length }} 小队</span></div>
          <div class="box-tools">
            <button type="button" :aria-expanded="!collapsed.has(String(team.team_id))" @click.stop="toggleTeam(team)">{{ collapsed.has(String(team.team_id)) ? '展开 ▾' : '收起 ▴' }}</button>
            <button v-if="!readonly" type="button" class="danger" :disabled="locked" @click.stop="removeTeam(team)">删除</button>
          </div>
        </header>
        <div v-show="!collapsed.has(String(team.team_id))" class="team-body">
          <section v-for="squad in team.squads" :key="squad.squad_id" class="squad-box" :data-squad-id="squad.squad_id">
            <header class="squad-header"><div><strong>{{ squad.squad_name }}</strong><span>{{ squad.count }} / 6</span></div>
              <button v-if="!readonly" type="button" class="danger" :disabled="locked" @click="removeSquad(team, squad)">删除小队</button>
            </header>
            <div class="seat-grid">
              <div v-for="seat in squad.seats" :key="seat.orderNum" class="seat" :class="{ occupied: seat.member, 'drop-over': dropKey === `${squad.squad_id}:${seat.orderNum}` }" :data-seat="seat.orderNum"
                @dragover.prevent="markDrop(squad, seat)" @dragleave="dropKey = ''" @drop.prevent.stop="dropPlayer($event, team, squad, seat)">
                <span class="seat-number">位置 {{ seat.orderNum }}</span>
                <button type="button" class="seat-main" :disabled="readonly || locked" :draggable="!readonly && !!seat.member && !locked" @dragstart="dragPlayer($event, seat.member)" @dragend="endDrag" @click="openPicker(team, squad, seat)">
                  <template v-if="seat.member"><strong :title="seat.member.player_name">{{ seat.member.player_name }}</strong>
                    <span class="player-class" :style="getClassStyle(seat.member.player_class)">{{ seat.member.player_class || '未设置' }}</span>
                    <span v-if="seat.member.is_temporary" class="temporary-label">临时</span>
                  </template>
                  <span v-else class="empty-seat">＋ 选择玩家</span>
                </button>
                <button v-if="!readonly && seat.member" type="button" class="clear-seat" :disabled="locked" :aria-label="`移出${seat.member.player_name}`" @click.stop="clearPlayer(seat.member)">×</button>
              </div>
            </div>
            <div v-if="squad.overflow.length" class="compatibility">
              <p>旧排表存在超出六个位置或位置冲突的人员，已保留，请重新安排：</p>
              <details v-for="folder in groupPlayersByClass(squad.overflow)" :key="folder.className" open>
                <summary><span class="class-label" :style="getClassStyle(folder.className)">{{ folder.className }}</span> · {{ folder.members.length }} 人</summary>
                <div v-for="member in folder.members" :key="member.assignment_id || member.member_id" class="compat-player" :draggable="!readonly" @dragstart="dragPlayer($event, member)" @dragend="endDrag">
                  <span>{{ member.player_name }}</span><button v-if="!readonly" type="button" :disabled="locked" @click="clearPlayer(member)">移出排表</button>
                </div>
              </details>
            </div>
          </section>
          <el-empty v-if="!team.squads.length" :image-size="44" description="还没有小队" />
          <button v-if="!readonly" type="button" class="add-squad" :disabled="locked" @click="createSquad(team)">＋ 在该团队创建小队</button>
        </div>
      </article>
    </div>
    <el-empty v-if="!boxes.length && !metadataLoading" :image-size="70" :description="readonly ? '该历史没有团队' : '暂无团队，请点击上方“创建团队”'" />
    <section v-if="legacyPlayers.length" class="compatibility legacy-panel">
      <strong>旧表格未编队人员（{{ legacyPlayers.length }} 人，数据已保留）</strong>
      <p>原表格位置不再作为新排表位置。可拖入新小队，原 Excel 内容仍保留在历史兼容数据中。</p>
      <details v-for="folder in groupPlayersByClass(legacyPlayers)" :key="folder.className" open>
        <summary><span class="class-label" :style="getClassStyle(folder.className)">{{ folder.className }}</span> · {{ folder.members.length }} 人</summary>
        <div v-for="member in folder.members" :key="String(member.member_id)" class="compat-player" :draggable="!readonly" @dragstart="dragPlayer($event, member)" @dragend="endDrag"><span>{{ member.player_name }}{{ member.is_temporary ? '（临时）' : '' }}</span><small>{{ member.cellLabel }}</small></div>
      </details>
    </section>
    <el-dialog v-model="pickerVisible" title="选择玩家" width="460px" append-to-body>
      <el-input v-model="pickerKeyword" placeholder="搜索玩家或职业" clearable />
      <div class="picker-tree">
        <details v-for="folder in pickerFolders" :key="folder.className" :open="pickerExpanded.has(folder.className)" @toggle="togglePickerFolder(folder.className, $event)">
          <summary><span class="class-label" :style="getClassStyle(folder.className)">{{ folder.className }}</span> · {{ folder.members.length }} 人</summary>
          <button v-for="member in folder.members" :key="String(member.member_id)" type="button" class="picker-player" :disabled="locked" @click="choosePlayer(member)">
            <span>{{ member.player_name }}</span><small>{{ member.is_temporary ? '临时 · ' : '' }}{{ placedIds.has(String(member.member_id)) ? '已排，选择后移动/交换' : '待排' }}</small>
          </button>
        </details>
        <el-empty v-if="!pickerFolders.length" :image-size="50" description="暂无候选，可调整左侧搜索或审核筛选" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount, onActivated, onDeactivated } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as scheduleApi from '@/api/guild/schedule'
import {
  buildScheduleBoxes, collectLegacyMembers, groupPlayersByClass, readTempMembers,
  remapTempAssignments
} from '../utils/scheduleBoxes'
import {
  cloneDraft, createScheduleDraft, addDraftTeam, addDraftSquad, removeDraftStructure,
  assignDraftPlayer, clearDraftPlayer, upsertDraftTempMember, loadHistoryIntoDraft,
  createDraftAutosaver, scheduleFingerprint
} from '../utils/scheduleDraft'
import { draftStorageKey, readScheduleDraft, writeScheduleDraft } from '../utils/scheduleDraftDb'
import { syncScheduleDraft } from '../utils/scheduleDraftSync'

const props = defineProps({
  schedule: { type: Object, default: () => ({ teams: [] }) },
  members: { type: Array, default: () => [] }, draggingMember: { type: Object, default: null },
  getClassStyle: { type: Function, required: true },
  userId: { type: [String, Number], default: '' },
  readonly: { type: Boolean, default: false }, workbook: { type: Object, default: null }
})
const emit = defineEmits(['temp-members-change', 'workbook-assignments-change', 'busy-change', 'draft-schedule-change'])
const draft = ref(null)
const busy = ref(false)
const syncing = ref(false)
const metadataLoading = ref(false)
const loadError = ref('')
const localError = ref('')
const submitError = ref('')
const localRevision = ref(-1)
const localSavedAt = ref(0)
const collapsed = ref(new Set())
const internalDrag = ref(null)
const dropKey = ref('')
const pickerVisible = ref(false)
const pickerKeyword = ref('')
const pickerExpanded = ref(new Set())
const selectedSlot = ref(null)
let pendingAction = Promise.resolve(true)
let loadGeneration = 0
let pageActive = true
const activeSchedule = computed(() => props.readonly ? props.schedule : draft.value?.schedule || props.schedule)
const activeWorkbook = computed(() => props.readonly ? remapTempAssignments(props.workbook || {}, props.schedule) : draft.value?.workbook || {})
const boxes = computed(() => buildScheduleBoxes(activeSchedule.value, activeWorkbook.value))
const locked = computed(() => busy.value || syncing.value || metadataLoading.value || !!loadError.value || (!props.readonly && !draft.value))
const legacyPlayers = computed(() => collectLegacyMembers(activeWorkbook.value, activeSchedule.value))
const saveStatus = computed(() => {
  if (syncing.value) return '正在提交到后端…'
  if (!draft.value) return '正在读取草稿…'
  if (draft.value.syncPending) return '提交未完成，草稿已保留；请再次保存'
  if (!draft.value.dirty) return '已提交到后端'
  return localRevision.value === draft.value.revision
    ? `本地已保存 ${new Date(localSavedAt.value).toLocaleTimeString()} · 未提交后端`
    : '未提交 · 等待本地自动保存'
})
const autosaver = createDraftAutosaver({
  read: () => props.readonly || syncing.value ? null : draft.value,
  persist: value => writeScheduleDraft(value.storageKey, value),
  onSuccess: value => {
    if (value.storageKey !== draft.value?.storageKey) return
    localRevision.value = value.revision; localSavedAt.value = Date.now(); localError.value = ''
  },
  onError: error => { localError.value = `${error?.message || '本地保存失败'}。最新修改仍在内存中，请勿关闭页面。` }
})
const placedIds = computed(() => new Set(boxes.value.flatMap(team => team.squads.flatMap(squad =>
  [...squad.seats.map(seat => seat.member).filter(Boolean), ...squad.overflow])).map(member => String(member.member_id))))
const pickerFolders = computed(() => {
  const query = pickerKeyword.value.trim().toLowerCase()
  return groupPlayersByClass(props.members.filter(member => !query ||
    [member.player_name, member.player_class, member.secondary_class].some(value => String(value || '').toLowerCase().includes(query))))
})

watch([busy, syncing, metadataLoading], ([editing, saving, loading]) => { if (!props.readonly) emit('busy-change', editing || saving || loading) })
watch([() => props.schedule.schedule_id, () => props.userId], () => {
  if (!props.readonly && props.schedule.schedule_id && props.userId) reloadWorkbook()
  else if (!props.readonly) { ++loadGeneration; autosaver.stop(); draft.value = null }
}, { immediate: true })

function publishLocalState() {
  if (props.readonly) return
  if (!draft.value) return
  emit('draft-schedule-change', draft.value.schedule)
  emit('temp-members-change', readTempMembers(draft.value.workbook))
  const assignments = []
  boxes.value.forEach(team => team.squads.forEach(squad => squad.seats.forEach(seat => {
    if (seat.member?.is_temporary) assignments.push({ ...seat.member, teamName: team.team_name, squadName: squad.squad_name, cellLabel: `位置 ${seat.orderNum}` })
  })))
  emit('workbook-assignments-change', assignments)
}

async function reloadWorkbook(options = {}) {
  if (props.readonly) return true
  if (syncing.value || busy.value) return false
  autosaver.stop()
  if (draft.value && !(await autosaver.flush(true))) return false
  const generation = ++loadGeneration
  metadataLoading.value = true
  loadError.value = ''
  try {
    const scheduleId = props.schedule.schedule_id, userId = props.userId
    const storageKey = draftStorageKey(userId, scheduleId, import.meta.env.VITE_APP_BASE_API)
    const [scheduleRes, workbookRes, stored] = await Promise.all([
      options.initial ? Promise.resolve({ data: props.schedule }) : scheduleApi.getCurrentSchedule(),
      scheduleApi.getCurrentScheduleWorkbook(), readScheduleDraft(storageKey)
    ])
    if (generation !== loadGeneration) return false
    if (String(workbookRes.data?.schedule_id) !== String(scheduleId) || String(scheduleRes.data?.schedule_id) !== String(scheduleId)) throw Error('排表已变化，请刷新后重试')
    if (stored && (stored.version !== 1 || !Array.isArray(stored.schedule?.teams) || typeof stored.baseFingerprint !== 'string' || stored.storageKey !== storageKey)) throw Error('本地草稿格式损坏，未覆盖旧草稿，请联系维护者')
    const useStored = stored && (stored.dirty || stored.syncPending)
    draft.value = useStored ? stored : { ...createScheduleDraft(scheduleRes.data, workbookRes.data?.workbook || {}), storageKey }
    localRevision.value = useStored ? stored.revision : -1
    localSavedAt.value = stored?.localSavedAt || 0
    if (stored?.dirty && scheduleFingerprint(scheduleRes.data, workbookRes.data?.workbook || {}) !== (stored.expectedFingerprint || stored.baseFingerprint)) ElMessage.warning('后端已有变化，已保留你的本地草稿，保存时会再次确认')
    publishLocalState()
    if (pageActive) autosaver.start()
    return true
  } catch (error) {
    if (generation === loadGeneration) loadError.value = error?.message || '附加排表数据读取失败，请重试。为保护旧数据，暂时不能编辑。'
    return false
  } finally {
    if (generation === loadGeneration) metadataLoading.value = false
  }
}

function updateDraft(value) {
  draft.value = value
  publishLocalState()
}

function runAction(action, message) {
  if (props.readonly || locked.value) return Promise.resolve(false)
  busy.value = true
  pendingAction = (async () => {
    try { await action(); if (message) ElMessage.success(message); return true }
    catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error?.message || '操作失败，请刷新确认服务端状态'); return false }
    finally { busy.value = false; endDrag() }
  })()
  return pendingAction
}

async function askName(title, defaultName) {
  const { value } = await ElMessageBox.prompt('请输入名称', title, {
    inputValue: defaultName, inputPattern: /\S+/, inputErrorMessage: '名称不能为空',
    inputValidator: value => String(value || '').trim().length <= 30 || '名称最多 30 个字',
    confirmButtonText: '创建', cancelButtonText: '取消'
  })
  return value.trim()
}

async function openCreateTeamDialog() {
  return runAction(async () => {
    const name = await askName('创建团队', `团队 ${boxes.value.length + 1}`)
    updateDraft(addDraftTeam(draft.value, name, makeId('team')))
  })
}

async function createSquad(team) {
  return runAction(async () => {
    const name = await askName('创建小队', `第 ${team.squads.length + 1} 小队`)
    updateDraft(addDraftSquad(draft.value, team.team_id, name, makeId('squad')))
  })
}

async function removeStructure(team, squad) {
  return runAction(async () => {
    await ElMessageBox.confirm(`从草稿删除「${squad?.squad_name || team.team_name}」？相关玩家移出草稿，不删除帮会成员；点击“保存”后才提交后端。`, '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    updateDraft(removeDraftStructure(draft.value, team.team_id, squad?.squad_id))
  })
}
const removeTeam = team => removeStructure(team, null)
const removeSquad = (team, squad) => removeStructure(team, squad)
function toggleTeam(team) {
  const next = new Set(collapsed.value)
  const id = String(team.team_id)
  if (next.has(id)) next.delete(id); else next.add(id)
  collapsed.value = next
}
function dragPlayer(event, member) {
  if (props.readonly || locked.value || !member) { event.preventDefault(); return }
  internalDrag.value = member
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', String(member.member_id))
}
function endDrag() { internalDrag.value = null; dropKey.value = '' }
function markDrop(squad, seat) { if (!props.readonly && !locked.value) dropKey.value = `${squad.squad_id}:${seat.orderNum}` }
function dropPlayer(event, team, squad, seat) {
  if (props.readonly || locked.value) return
  const id = event.dataTransfer?.getData('text/plain')
  const member = internalDrag.value || props.draggingMember || props.members.find(row => String(row.member_id) === id)
  if (!member) { ElMessage.warning('请从候选成员或已有位置拖入玩家'); return }
  return assignPlayer(member, team, squad, seat.orderNum)
}

function assignPlayer(member, team, squad, orderNum) {
  return runAction(async () => {
    updateDraft(assignDraftPlayer(draft.value, member, team.team_id, squad.squad_id, orderNum))
  })
}
function clearPlayer(member) {
  return runAction(async () => {
    updateDraft(clearDraftPlayer(draft.value, member.member_id))
  })
}
function openPicker(team, squad, seat) {
  if (props.readonly || locked.value) return
  selectedSlot.value = { team, squad, orderNum: seat.orderNum }
  pickerKeyword.value = ''
  pickerExpanded.value = new Set()
  pickerVisible.value = true
}
function togglePickerFolder(name, event) {
  const next = new Set(pickerExpanded.value)
  if (event.currentTarget.open) next.add(name); else next.delete(name)
  pickerExpanded.value = next
}
function choosePlayer(member) {
  if (!selectedSlot.value || locked.value) return
  pickerVisible.value = false
  const { team, squad, orderNum } = selectedSlot.value
  return assignPlayer(member, team, squad, orderNum)
}
function upsertTempMember(member) {
  return runAction(async () => {
    updateDraft(upsertDraftTempMember(draft.value, member))
  })
}
async function flushWorkbookSave() {
  await pendingAction
  if (metadataLoading.value || loadError.value) throw new Error('附加数据尚未就绪，不能保存历史')
  return saveToBackend()
}
const makeId = type => `local_${type}_${crypto.randomUUID()}`
async function saveToBackend() {
  if (props.readonly || locked.value) throw Error('请等待当前操作完成后再保存')
  busy.value = true
  autosaver.stop()
  submitError.value = ''
  const userId = String(props.userId)
  let submittingStarted = false
  try {
    if (!(await autosaver.flush(true))) throw Error('本地草稿保存失败，未开始提交后端')
    syncing.value = true
    busy.value = false
    submittingStarted = true
    const api = Object.fromEntries(Object.entries(scheduleApi).map(([name, fn]) => [name, (...args) => {
      if (String(props.userId) !== userId) throw Error('账号已切换，已停止提交旧账号草稿')
      return fn(...args)
    }]))
    const onCheckpoint = async value => {
      await writeScheduleDraft(value.storageKey, value)
      if (String(props.userId) === userId) { updateDraft(value); localRevision.value = value.revision; localSavedAt.value = Date.now() }
    }
    let result
    try { result = await syncScheduleDraft(draft.value, api, { onCheckpoint }) }
    catch (error) {
      if (error.code !== 'SCHEDULE_CONFLICT') throw error
      await ElMessageBox.confirm('后端排表已被其他窗口修改。确定以当前本地草稿覆盖后端吗？取消可保留草稿。', '保存冲突', { type: 'warning', confirmButtonText: '以草稿保存', cancelButtonText: '取消' })
      result = await syncScheduleDraft(draft.value, api, { onCheckpoint, force: true })
    }
    updateDraft(result)
    return true
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      submitError.value = error?.message || '提交失败'
      ElMessage.error(submittingStarted ? `${submitError.value}；草稿已保留，部分后端步骤可能已完成，可再次保存。` : `${submitError.value}；没有写入后端，最新修改仍在内存中，请勿关闭页面。`)
    }
    throw error
  } finally { syncing.value = false; busy.value = false; if (pageActive && draft.value && String(props.userId) === userId) autosaver.start() }
}
async function applyHistoryToDraft(history, workbook) {
  return runAction(async () => {
    updateDraft(loadHistoryIntoDraft(draft.value, history, workbook, makeId))
    if (!(await autosaver.flush(true))) throw Error('历史草稿已加载到内存，但本地数据库保存失败，请勿关闭页面')
  })
}
function handleBeforeUnload(event) {
  if (!props.readonly && (syncing.value || (draft.value && localRevision.value !== draft.value.revision))) { event.preventDefault(); event.returnValue = '' }
}
function handlePageHide() { autosaver.flush(true) }
onMounted(() => { if (!props.readonly) { window.addEventListener('beforeunload', handleBeforeUnload); window.addEventListener('pagehide', handlePageHide) } })
onActivated(() => { pageActive = true; if (!props.readonly && draft.value && !syncing.value) autosaver.start() })
onDeactivated(() => { pageActive = false; autosaver.stop(); autosaver.flush(true) })
onBeforeUnmount(() => { pageActive = false; ++loadGeneration; autosaver.stop(); autosaver.flush(true); window.removeEventListener('beforeunload', handleBeforeUnload); window.removeEventListener('pagehide', handlePageHide) })
onBeforeRouteLeave(async () => {
  if (props.readonly) return true
  if (syncing.value || busy.value) { ElMessage.warning('正在操作，请完成或取消后再离开'); return false }
  if (await autosaver.flush(true)) return true
  try { await ElMessageBox.confirm('本地保存失败，离开会丢失最新修改。仍然离开？', '草稿未保存', { type: 'warning' }); return true } catch { return false }
})
defineExpose({ openCreateTeamDialog, upsertTempMember, flushWorkbookSave, reloadWorkbook, saveToBackend,
  applyHistoryToDraft, hasDraft: () => !!draft.value })
</script>

<style scoped>
.schedule-boxes { flex: 1; min-height: 0; overflow: auto; padding: 14px; color: var(--el-text-color-primary); background: var(--el-fill-color-extra-light); }
.is-preview { overflow: visible; flex: none; padding: 0; }
.draft-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; margin-bottom: 8px; }
.draft-status { font-size: 12px; color: var(--el-color-success); }
.draft-status.pending { color: var(--el-color-warning); }
.usage-hint { color: var(--el-text-color-secondary); font-size: 11px; line-height: 1.5; }
.team-list { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; align-items: start; }
.team-box { min-width: 0; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 6px; }
.team-header, .squad-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.team-header { padding: 12px; border-bottom: 1px solid var(--el-border-color-lighter); }
.team-title { min-width: 0; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.team-title strong { font-size: 15px; overflow-wrap: anywhere; }
.team-title span, .squad-header span { color: var(--el-text-color-secondary); font-size: 12px; }
.box-tools { display: flex; gap: 12px; flex: 0 0 auto; }
button { font: inherit; }
.box-tools button, .squad-header button, .compat-player button { padding: 0; border: 0; background: none; cursor: pointer; color: var(--el-text-color-regular); font-size: 12px; }
button.danger { color: var(--el-color-danger); }
button:disabled { cursor: default; }
.team-body { padding: 8px; display: flex; flex-direction: column; gap: 8px; }
.squad-box { overflow-x: auto; width: 100%; flex: none; }
.squad-box + .squad-box { padding-top: 6px; border-top: 1px solid var(--el-border-color-lighter); }
.squad-header { margin-bottom: 4px; }
.squad-header > div { display: flex; align-items: center; gap: 8px; }
.squad-header strong { font-size: 13px; }
.seat-grid { display: grid; grid-template-columns: repeat(6, minmax(80px, 1fr)); gap: 6px; }
.seat { position: relative; min-width: 0; min-height: 60px; border: 1px dashed var(--el-border-color); border-radius: 4px; background: var(--el-fill-color-extra-light); }
.seat.occupied { background: var(--el-bg-color); border-style: solid; }
.seat.drop-over { border: 1px solid var(--el-color-primary); background: var(--el-color-primary-light-9); }
.seat-number { display: block; padding: 2px 6px 0; color: var(--el-text-color-secondary); font-size: 10px; line-height: 12px; }
.seat-main { width: 100%; min-height: 40px; border: 0; padding: 3px 6px; text-align: left; background: none; cursor: pointer; color: inherit; display: flex; flex-direction: column; align-items: flex-start; gap: 1px; }
.seat-main strong { max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; line-height: 18px; }
.player-class, .class-label { border: 1px solid currentColor; border-radius: 3px; padding: 1px 5px; font-size: 11px; font-weight: 600; line-height: 16px; }
.temporary-label { position: absolute; right: 22px; top: 2px; font-size: 9px; line-height: 12px; color: var(--el-text-color-secondary); }
.empty-seat { color: var(--el-text-color-placeholder); font-size: 12px; line-height: 18px; padding-top: 5px; white-space: nowrap; }
.clear-seat { position: absolute; right: 3px; top: 0; border: 0; background: none; color: var(--el-text-color-secondary); cursor: pointer; font-size: 18px; }
.add-squad { width: 100%; margin: 0; border: 1px dashed var(--el-border-color); border-radius: 4px; padding: 6px; line-height: 18px; background: var(--el-bg-color); color: var(--el-color-primary); font-size: 12px; cursor: pointer; }
.compatibility { margin-top: 10px; padding: 10px; border: 1px solid var(--el-color-warning-light-5); background: var(--el-color-warning-light-9); border-radius: 4px; font-size: 12px; }
.compatibility p { margin: 0 0 8px; line-height: 1.6; }
.legacy-panel > strong { display: block; margin-bottom: 6px; }
details summary { cursor: pointer; padding: 8px 0; font-size: 12px; }
.compat-player { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 6px; padding: 6px 0 6px 16px; cursor: grab; }
.compat-player small, .picker-player small { color: var(--el-text-color-secondary); }
.picker-tree { margin-top: 12px; max-height: 50vh; overflow: auto; }
.picker-player { width: 100%; display: flex; justify-content: space-between; gap: 8px; border: 0; border-bottom: 1px solid var(--el-border-color-extra-light); background: none; padding: 10px 8px 10px 18px; color: var(--el-text-color-primary); text-align: left; cursor: pointer; }
.picker-player:hover { background: var(--el-fill-color-light); }
.save-error { margin: 0 0 12px; color: var(--el-color-danger); font-size: 12px; }
</style>
