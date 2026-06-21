import ExcelJS from 'exceljs'
import { saveAs } from 'file-saver'

const DEFAULT_PREVIEW_ROW_LIMIT = 80
const DEFAULT_PREVIEW_COLUMN_LIMIT = 40
const DEFAULT_EXPORT_ROW_LIMIT = 2000
const DEFAULT_EXPORT_COLUMN_LIMIT = 200

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
