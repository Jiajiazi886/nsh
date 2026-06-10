<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <span>历史数据管理</span>
      </template>

      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        @expand-change="handleExpand"
        row-key="battle_id"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div
              class="expand-container"
              @wheel="handleWheel"
            >
              <el-radio-group v-model="row._filterMode" size="small" style="margin-bottom: 8px">
                <el-radio-button value="all">全部</el-radio-button>
                <el-radio-button v-for="name in guildNames" :key="name" :value="name">{{ name }}</el-radio-button>
              </el-radio-group>

              <div v-if="getCompareSummary(row)" class="compare-bar">
                <span v-for="(g, idx) in getCompareSummary(row)" :key="g.name">
                  <strong>{{ g.name }}</strong> 击败 {{ g.kills }}
                  <span v-if="idx === 0" class="compare-vs">　VS　</span>
                </span>
              </div>
              <el-table
                :data="filterRecords(row)"
                border
                size="small"
                :default-sort="{ prop: 'kills', order: 'descending' }"
                max-height="500"
              >
                <el-table-column prop="guild_name" label="帮会" width="80" fixed />
                <el-table-column prop="player_name" label="玩家" width="120" fixed sortable />
                <el-table-column prop="player_class" label="职业" width="90" sortable>
                  <template #default="{ row: r }">
                    <span class="class-tag" :style="getGuildClassStyle(r.player_class)">
                      {{ r.player_class || '--' }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="kills" label="击败" width="70" sortable />
                <el-table-column prop="qingquan_kills" label="清泉击败" width="90" sortable />
                <el-table-column prop="assists" label="助攻" width="70" sortable />
                <el-table-column prop="resources" label="资源" width="70" sortable />
                <el-table-column prop="dmg_to_players" label="对玩家伤害" width="120" sortable>
                  <template #default="{ row: r }">
                    {{ formatNumber(r.dmg_to_players) }}
                  </template>
                </el-table-column>
                <el-table-column prop="armor_break_players" label="人伤卸甲" width="100" sortable>
                  <template #default="{ row: r }">
                    {{ formatNumber(r.armor_break_players) }}
                  </template>
                </el-table-column>
                <el-table-column prop="dmg_to_buildings" label="对建筑伤害" width="120" sortable>
                  <template #default="{ row: r }">
                    {{ formatNumber(r.dmg_to_buildings) }}
                  </template>
                </el-table-column>
                <el-table-column prop="armor_break_buildings" label="破塔卸甲" width="100" sortable>
                  <template #default="{ row: r }">
                    {{ formatNumber(r.armor_break_buildings) }}
                  </template>
                </el-table-column>
                <el-table-column prop="healing" label="治疗值" width="100" sortable>
                  <template #default="{ row: r }">
                    {{ formatNumber(r.healing) }}
                  </template>
                </el-table-column>
                <el-table-column prop="dmg_taken" label="承受伤害" width="120" sortable>
                  <template #default="{ row: r }">
                    {{ formatNumber(r.dmg_taken) }}
                  </template>
                </el-table-column>
                <el-table-column prop="deaths" label="重伤" width="70" sortable />
                <el-table-column prop="revives" label="复活" width="70" sortable />
                <el-table-column prop="burn_bones" label="焚骨" width="70" sortable />
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="battle_id" label="ID" width="70" />
        <el-table-column prop="battle_name" label="战斗名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="battle_date" label="战斗日期" width="120" />
        <el-table-column prop="battle_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.battle_type === '帮战' ? 'danger' : 'primary'" size="small">
              {{ row.battle_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="battle_result" label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.battle_result === '胜利' ? 'success' : 'danger'" size="small">
              {{ row.battle_result }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="opponent_name" label="对手帮会" width="120" />
        <el-table-column prop="remark" label="备注" min-width="150" show-overflow-tooltip />
        <el-table-column label="击杀对比" width="240">
          <template #default="{ row }">
            <span class="compare-text">{{ getCompareText(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleExport(row)">
              导出数据
            </el-button>
            <el-button type="danger" size="small" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 16px; text-align: right">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBattleList, getBattleRecords, deleteBattle } from '@/api/guild/battle'
import { useGuildClassColors } from '@/utils/guildClassColor'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const guildNames = ref([])
const { getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()

const queryParams = reactive({
  page: 1,
  size: 10,
})

const CSV_HEADER = [
  '玩家名字',
  '职业',
  '击败/清泉',
  '助攻',
  '资源',
  '对玩家伤害',
  '人伤卸甲',
  '对建筑伤害',
  '破塔卸甲',
  '治疗值',
  '承受伤害',
  '重伤',
  '复活/清泉',
  '焚骨',
]

function formatNumber(num) {
  if (num == null || num === 0) return '0'
  if (num >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num.toLocaleString()
}

function getCompareSummary(row) {
  const records = row.records
  if (!records || records.length === 0) return null
  const map = {}
  records.forEach(r => {
    if (!map[r.guild_name]) {
      map[r.guild_name] = { name: r.guild_name, kills: 0 }
    }
    map[r.guild_name].kills += (r.kills || 0) + (r.qingquan_kills || 0)
  })
  return Object.values(map)
}

function getCompareText(row) {
  const summary = getCompareSummary(row)
  if (!summary) return '-'
  return summary.map(g => `${g.name}${g.kills}`).join('VS')
}

function filterRecords(row) {
  const records = row.records || []
  const mode = row._filterMode || 'all'
  if (mode === 'all') return records
  return records.filter(r => r.guild_name === mode)
}

function handleWheel(event) {
  if (!event.ctrlKey) return
  event.preventDefault()
  event.currentTarget.scrollLeft += event.deltaY
}

function normalizeNumber(value) {
  return Number.isFinite(Number(value)) ? Number(value) : 0
}

function escapeCsvField(value) {
  const text = value == null ? '' : String(value)
  return `"${text.replace(/"/g, '""')}"`
}

function sanitizeFilename(name) {
  return (name || 'battle-records')
    .replace(/[\\/:*?"<>|]/g, '_')
    .trim() || 'battle-records'
}

function buildCsvRow(columns) {
  return columns.map(escapeCsvField).join(',')
}

function buildRecordRow(record) {
  return buildCsvRow([
    record.player_name || '',
    record.player_class || '',
    `${normalizeNumber(record.kills)}/${normalizeNumber(record.qingquan_kills)}`,
    normalizeNumber(record.assists),
    normalizeNumber(record.resources),
    normalizeNumber(record.dmg_to_players),
    normalizeNumber(record.armor_break_players),
    normalizeNumber(record.dmg_to_buildings),
    normalizeNumber(record.armor_break_buildings),
    normalizeNumber(record.healing),
    normalizeNumber(record.dmg_taken),
    normalizeNumber(record.deaths),
    normalizeNumber(record.revives),
    normalizeNumber(record.burn_bones),
  ])
}

function buildBattleCsv(row) {
  const records = Array.isArray(row.records) ? row.records : []
  if (records.length === 0) return ''

  const guildMap = new Map()
  records.forEach((record) => {
    const guildName = record.guild_name || '未知帮会'
    if (!guildMap.has(guildName)) {
      guildMap.set(guildName, [])
    }
    guildMap.get(guildName).push(record)
  })

  return Array.from(guildMap.entries())
    .map(([guildName, guildRecords]) => {
      const lines = [
        buildCsvRow([guildName, guildRecords.length]),
        buildCsvRow(CSV_HEADER),
        ...guildRecords.map(buildRecordRow),
      ]
      return lines.join('\r\n')
    })
    .join('\r\n\r\n')
}

function downloadCsvFile(content, filename) {
  const blob = new Blob([`\uFEFF${content}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function handleExport(row) {
  if (!Array.isArray(row.records) || row.records.length === 0) {
    ElMessage.warning('暂无可导出的明细数据')
    return
  }

  const content = buildBattleCsv(row)
  if (!content) {
    ElMessage.warning('暂无可导出的明细数据')
    return
  }

  const filename = `${sanitizeFilename(row.battle_name || `battle_${row.battle_id}`)}.csv`
  downloadCsvFile(content, filename)
  ElMessage.success('导出成功')
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getBattleList({ page: queryParams.page, size: queryParams.size })
    const data = res.data || res
    const rows = (data.rows || []).map(item => ({ ...item, records: null, _filterMode: 'all' }))
    total.value = data.total || 0
    guildNames.value = data.guild_names || []

    const promises = rows.map(async (row) => {
      try {
        const rs = await getBattleRecords(row.battle_id)
        const rdata = rs.data || rs
        row.records = Array.isArray(rdata) ? rdata : []
      } catch {
        row.records = []
      }
    })
    await Promise.all(promises)
    tableData.value = rows
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleExpand(row, expandedRows) {
  const isExpanding = expandedRows.some(r => r.battle_id === row.battle_id)
  if (!isExpanding || row.records) return
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${row.battle_name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteBattle(row.battle_id)
    ElMessage.success('删除成功')
    await fetchList()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchList()
  loadGuildClassColors()
})
</script>

<style scoped>
.expand-container {
  padding: 10px 20px;
}

.compare-bar {
  margin-bottom: 8px;
  padding: 8px 12px;
  background: #f0f9eb;
  border-radius: 4px;
  font-size: 14px;
  color: #303133;
}

.compare-vs {
  color: #e6a23c;
  font-weight: bold;
}

.compare-hint {
  color: #c0c4cc;
  font-size: 13px;
}

.compare-text {
  font-size: 13px;
  color: #606266;
}

.class-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  padding: 2px 8px;
  border: 1px solid currentColor;
  border-radius: 999px;
  background: var(--el-fill-color-light);
  font-size: 12px;
  font-weight: 700;
}
</style>
