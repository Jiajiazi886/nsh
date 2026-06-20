<template>
  <div class="workbook-table-view">
    <template v-if="tableModel">
      <div class="table-toolbar">
        <div>
          <strong>{{ tableModel.sheetName }}</strong>
          <span>{{ tableModel.rowCount }} 行 x {{ tableModel.columnCount }} 列</span>
        </div>
        <span>
          {{ firstCellLabel }} - {{ lastCellLabel }}
        </span>
      </div>

      <div class="table-scroller">
        <table class="readonly-workbook-table">
          <colgroup>
            <col class="row-header-column" />
            <col
              v-for="column in tableModel.columns"
              :key="column.key"
              :style="{ width: column.width }"
            />
          </colgroup>
          <thead>
            <tr>
              <th class="corner-cell"></th>
              <th
                v-for="column in tableModel.columns"
                :key="column.key"
                class="column-header-cell"
              >
                {{ column.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in tableModel.rows"
              :key="row.key"
              :style="{ height: row.height }"
            >
              <th class="row-header-cell">{{ row.label }}</th>
              <td
                v-for="cell in row.cells"
                :key="cell.key"
                :rowspan="cell.rowspan"
                :colspan="cell.colspan"
                :style="cell.style"
              >
                {{ cell.value }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <el-empty v-else description="暂无自由表格数据" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { buildWorkbookTableModel } from '../utils/scheduleWorkbook'

const props = defineProps({
  workbook: {
    type: Object,
    default: null
  }
})

const tableModel = computed(() => props.workbook ? buildWorkbookTableModel(props.workbook) : null)

const firstCellLabel = computed(() => {
  const range = tableModel.value?.range
  if (!range) return ''
  return `${columnToName(range.minColumn)}${range.minRow + 1}`
})

const lastCellLabel = computed(() => {
  const range = tableModel.value?.range
  if (!range) return ''
  return `${columnToName(range.maxColumn)}${range.maxRow + 1}`
})

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
.workbook-table-view {
  min-height: 300px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
  background: #f8fafc;
  overflow: hidden;
}

.table-toolbar {
  min-height: 42px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.26);
  padding: 8px 10px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(241, 245, 249, 0.92));
  color: #334155;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.table-toolbar > div {
  min-width: 0;
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
}

.table-toolbar strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #0f172a;
}

.table-toolbar span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.table-scroller {
  max-height: 58vh;
  overflow: auto;
  background:
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px) 0 0 / 28px 28px,
    #ffffff;
}

.readonly-workbook-table {
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  width: max-content;
  min-width: 100%;
  font-family: "Microsoft YaHei", "SimSun", sans-serif;
  font-size: 12px;
  color: #111827;
}

.row-header-column {
  width: 46px;
}

.readonly-workbook-table th,
.readonly-workbook-table td {
  border-right: 1px solid #d6dce8;
  border-bottom: 1px solid #d6dce8;
  box-sizing: border-box;
}

.readonly-workbook-table td {
  min-width: 56px;
  padding: 4px 8px;
  line-height: 1.35;
}

.corner-cell,
.column-header-cell {
  position: sticky;
  top: 0;
  z-index: 3;
  height: 28px;
  background: #edf2f7;
  color: #475569;
  font-size: 11px;
  font-weight: 800;
  text-align: center;
}

.corner-cell,
.row-header-cell {
  position: sticky;
  left: 0;
  z-index: 2;
  background: #f1f5f9;
  color: #64748b;
  font-size: 11px;
  font-weight: 800;
  text-align: center;
}

.corner-cell {
  z-index: 4;
}

.row-header-cell {
  padding: 0 6px;
}
</style>
