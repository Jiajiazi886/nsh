<template>
  <div class="schedule-sheet-shell">
    <div
      class="sheet-workbench"
      @dragover.capture="handleWorkbenchDragOver"
      @dragleave="handleWorkbenchDragLeave"
      @pointerdown.capture="handleWorkbenchPointerDown"
      @pointermove.capture="handleWorkbenchPointerMove"
      @pointerup.capture="handleWorkbenchPointerUp"
      @pointercancel.capture="cancelInternalCellMove"
    >
      <div ref="containerRef" class="univer-host"></div>

      <div v-if="workbookLoading" class="sheet-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>正在展开自由表格...</span>
      </div>

      <div
        class="sheet-drop-catcher"
        :class="{ active: Boolean(activeDragMember), over: Boolean(dropPreviewCell) }"
        :style="dropPreviewCell?.catcherStyle"
      >
        <span v-if="dropPreviewCell" class="drop-position">
          将放入：{{ dropPreviewCell.label }}
        </span>
        <span
          v-if="dropPreviewCell"
          class="drop-cursor-tip"
          :style="dropPreviewCell.tooltipStyle"
        >
          {{ dropPreviewCell.label }}
        </span>
        <span v-else-if="activeDragMember" class="drop-position muted">
          拖到表格单元格内即可放入
        </span>
      </div>

      <div
        v-if="internalCellMove?.dragging"
        class="sheet-internal-move-tip"
        :style="internalCellMove.tooltipStyle"
      >
        <span>移动 {{ internalCellMove.label }}</span>
        <strong>{{ internalCellMove.targetLabel || '选择目标格' }}</strong>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { UniverSheetsCorePreset } from '@univerjs/preset-sheets-core'
import UniverPresetSheetsCoreZhCN from '@univerjs/preset-sheets-core/locales/zh-CN'
import {
  BooleanNumber,
  CellValueType,
  createUniver,
  HorizontalAlign,
  LocaleType,
  mergeLocales,
  VerticalAlign,
  WrapStrategy
} from '@univerjs/presets'
import { getCurrentScheduleWorkbook, saveCurrentScheduleWorkbook } from '@/api/guild/schedule'
import {
  exportScheduleWorkbook,
  getTempMembersFromWorkbook,
  setTempMembersToWorkbook
} from '../utils/scheduleWorkbook'
import '@univerjs/preset-sheets-core/lib/index.css'

const props = defineProps({
  schedule: {
    type: Object,
    default: () => ({ teams: [] })
  },
  draggingMember: {
    type: Object,
    default: null
  },
  getClassStyle: {
    type: Function,
    required: true
  }
})

const emit = defineEmits(['assign-member', 'workbook-assignments-change', 'temp-members-change'])

const LARGE_ROW_COUNT = 2000
const LARGE_COLUMN_COUNT = 200
const DEFAULT_ROW_HEIGHT = 30
const DEFAULT_COLUMN_WIDTH = 132
const PLAYER_COLUMN_WIDTH = 126
const TASK_COLUMN_WIDTH = 220
const SHEET_ID = 'schedule-free-sheet'
const WORKBOOK_ID_PREFIX = 'guild-schedule-workbook'

const containerRef = ref(null)
const univerInstance = shallowRef(null)
const univerAPIInstance = shallowRef(null)
const workbookData = shallowRef(null)
const workbookLoading = ref(false)
const dropPreviewCell = ref(null)
const systemSlotMap = shallowRef({})
const commandDisposable = shallowRef(null)
const dragOverDisposable = shallowRef(null)
const dropDisposable = shallowRef(null)
const dropHighlightDisposable = shallowRef(null)
const saveTimer = ref(null)
const loadingToken = ref(0)
const suppressCommandSave = ref(false)
const lastDragPointer = ref(null)
const lastUniverDropTarget = ref(null)
const tempMembers = ref([])
const internalCellMove = ref(null)

const teams = computed(() => props.schedule?.teams || [])
const activeDragMember = computed(() => props.draggingMember)

watch(
  () => JSON.stringify(props.schedule || {}),
  () => {
    loadWorkbook()
  }
)

onMounted(() => {
  loadWorkbook()
})

onBeforeUnmount(() => {
  flushWorkbookSave()
  disposeUniver()
  if (saveTimer.value) {
    clearTimeout(saveTimer.value)
  }
})

defineExpose({
  flushWorkbookSave,
  saveWorkbookNow,
  upsertTempMember,
  getWorkbookSnapshot,
  exportWorkbook
})

async function loadWorkbook() {
  const token = loadingToken.value + 1
  loadingToken.value = token
  workbookLoading.value = true
  try {
    const res = await getCurrentScheduleWorkbook()
    if (token !== loadingToken.value) return
    const remoteWorkbook = res.data?.workbook
    workbookData.value = normalizeWorkbookData(remoteWorkbook || buildDefaultWorkbookData())
    syncTempMembersFromWorkbook(workbookData.value)
    emitWorkbookAssignments()
    await nextTick()
    rebuildWorkbook()
  } catch (error) {
    workbookData.value = buildDefaultWorkbookData()
    syncTempMembersFromWorkbook(workbookData.value)
    emitWorkbookAssignments()
    await nextTick()
    rebuildWorkbook()
    ElMessage.warning('自由表格加载失败，已使用本地空白表格')
  } finally {
    if (token === loadingToken.value) {
      workbookLoading.value = false
    }
  }
}

function disposeUniver() {
  commandDisposable.value?.dispose?.()
  dragOverDisposable.value?.dispose?.()
  dropDisposable.value?.dispose?.()
  clearDropHighlight()
  commandDisposable.value = null
  dragOverDisposable.value = null
  dropDisposable.value = null
  univerAPIInstance.value?.dispose?.()
  univerInstance.value?.dispose?.()
  univerAPIInstance.value = null
  univerInstance.value = null
  dropPreviewCell.value = null
  lastUniverDropTarget.value = null
  cancelInternalCellMove()
}

function rebuildWorkbook() {
  if (!containerRef.value || !workbookData.value) return
  disposeUniver()
  suppressCommandSave.value = true

  const { univer, univerAPI } = createUniver({
    locale: LocaleType.ZH_CN,
    locales: {
      [LocaleType.ZH_CN]: mergeLocales(UniverPresetSheetsCoreZhCN)
    },
    presets: [
      UniverSheetsCorePreset({
        container: containerRef.value,
        header: true,
        toolbar: true,
        formulaBar: true,
        footer: true
      })
    ]
  })

  univerAPI.createWorkbook(cloneWorkbook(workbookData.value))
  univerInstance.value = univer
  univerAPIInstance.value = univerAPI
  commandDisposable.value = univerAPI.addEvent?.(univerAPI.Event.CommandExecuted, () => {
    if (!suppressCommandSave.value) {
      scheduleWorkbookSave()
    }
  })
  registerUniverDropEvents(univerAPI)
  nextTick(() => {
    suppressCommandSave.value = false
  })
}

function registerUniverDropEvents(univerAPI) {
  if (!univerAPI.addEvent || !univerAPI.Event?.DragOver || !univerAPI.Event?.Drop) return
  dragOverDisposable.value = univerAPI.addEvent(univerAPI.Event.DragOver, handleUniverDragOver)
  dropDisposable.value = univerAPI.addEvent(univerAPI.Event.Drop, handleUniverDrop)
}

function buildDefaultWorkbookData() {
  const cellData = {}
  const rowData = {}
  const columnData = {}
  const mergeData = []
  const styles = buildBaseStyles()

  const slotMap = {}
  if (teams.value.length) {
    fillScheduleTemplate(cellData, rowData, columnData, mergeData, styles, slotMap)
  } else {
    setCell(cellData, 1, 1, '自由约战排表：可以直接编辑，也可以从左侧拖入玩家。', 'title')
    mergeData.push({ startRow: 1, endRow: 1, startColumn: 1, endColumn: 8 })
  }
  systemSlotMap.value = slotMap

  return {
    id: `${WORKBOOK_ID_PREFIX}-${props.schedule?.schedule_id || 'current'}`,
    name: props.schedule?.schedule_name || '约战排表',
    appVersion: '0.25.0',
    locale: LocaleType.ZH_CN,
    styles,
    sheetOrder: [SHEET_ID],
    sheets: {
      [SHEET_ID]: {
        id: SHEET_ID,
        name: '自由排表',
        rowCount: LARGE_ROW_COUNT,
        columnCount: LARGE_COLUMN_COUNT,
        defaultRowHeight: DEFAULT_ROW_HEIGHT,
        defaultColumnWidth: DEFAULT_COLUMN_WIDTH,
        cellData,
        rowData,
        columnData,
        mergeData,
        freeze: {
          startRow: 0,
          startColumn: 0,
          ySplit: 0,
          xSplit: 0
        },
        showGridlines: 1
      }
    }
  }
}

function fillScheduleTemplate(cellData, rowData, columnData, mergeData, styles, slotMap) {
  let row = 1
  const startColumn = 1
  teams.value.forEach((team, teamIndex) => {
    const squads = team.squads || []
    const squadCount = Math.max(squads.length, 1)
    const usedColumnCount = Math.max(squadCount * 2, 6)
    const noteColumn = startColumn + usedColumnCount + 1

    rowData[row] = { h: 42 }
    setCell(cellData, row, startColumn, `${team.team_name || `第${teamIndex + 1}团`} 排表`, 'title')
    mergeData.push({ startRow: row, endRow: row, startColumn, endColumn: startColumn + usedColumnCount - 1 })
    setCell(cellData, row, noteColumn, '替换及替补', 'sideHeader')
    setCell(cellData, row, noteColumn + 1, '请假待定 / 备注', 'sideHeader')

    row += 1
    rowData[row] = { h: 34 }
    squads.forEach((squad, squadIndex) => {
      const playerColumn = startColumn + squadIndex * 2
      const taskColumn = playerColumn + 1
      columnData[playerColumn] = { w: PLAYER_COLUMN_WIDTH }
      columnData[taskColumn] = { w: TASK_COLUMN_WIDTH }
      setCell(cellData, row, playerColumn, squad.squad_name || `${squadIndex + 1}队`, 'squad')
      setCell(cellData, row, taskColumn, '职责 / 备注', 'taskHeader')
    })
    setCell(cellData, row, noteColumn, '替补', 'sideHeader')
    setCell(cellData, row, noteColumn + 1, '请假/未接龙', 'sideHeader')

    for (let slotIndex = 1; slotIndex <= 6; slotIndex += 1) {
      row += 1
      rowData[row] = { h: 34 }
      squads.forEach((squad, squadIndex) => {
        const playerColumn = startColumn + squadIndex * 2
        const taskColumn = playerColumn + 1
        const member = getSlotMember(squad, slotIndex)
        if (member) {
          const styleId = ensurePlayerStyle(styles, member.player_class)
          setCell(cellData, row, playerColumn, getMemberDisplayName(member), styleId, {
            member_id: member.member_id,
            player_class: member.player_class || ''
          })
        } else {
          setCell(cellData, row, playerColumn, '', 'empty')
        }
        setCell(cellData, row, taskColumn, '', 'task')
        slotMap[getCellKey(row, playerColumn)] = {
          team,
          squad,
          orderNum: slotIndex
        }
      })
      setCell(cellData, row, noteColumn, '', 'empty')
      setCell(cellData, row, noteColumn + 1, '', 'empty')
    }

    row += 2
  })
}

function buildBaseStyles() {
  return {
    title: {
      bg: { rgb: '#aebbe0' },
      cl: { rgb: '#111827' },
      bl: BooleanNumber.TRUE,
      fs: 16,
      ht: HorizontalAlign.CENTER,
      vt: VerticalAlign.MIDDLE
    },
    squad: {
      bg: { rgb: '#d9e0f1' },
      cl: { rgb: '#374151' },
      bl: BooleanNumber.TRUE,
      fs: 12,
      ht: HorizontalAlign.CENTER,
      vt: VerticalAlign.MIDDLE
    },
    taskHeader: {
      bg: { rgb: '#edf2ff' },
      cl: { rgb: '#374151' },
      fs: 12,
      ht: HorizontalAlign.CENTER,
      vt: VerticalAlign.MIDDLE
    },
    sideHeader: {
      bg: { rgb: '#d9e0f1' },
      cl: { rgb: '#374151' },
      fs: 12,
      ht: HorizontalAlign.CENTER,
      vt: VerticalAlign.MIDDLE
    },
    task: {
      bg: { rgb: '#ffffff' },
      cl: { rgb: '#374151' },
      fs: 12,
      ht: HorizontalAlign.CENTER,
      vt: VerticalAlign.MIDDLE,
      tb: WrapStrategy.WRAP
    },
    empty: {
      bg: { rgb: '#ffffff' },
      cl: { rgb: '#111827' },
      fs: 12,
      ht: HorizontalAlign.CENTER,
      vt: VerticalAlign.MIDDLE
    }
  }
}

function normalizeWorkbookData(rawWorkbook) {
  const workbook = cloneWorkbook(rawWorkbook || buildDefaultWorkbookData())
  workbook.id = workbook.id || `${WORKBOOK_ID_PREFIX}-${props.schedule?.schedule_id || 'current'}`
  workbook.name = workbook.name || props.schedule?.schedule_name || '约战排表'
  workbook.appVersion = workbook.appVersion || '0.25.0'
  workbook.locale = workbook.locale || LocaleType.ZH_CN
  workbook.styles = { ...buildBaseStyles(), ...(workbook.styles || {}) }
  workbook.sheetOrder = workbook.sheetOrder?.length ? workbook.sheetOrder : [SHEET_ID]
  workbook.sheets = workbook.sheets || {}

  const firstSheetId = workbook.sheetOrder[0] || Object.keys(workbook.sheets)[0] || SHEET_ID
  if (!workbook.sheets[firstSheetId]) {
    workbook.sheets[firstSheetId] = buildDefaultWorkbookData().sheets[SHEET_ID]
    workbook.sheetOrder = [firstSheetId]
  }

  const sheet = workbook.sheets[firstSheetId]
  sheet.id = sheet.id || firstSheetId
  sheet.name = sheet.name || '自由排表'
  sheet.rowCount = Math.max(Number(sheet.rowCount || 0), LARGE_ROW_COUNT)
  sheet.columnCount = Math.max(Number(sheet.columnCount || 0), LARGE_COLUMN_COUNT)
  sheet.defaultRowHeight = sheet.defaultRowHeight || DEFAULT_ROW_HEIGHT
  sheet.defaultColumnWidth = sheet.defaultColumnWidth || DEFAULT_COLUMN_WIDTH
  sheet.cellData = sheet.cellData || {}
  sheet.rowData = sheet.rowData || {}
  sheet.columnData = sheet.columnData || {}
  sheet.mergeData = sheet.mergeData || []
  sheet.showGridlines = 1
  normalizeNumericMemberCells(sheet)
  systemSlotMap.value = buildSlotMapFromSchedule()
  return workbook
}

function normalizeNumericMemberCells(sheet) {
  Object.values(sheet.cellData || {}).forEach(columns => {
    Object.values(columns || {}).forEach(cell => {
      if (!cell?.custom?.member_id || !isPlainNumericId(cell.v)) return
      const normalized = buildCellValue(cell.v)
      cell.v = normalized.v
      cell.t = normalized.t
    })
  })
}

async function upsertTempMember(member) {
  if (!member?.member_id || !member?.player_name) return
  const normalized = {
    member_id: String(member.member_id),
    player_name: String(member.player_name || ''),
    player_class: String(member.player_class || ''),
    secondary_class: String(member.secondary_class || ''),
    is_temporary: true
  }
  const existingIndex = tempMembers.value.findIndex(item => String(item.member_id) === normalized.member_id)
  const nextMembers = [...tempMembers.value]
  if (existingIndex >= 0) {
    nextMembers.splice(existingIndex, 1, normalized)
  } else {
    nextMembers.push(normalized)
  }
  tempMembers.value = nextMembers
  workbookData.value = normalizeWorkbookData(setTempMembersToWorkbook(getWorkbookSnapshot(), tempMembers.value))
  emitTempMembers()
  await saveWorkbookNow()
}

function syncTempMembersFromWorkbook(workbook) {
  tempMembers.value = getTempMembersFromWorkbook(workbook)
  emitTempMembers()
}

function emitTempMembers() {
  emit('temp-members-change', tempMembers.value.map(member => ({ ...member })))
}

function buildSlotMapFromSchedule() {
  const slotMap = {}
  let row = 3
  const startColumn = 1
  teams.value.forEach((team) => {
    const squads = team.squads || []
    for (let slotIndex = 1; slotIndex <= 6; slotIndex += 1) {
      squads.forEach((squad, squadIndex) => {
        const playerColumn = startColumn + squadIndex * 2
        slotMap[getCellKey(row, playerColumn)] = {
          team,
          squad,
          orderNum: slotIndex
        }
      })
      row += 1
    }
    row += 3
  })
  return slotMap
}

function getSlotMember(squad, slotIndex) {
  return (squad.members || []).find(member => Number(member.order_num || 0) === slotIndex)
    || (squad.members || [])[slotIndex - 1]
    || null
}

function setCell(cellData, row, column, value, styleId, custom = null) {
  if (!cellData[row]) {
    cellData[row] = {}
  }
  const cellValue = custom?.member_id ? buildCellValue(value) : buildTextCellValue(value)
  cellData[row][column] = {
    ...cellValue,
    s: styleId
  }
  if (custom) {
    cellData[row][column].custom = custom
  }
}

function ensurePlayerStyle(styles, className) {
  const styleId = classStyleId(className)
  if (styles[styleId]) return styleId
  const style = normalizeClassStyle(props.getClassStyle(className))
  styles[styleId] = {
    bg: { rgb: style.backgroundColor || '#dbeafe' },
    cl: { rgb: style.color || '#111827' },
    bl: BooleanNumber.TRUE,
    fs: 12,
    ht: HorizontalAlign.CENTER,
    vt: VerticalAlign.MIDDLE,
    tb: WrapStrategy.WRAP
  }
  return styleId
}

function handleWorkbenchDragOver(event) {
  if (!activeDragMember.value) return
  lastDragPointer.value = {
    clientX: event.clientX,
    clientY: event.clientY
  }
  if (dropPreviewCell.value) {
    dropPreviewCell.value = buildDropPreview(dropPreviewCell.value, event)
  }
}

function handleWorkbenchDragLeave(event) {
  const nextTarget = event.relatedTarget
  if (nextTarget && event.currentTarget?.contains?.(nextTarget)) return
  clearDropPreview()
}

function handleWorkbenchPointerDown(event) {
  if (event.button !== 0 || !event.altKey || activeDragMember.value || workbookLoading.value) return
  const selectedCell = getSelectedMemberCellForMove()
  if (!selectedCell) return

  internalCellMove.value = {
    source: selectedCell,
    cellData: cloneWorkbook(selectedCell.cellData),
    startX: event.clientX,
    startY: event.clientY,
    pointerX: event.clientX,
    pointerY: event.clientY,
    dragging: false,
    label: formatCellPosition(selectedCell),
    target: null,
    targetLabel: '',
    tooltipStyle: buildInternalMoveTooltipStyle(event)
  }
}

function handleWorkbenchPointerMove(event) {
  const state = internalCellMove.value
  if (!state) return
  if (!event.altKey) {
    cancelInternalCellMove()
    return
  }

  const distance = Math.hypot(event.clientX - state.startX, event.clientY - state.startY)
  if (distance < 4 && !state.dragging) return

  const target = getTargetCellFromActiveSelection(state.source, event)
  const targetLabel = target ? formatCellPosition(target) : ''
  internalCellMove.value = {
    ...state,
    pointerX: event.clientX,
    pointerY: event.clientY,
    dragging: true,
    target,
    targetLabel,
    tooltipStyle: buildInternalMoveTooltipStyle(event)
  }

  if (target) {
    updateDropHighlight({ ...target, worksheet: getActiveWorksheet() })
  }
}

async function handleWorkbenchPointerUp(event) {
  const state = internalCellMove.value
  if (!state) return

  const target = state.dragging
    ? getTargetCellFromActiveSelection(state.source, event) || state.target
    : null
  cancelInternalCellMove()
  if (!target || isSameCell(state.source, target)) return

  await moveMemberCell(state.source, target, state.cellData)
}

function getSelectedMemberCellForMove() {
  const workbook = univerAPIInstance.value?.getActiveWorkbook?.()
  const activeCell = workbook?.getActiveCell?.() || workbook?.getActiveRange?.()
  const row = Number(activeCell?.getRow?.())
  const column = Number(activeCell?.getColumn?.())
  if (!Number.isInteger(row) || !Number.isInteger(column)) return null

  const cellData = getSnapshotCellData(row, column)
  if (!cellData?.custom?.member_id) return null
  return { row, column, cellData }
}

function getTargetCellFromActiveSelection(source, event) {
  const workbook = univerAPIInstance.value?.getActiveWorkbook?.()
  const activeRange = workbook?.getActiveRange?.()
  const range = activeRange?.getRange?.()
  if (!range) {
    const activeCell = workbook?.getActiveCell?.()
    const row = Number(activeCell?.getRow?.())
    const column = Number(activeCell?.getColumn?.())
    return Number.isInteger(row) && Number.isInteger(column) ? { row, column } : null
  }

  const startRow = Number(range.startRow)
  const endRow = Number(range.endRow)
  const startColumn = Number(range.startColumn)
  const endColumn = Number(range.endColumn)
  if ([startRow, endRow, startColumn, endColumn].some(value => !Number.isInteger(value))) return null

  const deltaX = event.clientX - (internalCellMove.value?.startX || event.clientX)
  const deltaY = event.clientY - (internalCellMove.value?.startY || event.clientY)
  const row = deltaY < 0 ? startRow : endRow
  const column = deltaX < 0 ? startColumn : endColumn
  return { row, column }
}

async function moveMemberCell(source, target, cellData) {
  const worksheet = getActiveWorksheet()
  const sourceRange = worksheet?.getRange?.(source.row, source.column)
  const targetRange = worksheet?.getRange?.(target.row, target.column)
  if (!sourceRange || !targetRange) return

  targetRange.setValueForCell(cloneWorkbook(cellData))
  sourceRange.clear()

  await saveWorkbookNow()
  emitWorkbookAssignments()

  const slot = systemSlotMap.value[getCellKey(target.row, target.column)]
  if (!cellData?.custom?.is_temporary && slot?.team && slot?.squad) {
    emit('assign-member', {
      member: {
        member_id: cellData.custom.member_id,
        player_class: cellData.custom.player_class || '',
        player_name: cellData.custom.player_name || cellData.v || ''
      },
      team: slot.team,
      squad: slot.squad,
      orderNum: slot.orderNum
    })
  }
}

function getSnapshotCellData(row, column) {
  const workbook = getWorkbookSnapshot()
  const sheetId = workbook?.sheetOrder?.[0] || Object.keys(workbook?.sheets || {})[0]
  return sheetId ? workbook?.sheets?.[sheetId]?.cellData?.[row]?.[column] : null
}

function buildInternalMoveTooltipStyle(event) {
  const workbenchRect = containerRef.value?.parentElement?.getBoundingClientRect()
  if (!workbenchRect) return {}
  const tooltipWidth = 150
  const tooltipHeight = 48
  const left = Math.min(
    Math.max(8, event.clientX - workbenchRect.left + 14),
    Math.max(8, workbenchRect.width - tooltipWidth - 8)
  )
  const top = Math.min(
    Math.max(8, event.clientY - workbenchRect.top + 14),
    Math.max(8, workbenchRect.height - tooltipHeight - 8)
  )
  return {
    left: `${left}px`,
    top: `${top}px`
  }
}

function cancelInternalCellMove() {
  internalCellMove.value = null
  clearDropHighlight()
}

function isSameCell(left, right) {
  return Number(left?.row) === Number(right?.row) && Number(left?.column) === Number(right?.column)
}

function handleUniverDragOver(params) {
  const member = activeDragMember.value
  if (!member) return
  const target = normalizeUniverDropTarget(params)
  if (!target) {
    clearDropPreview()
    return
  }
  lastUniverDropTarget.value = target
  dropPreviewCell.value = buildDropPreview(target)
  updateDropHighlight(target)
  debugUniverDropHit('dragover', params, target)
  if (params.dataTransfer) {
    params.dataTransfer.dropEffect = 'move'
  }
}

async function handleUniverDrop(params) {
  const member = activeDragMember.value
  const target = normalizeUniverDropTarget(params) || lastUniverDropTarget.value
  clearDropPreview()
  if (!member) return
  if (!target) {
    ElMessage.warning('请拖到表格单元格内')
    return
  }
  debugUniverDropHit('drop', params, target)
  await placeMemberIntoCell(member, target)
}

async function placeMemberIntoCell(member, target) {
  const range = target.worksheet?.getRange?.(target.row, target.column) || getActiveWorksheet()?.getRange(target.row, target.column)
  if (!range) return
  const style = normalizeClassStyle(props.getClassStyle(member.player_class))
  const displayName = getMemberDisplayName(member)
  range.setValueForCell({
    ...buildCellValue(displayName),
    s: {
      bg: { rgb: style.backgroundColor || '#dbeafe' },
      cl: { rgb: style.color || '#111827' },
      bl: BooleanNumber.TRUE,
      ht: HorizontalAlign.CENTER,
      vt: VerticalAlign.MIDDLE,
      tb: WrapStrategy.WRAP
    },
    custom: {
      member_id: member.member_id,
      player_class: member.player_class || '',
      player_name: displayName,
      is_temporary: Boolean(member.is_temporary)
    }
  })

  await saveWorkbookNow()
  emitWorkbookAssignments()

  const slot = systemSlotMap.value[getCellKey(target.row, target.column)]
  if (!member.is_temporary && slot?.team && slot?.squad) {
    emit('assign-member', {
      member,
      team: slot.team,
      squad: slot.squad,
      orderNum: slot.orderNum
    })
  }
}

function normalizeUniverDropTarget(params) {
  const row = Number(params?.row ?? params?.location?.row)
  const column = Number(params?.column ?? params?.col ?? params?.location?.col)
  if (!Number.isInteger(row) || !Number.isInteger(column) || row < 0 || column < 0) return null
  const sheet = getCurrentSheetData(false)
  return {
    row: clampIndex(row, sheet?.rowCount || LARGE_ROW_COUNT),
    column: clampIndex(column, sheet?.columnCount || LARGE_COLUMN_COUNT),
    worksheet: params?.worksheet || getActiveWorksheet()
  }
}

function buildDropPreview(target, event = null) {
  const workbenchRect = containerRef.value?.parentElement?.getBoundingClientRect()
  if (!workbenchRect) return null

  const pointer = event || lastDragPointer.value
  const tooltipWidth = 82
  const tooltipHeight = 34
  const rawTooltipLeft = (pointer?.clientX ?? workbenchRect.right - 120) - workbenchRect.left + 16
  const rawTooltipTop = (pointer?.clientY ?? workbenchRect.top + 130) - workbenchRect.top + 14
  const tooltipLeft = Math.min(Math.max(8, rawTooltipLeft), Math.max(8, workbenchRect.width - tooltipWidth - 8))
  const tooltipTop = Math.min(Math.max(8, rawTooltipTop), Math.max(8, workbenchRect.height - tooltipHeight - 8))

  return {
    row: target.row,
    column: target.column,
    label: formatCellPosition(target),
    catcherStyle: {
      '--drag-x': `${(pointer?.clientX ?? workbenchRect.left + workbenchRect.width / 2) - workbenchRect.left}px`,
      '--drag-y': `${(pointer?.clientY ?? workbenchRect.top + workbenchRect.height / 2) - workbenchRect.top}px`
    },
    tooltipStyle: {
      left: `${tooltipLeft}px`,
      top: `${tooltipTop}px`
    }
  }
}

function updateDropHighlight(target) {
  clearDropHighlight()
  const worksheet = target.worksheet || getActiveWorksheet()
  const range = worksheet?.getRange?.(target.row, target.column)
  if (!worksheet?.highlightRanges || !range) return
  dropHighlightDisposable.value = worksheet.highlightRanges(
    [range],
    {
      stroke: '#0ea5e9',
      strokeWidth: 2.5,
      fill: 'rgba(14, 165, 233, 0.20)',
      rowHeaderFill: 'rgba(14, 165, 233, 0.18)',
      columnHeaderFill: 'rgba(14, 165, 233, 0.18)',
      widgets: {}
    }
  )
}

function clearDropHighlight() {
  dropHighlightDisposable.value?.dispose?.()
  dropHighlightDisposable.value = null
}

function clearDropPreview() {
  dropPreviewCell.value = null
  lastUniverDropTarget.value = null
  clearDropHighlight()
}

function getCurrentSheetData(liveSnapshot = false) {
  const workbook = liveSnapshot
    ? normalizeWorkbookData(univerAPIInstance.value?.getActiveWorkbook?.()?.save?.() || workbookData.value)
    : workbookData.value
  const sheetId = workbook?.sheetOrder?.[0] || Object.keys(workbook?.sheets || {})[0]
  return sheetId ? workbook?.sheets?.[sheetId] : null
}

function debugUniverDropHit(phase, params, target) {
  if (!import.meta.env.DEV || localStorage.getItem('guild-schedule-debug-drop') !== '1') return
  console.debug('[guild-schedule-drop]', {
    phase,
    cell: formatCellPosition(target),
    row: target.row,
    column: target.column,
    univerRow: params?.row,
    univerColumn: params?.column,
    location: params?.location
  })
}

function getActiveWorksheet() {
  const workbook = univerAPIInstance.value?.getActiveWorkbook?.()
  return workbook?.getActiveSheet?.()
}

function scheduleWorkbookSave(delay = 1000) {
  if (saveTimer.value) {
    clearTimeout(saveTimer.value)
  }
  saveTimer.value = setTimeout(() => {
    saveWorkbookNow()
  }, delay)
}

async function flushWorkbookSave() {
  if (saveTimer.value) {
    clearTimeout(saveTimer.value)
    saveTimer.value = null
  }
  await saveWorkbookNow()
}

async function saveWorkbookNow() {
  if (!univerAPIInstance.value) return
  if (saveTimer.value) {
    clearTimeout(saveTimer.value)
    saveTimer.value = null
  }
  const snapshot = univerAPIInstance.value.getActiveWorkbook?.()?.save?.()
  if (!snapshot) return
  workbookData.value = normalizeWorkbookData(setTempMembersToWorkbook(snapshot, tempMembers.value))
  emitWorkbookAssignments()
  try {
    await saveCurrentScheduleWorkbook(workbookData.value)
  } catch (error) {
    ElMessage.error('自由表格保存失败')
  }
}

function getWorkbookSnapshot() {
  const snapshot = univerAPIInstance.value?.getActiveWorkbook?.()?.save?.() || workbookData.value || buildDefaultWorkbookData()
  return normalizeWorkbookData(setTempMembersToWorkbook(snapshot, tempMembers.value))
}

async function exportWorkbook(filename = '约战排表.xlsx', sourceWorkbook = null) {
  await exportScheduleWorkbook(sourceWorkbook || getWorkbookSnapshot(), filename)
}

function emitWorkbookAssignments() {
  const sheet = getCurrentSheetData(false)
  const rows = sheet?.cellData || {}
  const assignments = []
  Object.entries(rows).forEach(([rowKey, columns]) => {
    Object.entries(columns || {}).forEach(([columnKey, cell]) => {
      const memberId = cell?.custom?.member_id
      if (!memberId) return
      const row = Number(rowKey)
      const column = Number(columnKey)
      if (!Number.isFinite(row) || !Number.isFinite(column)) return
      assignments.push({
        member_id: memberId,
        player_class: cell?.custom?.player_class || '',
        player_name: cell?.custom?.player_name || cell?.v || '',
        is_temporary: Boolean(cell?.custom?.is_temporary),
        cellLabel: formatCellPosition({ row, column })
      })
    })
  })
  emit('workbook-assignments-change', assignments)
}

function getCellKey(row, column) {
  return `${row}:${column}`
}

function getMemberDisplayName(member) {
  return String(member.player_id || member.game_id || member.player_name || member.member_id || '')
}

function buildCellValue(value) {
  const text = String(value ?? '')
  if (isPlainNumericId(text)) {
    return {
      v: Number(text),
      t: CellValueType.NUMBER
    }
  }
  return {
    v: text,
    t: CellValueType.STRING
  }
}

function buildTextCellValue(value) {
  return {
    v: String(value ?? ''),
    t: CellValueType.STRING
  }
}

function isPlainNumericId(value) {
  return /^(0|[1-9]\d*)$/.test(String(value || '').trim())
}

function classStyleId(className) {
  const normalized = String(className || 'unset').replace(/[^\w\u4e00-\u9fa5-]/g, '_')
  return `class_${normalized}`
}

function normalizeClassStyle(style) {
  if (!style || typeof style !== 'object') {
    return {}
  }
  return {
    color: normalizeColor(style.color),
    backgroundColor: normalizeColor(style.backgroundColor || style.background)
  }
}

function normalizeColor(value) {
  if (!value || typeof value !== 'string') return ''
  if (value.startsWith('#')) return value
  const match = value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i)
  if (!match) return ''
  return `#${[match[1], match[2], match[3]].map(item => Number(item).toString(16).padStart(2, '0')).join('')}`
}

function cloneWorkbook(value) {
  return JSON.parse(JSON.stringify(value || {}))
}

function clampIndex(value, max) {
  return Math.max(0, Math.min(max - 1, Number(value) || 0))
}

function formatCellPosition(cell) {
  return `${columnToName(cell.column)}${cell.row + 1}`
}

function columnToName(index) {
  let value = index + 1
  let name = ''
  while (value > 0) {
    const remainder = (value - 1) % 26
    name = String.fromCharCode(65 + remainder) + name
    value = Math.floor((value - 1) / 26)
  }
  return name
}
</script>

<style scoped>
.schedule-sheet-shell {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.sheet-workbench {
  position: relative;
  flex: 1;
  min-height: 680px;
  overflow: hidden;
}

.univer-host {
  position: absolute;
  inset: 0;
}

.sheet-loading {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  background: rgba(248, 250, 252, 0.74);
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  backdrop-filter: blur(3px);
}

.sheet-drop-catcher {
  position: absolute;
  inset: 0;
  z-index: 8;
  display: none;
  pointer-events: none;
}

.sheet-drop-catcher.active {
  display: block;
  pointer-events: none;
}

.sheet-drop-catcher.over {
  cursor: copy;
  background:
    radial-gradient(circle at var(--drag-x, 50%) var(--drag-y, 50%), rgba(14, 165, 233, 0.12), transparent 220px),
    linear-gradient(135deg, rgba(37, 99, 235, 0.035), rgba(14, 165, 233, 0.02));
}

.drop-position {
  position: absolute;
  top: 132px;
  right: 20px;
  border: 1px solid rgba(37, 99, 235, 0.28);
  border-radius: 999px;
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.92);
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 800;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.12);
}

.drop-position.muted {
  border-color: rgba(100, 116, 139, 0.28);
  color: #475569;
}

.drop-cursor-tip {
  position: absolute;
  z-index: 3;
  min-width: 48px;
  pointer-events: none;
  border: 1px solid rgba(8, 47, 73, 0.18);
  border-radius: 10px;
  padding: 7px 11px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(224, 242, 254, 0.92));
  color: #075985;
  font-family: "JetBrains Mono", "Cascadia Mono", Consolas, monospace;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 0.04em;
  text-align: center;
  box-shadow:
    0 14px 30px rgba(8, 47, 73, 0.16),
    0 0 0 1px rgba(255, 255, 255, 0.7) inset;
  transform: translateZ(0);
}

.sheet-internal-move-tip {
  position: absolute;
  z-index: 9;
  pointer-events: none;
  display: grid;
  gap: 2px;
  min-width: 126px;
  border: 1px solid rgba(15, 23, 42, 0.18);
  border-radius: 12px;
  padding: 8px 10px;
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.9));
  color: #e2e8f0;
  box-shadow:
    0 16px 34px rgba(15, 23, 42, 0.22),
    0 0 0 1px rgba(255, 255, 255, 0.12) inset;
}

.sheet-internal-move-tip span {
  font-size: 11px;
  font-weight: 700;
  opacity: 0.8;
}

.sheet-internal-move-tip strong {
  color: #7dd3fc;
  font-family: "JetBrains Mono", "Cascadia Mono", Consolas, monospace;
  font-size: 15px;
  letter-spacing: 0.04em;
}

@media (max-width: 900px) {
  .sheet-workbench {
    min-height: 720px;
  }
}
</style>
