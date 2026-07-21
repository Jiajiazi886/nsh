import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'

const DEFAULT_PREVIEW_ROW_LIMIT = 80
const DEFAULT_PREVIEW_COLUMN_LIMIT = 40
const DEFAULT_EXPORT_ROW_LIMIT = 2000
const DEFAULT_EXPORT_COLUMN_LIMIT = 200

const EXCEL_MAX_IMPORT_ROWS = 2000
const EXCEL_MAX_IMPORT_COLUMNS = 200
const EXCEL_BORDER_STYLE = {
  thin: 1,
  hair: 2,
  dotted: 3,
  dashed: 4,
  dashDot: 5,
  dashDotDot: 6,
  double: 7,
  medium: 8,
  mediumDashed: 9,
  mediumDashDot: 10,
  mediumDashDotDot: 11,
  slantDashDot: 12,
  thick: 13
}

export function cloneWorkbook(value) {
  return JSON.parse(JSON.stringify(value || {}))
}

export function getFirstSheet(workbook) {
  const sheetId = workbook?.sheetOrder?.[0] || Object.keys(workbook?.sheets || {})[0]
  if (!sheetId) return null
  const sheet = workbook?.sheets?.[sheetId]
  return sheet ? { sheetId, sheet } : null
}

export function getWorkbookCustom(workbook) {
  if (!workbook || typeof workbook !== 'object') return {}
  if (!workbook.custom || typeof workbook.custom !== 'object') {
    workbook.custom = {}
  }
  return workbook.custom
}

export function getTempMembersFromWorkbook(workbook) {
  const custom = workbook?.custom || {}
  return Array.isArray(custom.guildScheduleTempMembers)
    ? custom.guildScheduleTempMembers.filter(item => item?.member_id && item?.player_name)
    : []
}

export function setTempMembersToWorkbook(workbook, tempMembers = []) {
  const nextWorkbook = cloneWorkbook(workbook)
  const custom = getWorkbookCustom(nextWorkbook)
  custom.guildScheduleTempMembers = tempMembers.map(member => ({
    member_id: String(member.member_id),
    player_name: String(member.player_name || ''),
    player_class: String(member.player_class || ''),
    secondary_class: String(member.secondary_class || ''),
    is_temporary: true
  }))
  return nextWorkbook
}

export function getScheduleRegionsFromWorkbook(workbook) {
  const custom = workbook?.custom || {}
  const regions = custom.guildScheduleRegions || {}
  return {
    squads: Array.isArray(regions.squads)
      ? regions.squads.map(normalizeSquadRegion).filter(Boolean)
      : [],
    teams: Array.isArray(regions.teams)
      ? regions.teams.map(normalizeTeamRegion).filter(Boolean)
      : []
  }
}

export function setScheduleRegionsToWorkbook(workbook, regions = {}) {
  const nextWorkbook = cloneWorkbook(workbook)
  const custom = getWorkbookCustom(nextWorkbook)
  custom.guildScheduleRegions = {
    squads: Array.isArray(regions.squads)
      ? regions.squads.map(normalizeSquadRegion).filter(Boolean)
      : [],
    teams: Array.isArray(regions.teams)
      ? regions.teams.map(normalizeTeamRegion).filter(Boolean)
      : []
  }
  return nextWorkbook
}

export function getUsedRange(workbook, options = {}) {
  const firstSheet = getFirstSheet(workbook)
  if (!firstSheet) return null
  const { sheet } = firstSheet
  const maxRows = options.maxRows || DEFAULT_EXPORT_ROW_LIMIT
  const maxColumns = options.maxColumns || DEFAULT_EXPORT_COLUMN_LIMIT
  let minRow = Number.POSITIVE_INFINITY
  let maxRow = 0
  let minColumn = Number.POSITIVE_INFINITY
  let maxColumn = 0

  Object.entries(sheet.cellData || {}).forEach(([rowKey, columns]) => {
    const row = Number(rowKey)
    if (!Number.isFinite(row) || row >= maxRows) return
    Object.entries(columns || {}).forEach(([columnKey, cell]) => {
      const column = Number(columnKey)
      if (!Number.isFinite(column) || column >= maxColumns) return
      const hasValue = cell?.v !== undefined && cell?.v !== null && String(cell.v) !== ''
      const hasStyle = Boolean(cell?.s)
      const hasCustom = Boolean(cell?.custom)
      if (!hasValue && !hasStyle && !hasCustom) return
      minRow = Math.min(minRow, row)
      maxRow = Math.max(maxRow, row)
      minColumn = Math.min(minColumn, column)
      maxColumn = Math.max(maxColumn, column)
    })
  })

  ;(sheet.mergeData || []).forEach((merge) => {
    minRow = Math.min(minRow, Number(merge.startRow || 0))
    maxRow = Math.max(maxRow, Number(merge.endRow || 0))
    minColumn = Math.min(minColumn, Number(merge.startColumn || 0))
    maxColumn = Math.max(maxColumn, Number(merge.endColumn || 0))
  })

  getScheduleRegionsFromWorkbook(workbook).squads.forEach((region) => {
    minRow = Math.min(minRow, region.range.start_row)
    maxRow = Math.max(maxRow, region.range.end_row)
    minColumn = Math.min(minColumn, region.range.start_column)
    maxColumn = Math.max(maxColumn, region.range.end_column)
  })

  if (!Number.isFinite(minRow) || !Number.isFinite(minColumn)) {
    if (options.emptyFallback === false) return null
    return {
      sheet,
      minRow: 0,
      maxRow: Math.min(20, maxRows - 1),
      minColumn: 0,
      maxColumn: Math.min(10, maxColumns - 1)
    }
  }

  return {
    sheet,
    minRow: Math.max(0, minRow),
    maxRow: Math.min(maxRows - 1, maxRow),
    minColumn: Math.max(0, minColumn),
    maxColumn: Math.min(maxColumns - 1, maxColumn)
  }
}

export function buildWorkbookPreviewModel(workbook, options = {}) {
  return buildWorkbookTableModel(workbook, {
    maxRows: options.maxRows || DEFAULT_PREVIEW_ROW_LIMIT,
    maxColumns: options.maxColumns || DEFAULT_PREVIEW_COLUMN_LIMIT,
    emptyFallback: options.emptyFallback ?? true
  })
}

export function buildWorkbookTableModel(workbook, options = {}) {
  const range = getUsedRange(workbook, {
    maxRows: options.maxRows || DEFAULT_EXPORT_ROW_LIMIT,
    maxColumns: options.maxColumns || DEFAULT_EXPORT_COLUMN_LIMIT,
    emptyFallback: options.emptyFallback === true
  })
  if (!range) return null
  const { sheet, minRow, maxRow, minColumn, maxColumn } = range
  const styles = workbook?.styles || {}
  const coveredCells = new Set()
  const mergeMap = new Map()

  ;(sheet.mergeData || []).forEach((merge) => {
    const startRow = Number(merge.startRow)
    const endRow = Number(merge.endRow)
    const startColumn = Number(merge.startColumn)
    const endColumn = Number(merge.endColumn)
    if ([startRow, endRow, startColumn, endColumn].some(value => !Number.isFinite(value))) return
    if (endRow < minRow || startRow > maxRow || endColumn < minColumn || startColumn > maxColumn) return
    mergeMap.set(cellKey(startRow, startColumn), {
      rowspan: Math.max(1, Math.min(endRow, maxRow) - Math.max(startRow, minRow) + 1),
      colspan: Math.max(1, Math.min(endColumn, maxColumn) - Math.max(startColumn, minColumn) + 1)
    })
    for (let row = startRow; row <= endRow; row += 1) {
      for (let column = startColumn; column <= endColumn; column += 1) {
        if (row === startRow && column === startColumn) continue
        coveredCells.add(cellKey(row, column))
      }
    }
  })

  const rows = []
  for (let row = minRow; row <= maxRow; row += 1) {
    const cells = []
    for (let column = minColumn; column <= maxColumn; column += 1) {
      if (coveredCells.has(cellKey(row, column))) continue
      const cell = sheet.cellData?.[row]?.[column] || {}
      const merge = mergeMap.get(cellKey(row, column)) || {}
      const style = resolveCellStyle(cell, styles)
      cells.push({
        key: cellKey(row, column),
        value: cell.v ?? '',
        rowspan: merge.rowspan || 1,
        colspan: merge.colspan || 1,
        style: toCssStyle(style)
      })
    }
    rows.push({
      key: row,
      label: String(row + 1),
      height: pxFromRowHeight(sheet.rowData?.[row]?.h || sheet.defaultRowHeight || 30),
      cells
    })
  }

  const columns = []
  for (let column = minColumn; column <= maxColumn; column += 1) {
    columns.push({
      key: column,
      label: columnToName(column),
      width: pxFromColumnWidth(sheet.columnData?.[column]?.w || sheet.defaultColumnWidth || 120)
    })
  }

  return {
    rows,
    columns,
    sheetName: sheet.name || '约战排表',
    range: { minRow, maxRow, minColumn, maxColumn },
    rowCount: maxRow - minRow + 1,
    columnCount: maxColumn - minColumn + 1
  }
}

export async function exportScheduleWorkbook(workbook, filename = '约战排表.xlsx') {
  const range = getUsedRange(workbook)
  if (!range) return
  const { sheet, minRow, maxRow, minColumn, maxColumn } = range
  const styles = workbook?.styles || {}
  const squadRegions = getScheduleRegionsFromWorkbook(workbook).squads
  const excelWorkbook = new ExcelJS.Workbook()
  const excelSheet = excelWorkbook.addWorksheet(sheet.name || '约战排表')

  for (let column = minColumn; column <= maxColumn; column += 1) {
    const excelColumn = excelSheet.getColumn(column - minColumn + 1)
    excelColumn.width = excelWidthFromPixels(sheet.columnData?.[column]?.w || sheet.defaultColumnWidth || 120)
  }

  for (let row = minRow; row <= maxRow; row += 1) {
    const excelRow = excelSheet.getRow(row - minRow + 1)
    excelRow.height = excelHeightFromPixels(sheet.rowData?.[row]?.h || sheet.defaultRowHeight || 30)
    for (let column = minColumn; column <= maxColumn; column += 1) {
      const sourceCell = sheet.cellData?.[row]?.[column] || {}
      const regionBorder = getRegionBorder(row, column, squadRegions)
      if (!sourceCell.v && !sourceCell.s && !regionBorder) continue
      const excelCell = excelRow.getCell(column - minColumn + 1)
      excelCell.value = sourceCell.v ?? ''
      applyExcelCellStyle(excelCell, resolveCellStyle(sourceCell, styles), regionBorder)
    }
  }

  ;(sheet.mergeData || []).forEach((merge) => {
    const startRow = Number(merge.startRow)
    const endRow = Number(merge.endRow)
    const startColumn = Number(merge.startColumn)
    const endColumn = Number(merge.endColumn)
    if ([startRow, endRow, startColumn, endColumn].some(value => !Number.isFinite(value))) return
    if (endRow < minRow || startRow > maxRow || endColumn < minColumn || startColumn > maxColumn) return
    excelSheet.mergeCells(
      Math.max(startRow, minRow) - minRow + 1,
      Math.max(startColumn, minColumn) - minColumn + 1,
      Math.min(endRow, maxRow) - minRow + 1,
      Math.min(endColumn, maxColumn) - minColumn + 1
    )
  })

  const buffer = await excelWorkbook.xlsx.writeBuffer()
  saveAs(
    new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
    filename.endsWith('.xlsx') ? filename : `${filename}.xlsx`
  )
}

export async function importScheduleWorkbook(file, members = []) {
  if (!file || !/\.xlsx$/i.test(file.name || '')) {
    throw new Error('请选择 .xlsx 格式的 Excel 文件')
  }

  const excelWorkbook = new ExcelJS.Workbook()
  await excelWorkbook.xlsx.load(await file.arrayBuffer())
  const excelSheet = excelWorkbook.worksheets[0]
  if (!excelSheet) {
    throw new Error('Excel 中没有可导入的工作表')
  }

  const rowCount = Math.min(Math.max(excelSheet.actualRowCount || 1, 1), EXCEL_MAX_IMPORT_ROWS)
  const columnCount = Math.min(Math.max(excelSheet.actualColumnCount || 1, 1), EXCEL_MAX_IMPORT_COLUMNS)
  const memberByName = new Map(
    members
      .filter(member => member?.member_id && member?.player_name)
      .map(member => [String(member.player_name).trim(), member])
  )
  const temporaryMembers = new Map()
  const cellData = {}
  const rowData = {}
  const columnData = {}

  for (let rowIndex = 1; rowIndex <= rowCount; rowIndex += 1) {
    const excelRow = excelSheet.getRow(rowIndex)
    if (excelRow.height) {
      rowData[rowIndex - 1] = { h: Math.max(24, Math.round(excelRow.height / 0.75)) }
    }
    for (let columnIndex = 1; columnIndex <= columnCount; columnIndex += 1) {
      const excelCell = excelRow.getCell(columnIndex)
      const value = getExcelCellText(excelCell)
      const style = buildImportedCellStyle(excelCell)
      if (!value && !Object.keys(style).length) continue

      const row = rowIndex - 1
      const column = columnIndex - 1
      const member = memberByName.get(value)
      const custom = member
        ? {
            member_id: member.member_id,
            player_name: member.player_name,
            player_class: member.player_class || '',
            is_temporary: false
          }
        : buildTemporaryMember(value, temporaryMembers)

      if (!cellData[row]) cellData[row] = {}
      cellData[row][column] = {
        v: typeof excelCell.value === 'number' ? excelCell.value : value,
        t: typeof excelCell.value === 'number' ? 2 : 1,
        ...(Object.keys(style).length ? { s: style } : {}),
        ...(custom ? { custom } : {})
      }
    }
  }

  for (let columnIndex = 1; columnIndex <= columnCount; columnIndex += 1) {
    const width = excelSheet.getColumn(columnIndex).width
    if (width) {
      columnData[columnIndex - 1] = { w: Math.max(56, Math.round(width * 7)) }
    }
  }

  return {
    id: `guild-schedule-workbook-import-${Date.now()}`,
    name: excelSheet.name || '约战排表',
    appVersion: '0.25.0',
    locale: 'zh-CN',
    sheetOrder: ['sheet-import'],
    sheets: {
      'sheet-import': {
        id: 'sheet-import',
        name: excelSheet.name || '约战排表',
        rowCount: Math.max(rowCount, 20),
        columnCount: Math.max(columnCount, 10),
        defaultRowHeight: 30,
        defaultColumnWidth: 132,
        cellData,
        rowData,
        columnData,
        mergeData: getImportedMergeData(excelSheet, rowCount, columnCount),
        showGridlines: 1
      }
    },
    custom: {
      guildScheduleTempMembers: Array.from(temporaryMembers.values()),
      guildScheduleRegions: { squads: [], teams: [] }
    }
  }
}

function getExcelCellText(cell) {
  const raw = cell?.value
  if (raw === null || raw === undefined) return ''
  if (typeof raw === 'object') {
    if (Array.isArray(raw.richText)) return raw.richText.map(item => item.text || '').join('').trim()
    if (raw.text !== undefined) return String(raw.text).trim()
    if (raw.result !== undefined && raw.result !== null) return String(raw.result).trim()
  }
  return String(cell.text ?? raw).trim()
}

function buildImportedCellStyle(cell) {
  const background = excelColorToCss(cell?.fill?.fgColor)
  const foreground = excelColorToCss(cell?.font?.color)
  const horizontal = {
    left: 1,
    center: 2,
    right: 3,
    justify: 4,
    distributed: 6
  }[cell?.alignment?.horizontal]
  const vertical = {
    top: 1,
    middle: 2,
    bottom: 3
  }[cell?.alignment?.vertical]
  const border = buildImportedBorder(cell?.border)
  const style = {
    ...(background ? { bg: { rgb: background } } : {}),
    ...(foreground ? { cl: { rgb: foreground } } : {}),
    ...(cell?.font?.name ? { ff: cell.font.name } : {}),
    ...(cell?.font?.size ? { fs: Number(cell.font.size) } : {}),
    ...(cell?.font?.bold ? { bl: 1 } : {}),
    ...(cell?.font?.italic ? { it: 1 } : {}),
    ...(horizontal ? { ht: horizontal } : {}),
    ...(vertical ? { vt: vertical } : {}),
    ...(cell?.alignment?.wrapText ? { tb: 3 } : {}),
    ...(border ? { bd: border } : {})
  }
  return style
}

function buildImportedBorder(border) {
  if (!border || typeof border !== 'object') return null
  const sides = {
    top: 't',
    right: 'r',
    bottom: 'b',
    left: 'l'
  }
  const result = {}
  Object.entries(sides).forEach(([excelSide, univerSide]) => {
    const source = border[excelSide]
    const style = EXCEL_BORDER_STYLE[source?.style]
    if (!style) return
    result[univerSide] = {
      s: style,
      cl: { rgb: excelColorToCss(source.color) || '#d6dce8' }
    }
  })
  return Object.keys(result).length ? result : null
}

function excelColorToCss(color) {
  const argb = String(color?.argb || color?.rgb || '').replace('#', '').trim()
  if (/^[0-9a-fA-F]{8}$/.test(argb)) return `#${argb.slice(2)}`
  if (/^[0-9a-fA-F]{6}$/.test(argb)) return `#${argb}`
  return ''
}

function getImportedMergeData(sheet, rowCount, columnCount) {
  const merges = sheet?.model?.merges || []
  return merges.reduce((items, range) => {
    const match = String(range).match(/^([A-Z]+)(\d+):([A-Z]+)(\d+)$/i)
    if (!match) return items
    const startColumn = excelColumnNameToIndex(match[1])
    const endColumn = excelColumnNameToIndex(match[3])
    const startRow = Number(match[2]) - 1
    const endRow = Number(match[4]) - 1
    if (startRow < 0 || startColumn < 0 || endRow >= rowCount || endColumn >= columnCount) return items
    items.push({ startRow, endRow, startColumn, endColumn })
    return items
  }, [])
}

function excelColumnNameToIndex(name) {
  return String(name).toUpperCase().split('').reduce((total, letter) => total * 26 + letter.charCodeAt(0) - 64, 0) - 1
}

function buildTemporaryMember(value, temporaryMembers) {
  if (!looksLikePlayerName(value)) return null
  const existing = temporaryMembers.get(value)
  if (existing) {
    return {
      member_id: existing.member_id,
      player_name: existing.player_name,
      player_class: '',
      is_temporary: true
    }
  }
  const member = {
    member_id: `temp_excel_${stableTextId(value)}`,
    player_name: value,
    player_class: '',
    secondary_class: '',
    is_temporary: true
  }
  temporaryMembers.set(value, member)
  return {
    member_id: member.member_id,
    player_name: member.player_name,
    player_class: '',
    is_temporary: true
  }
}

function looksLikePlayerName(value) {
  const text = String(value || '').trim()
  if (!text || text.length > 30 || /[\r\n]/.test(text)) return false
  if (/^\d+(?:\.\d+)?$/.test(text)) return false
  return !/(排表|小队|团队|队伍|替补|职责|备注|请假|未接龙|成员|名称|位置)/.test(text)
}

function stableTextId(value) {
  let hash = 0
  for (const char of String(value)) {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0
  }
  return hash.toString(36)
}

function resolveCellStyle(cell, styles) {
  if (!cell?.s) return {}
  if (typeof cell.s === 'string') return styles[cell.s] || {}
  return cell.s
}

function normalizeSquadRegion(region) {
  const range = normalizeRegionRange(region?.range)
  const squadId = Number(region?.squad_id)
  if (!range || !Number.isFinite(squadId)) return null
  return {
    region_id: String(region.region_id || `squad-${squadId}`),
    squad_id: squadId,
    squad_name: String(region.squad_name || ''),
    team_id: Number(region.team_id || 0),
    max_members: Number(region.max_members || getRegionCellCount(range)),
    color: String(region.color || '#0ea5e9'),
    range
  }
}

function normalizeTeamRegion(region) {
  const teamId = Number(region?.team_id)
  if (!Number.isFinite(teamId)) return null
  return {
    team_id: teamId,
    team_name: String(region.team_name || ''),
    squad_ids: Array.isArray(region.squad_ids)
      ? region.squad_ids.map(value => Number(value)).filter(Number.isFinite)
      : []
  }
}

function normalizeRegionRange(range) {
  const startRow = Number(range?.start_row)
  const endRow = Number(range?.end_row)
  const startColumn = Number(range?.start_column)
  const endColumn = Number(range?.end_column)
  if ([startRow, endRow, startColumn, endColumn].some(value => !Number.isFinite(value))) return null
  return {
    start_row: Math.min(startRow, endRow),
    end_row: Math.max(startRow, endRow),
    start_column: Math.min(startColumn, endColumn),
    end_column: Math.max(startColumn, endColumn)
  }
}

function getRegionCellCount(range) {
  return (range.end_row - range.start_row + 1) * (range.end_column - range.start_column + 1)
}

function toCssStyle(style) {
  return {
    backgroundColor: normalizeCssColor(style?.bg?.rgb) || '#ffffff',
    color: normalizeCssColor(style?.cl?.rgb) || '#111827',
    fontWeight: style?.bl ? '800' : '500',
    textAlign: 'center',
    verticalAlign: 'middle',
    whiteSpace: 'pre-wrap'
  }
}

function applyExcelCellStyle(excelCell, style, regionBorder = null) {
  const fillColor = normalizeExcelColor(style?.bg?.rgb)
  const fontColor = normalizeExcelColor(style?.cl?.rgb)
  excelCell.alignment = {
    horizontal: 'center',
    vertical: 'middle',
    wrapText: true
  }
  excelCell.font = {
    bold: Boolean(style?.bl),
    color: fontColor ? { argb: fontColor } : undefined,
    size: Number(style?.fs || 11)
  }
  if (fillColor) {
    excelCell.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: fillColor }
    }
  }
  excelCell.border = {
    top: { style: 'thin', color: { argb: 'FFD6DCE8' } },
    left: { style: 'thin', color: { argb: 'FFD6DCE8' } },
    bottom: { style: 'thin', color: { argb: 'FFD6DCE8' } },
    right: { style: 'thin', color: { argb: 'FFD6DCE8' } }
  }
  if (regionBorder) {
    const color = { argb: normalizeExcelColor(regionBorder.color) || 'FF0EA5E9' }
    excelCell.border = {
      ...excelCell.border,
      ...(regionBorder.top ? { top: { style: 'medium', color } } : {}),
      ...(regionBorder.left ? { left: { style: 'medium', color } } : {}),
      ...(regionBorder.bottom ? { bottom: { style: 'medium', color } } : {}),
      ...(regionBorder.right ? { right: { style: 'medium', color } } : {})
    }
  }
}

function getRegionBorder(row, column, regions = []) {
  for (const region of regions) {
    const range = region.range
    if (
      row < range.start_row ||
      row > range.end_row ||
      column < range.start_column ||
      column > range.end_column
    ) {
      continue
    }
    return {
      color: region.color,
      top: row === range.start_row,
      left: column === range.start_column,
      bottom: row === range.end_row,
      right: column === range.end_column
    }
  }
  return null
}

function normalizeCssColor(value) {
  if (!value) return ''
  return String(value).startsWith('#') ? value : `#${String(value).replace(/^#/, '')}`
}

function normalizeExcelColor(value) {
  if (!value) return ''
  const color = String(value).replace('#', '').trim()
  if (color.length === 6) return `FF${color.toUpperCase()}`
  if (color.length === 8) return color.toUpperCase()
  return ''
}

function excelWidthFromPixels(value) {
  return Math.max(8, Math.round((Number(value) || 120) / 7))
}

function excelHeightFromPixels(value) {
  return Math.max(18, Math.round((Number(value) || 30) * 0.75))
}

function pxFromColumnWidth(value) {
  return `${Math.max(56, Number(value) || 120)}px`
}

function pxFromRowHeight(value) {
  return `${Math.max(24, Number(value) || 30)}px`
}

function cellKey(row, column) {
  return `${row}:${column}`
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
