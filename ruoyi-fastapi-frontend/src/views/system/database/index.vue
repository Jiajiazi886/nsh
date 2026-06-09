<template>
  <div class="app-container database-page">
    <section class="database-hero">
      <div>
        <p class="eyebrow">Super Admin Database</p>
        <h2>数据库管理</h2>
        <p class="hero-copy">超级管理员专用的只读数据库浏览器，可以查看所有表结构、分页数据和完整用户总览。</p>
      </div>
      <div class="hero-metrics">
        <div class="metric">
          <span>数据库</span>
          <strong>{{ overview.databaseName || '-' }}</strong>
        </div>
        <div class="metric">
          <span>类型</span>
          <strong>{{ overview.databaseType || '-' }}</strong>
        </div>
        <div class="metric">
          <span>数据表</span>
          <strong>{{ overview.totalTables || 0 }}</strong>
        </div>
      </div>
    </section>

    <section class="database-workbench">
      <aside class="table-navigator">
        <div class="navigator-head">
          <h3>数据表</h3>
          <el-button text type="primary" :loading="overviewLoading" @click="loadOverview">刷新</el-button>
        </div>
        <el-input v-model="tableKeyword" placeholder="搜索表名" clearable />
        <div class="table-list">
          <button
            v-for="table in filteredTables"
            :key="table.tableName"
            class="table-item"
            :class="{ active: table.tableName === activeTable }"
            type="button"
            @click="selectTable(table.tableName)"
          >
            <span class="table-name">{{ table.tableName }}</span>
            <span class="table-meta">{{ formatRows(table.rowCount) }} 行 · {{ formatBytes(table.dataLength) }}</span>
          </button>
        </div>
      </aside>

      <main class="database-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">{{ activeTable || '请选择数据表' }}</p>
            <h3>{{ activeTable || '数据浏览' }}</h3>
          </div>
          <el-tag type="warning" effect="plain">只读模式</el-tag>
        </div>

        <el-tabs v-model="activeTab" class="database-tabs" @tab-change="handleTabChange">
          <el-tab-pane label="表数据" name="rows">
            <el-table
              v-loading="rowsLoading"
              :data="tableRows.rows"
              border
              height="520"
              empty-text="暂无数据"
            >
              <el-table-column
                v-for="column in tableRows.columns"
                :key="column"
                :prop="column"
                :label="column"
                min-width="150"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span class="cell-value">{{ normalizeCell(row[column]) }}</span>
                </template>
              </el-table-column>
            </el-table>
            <pagination
              v-show="tableRows.total > 0"
              v-model:page="rowQuery.pageNum"
              v-model:limit="rowQuery.pageSize"
              :total="tableRows.total"
              @pagination="loadRows"
            />
          </el-tab-pane>

          <el-tab-pane label="字段结构" name="columns">
            <el-table
              v-loading="columnsLoading"
              :data="columns"
              border
              height="560"
              empty-text="暂无字段"
            >
              <el-table-column prop="ordinalPosition" label="#" width="70" />
              <el-table-column prop="columnName" label="字段名" min-width="160" />
              <el-table-column prop="columnType" label="类型" min-width="150" />
              <el-table-column prop="isNullable" label="允许为空" width="110" />
              <el-table-column prop="columnKey" label="索引" width="100" />
              <el-table-column prop="columnDefault" label="默认值" min-width="140" show-overflow-tooltip />
              <el-table-column prop="columnComment" label="说明" min-width="220" show-overflow-tooltip />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="全部用户数据" name="users">
            <el-table
              v-loading="usersLoading"
              :data="users.rows"
              border
              height="520"
              empty-text="暂无用户"
            >
              <el-table-column prop="userId" label="用户ID" width="90" />
              <el-table-column prop="userName" label="账号" min-width="130" />
              <el-table-column prop="nickName" label="昵称" min-width="130" />
              <el-table-column prop="roleNames" label="角色名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="roleKeys" label="角色符号" min-width="160" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.status === '0' ? 'success' : 'danger'" effect="plain">
                    {{ row.status === '0' ? '正常' : '停用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="loginIp" label="最后登录IP" min-width="150" />
              <el-table-column prop="loginDate" label="最后登录时间" min-width="170" />
              <el-table-column prop="createTime" label="创建时间" min-width="170" />
              <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
            </el-table>
            <pagination
              v-show="users.total > 0"
              v-model:page="userQuery.pageNum"
              v-model:limit="userQuery.pageSize"
              :total="users.total"
              @pagination="loadUsers"
            />
          </el-tab-pane>
        </el-tabs>
      </main>
    </section>
  </div>
</template>

<script setup>
import { getDatabaseOverview, getDatabaseUsers, getTableColumns, getTableRows } from '@/api/system/database'

const overviewLoading = ref(false)
const rowsLoading = ref(false)
const columnsLoading = ref(false)
const usersLoading = ref(false)
const tableKeyword = ref('')
const activeTable = ref('')
const activeTab = ref('rows')

const overview = ref({
  databaseName: '',
  databaseType: '',
  totalTables: 0,
  tables: []
})
const tableRows = ref({
  tableName: '',
  columns: [],
  rows: [],
  total: 0
})
const columns = ref([])
const users = ref({
  rows: [],
  total: 0
})
const rowQuery = reactive({
  pageNum: 1,
  pageSize: 10
})
const userQuery = reactive({
  pageNum: 1,
  pageSize: 10
})

const filteredTables = computed(() => {
  const keyword = tableKeyword.value.trim().toLowerCase()
  if (!keyword) {
    return overview.value.tables
  }
  return overview.value.tables.filter(table => table.tableName.toLowerCase().includes(keyword))
})

onMounted(() => {
  loadOverview()
  loadUsers()
})

async function loadOverview() {
  overviewLoading.value = true
  try {
    const res = await getDatabaseOverview()
    overview.value = res.data || overview.value
    if (!activeTable.value && overview.value.tables.length) {
      await selectTable(overview.value.tables[0].tableName)
    }
  } finally {
    overviewLoading.value = false
  }
}

async function selectTable(tableName) {
  activeTable.value = tableName
  rowQuery.pageNum = 1
  tableRows.value = { tableName, columns: [], rows: [], total: 0 }
  columns.value = []
  if (activeTab.value === 'columns') {
    await loadColumns()
  } else {
    await loadRows()
  }
}

function handleTabChange(tabName) {
  if (tabName === 'columns' && activeTable.value && columns.value.length === 0) {
    loadColumns()
  }
  if (tabName === 'rows' && activeTable.value && tableRows.value.rows.length === 0) {
    loadRows()
  }
  if (tabName === 'users' && users.value.rows.length === 0) {
    loadUsers()
  }
}

async function loadRows() {
  if (!activeTable.value) {
    return
  }
  rowsLoading.value = true
  try {
    const res = await getTableRows(activeTable.value, rowQuery)
    tableRows.value = res.data || tableRows.value
  } finally {
    rowsLoading.value = false
  }
}

async function loadColumns() {
  if (!activeTable.value) {
    return
  }
  columnsLoading.value = true
  try {
    const res = await getTableColumns(activeTable.value)
    columns.value = res.data || []
  } finally {
    columnsLoading.value = false
  }
}

async function loadUsers() {
  usersLoading.value = true
  try {
    const res = await getDatabaseUsers(userQuery)
    users.value = res.data || users.value
  } finally {
    usersLoading.value = false
  }
}

function normalizeCell(value) {
  if (value === null || value === undefined || value === '') {
    return '-'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

function formatRows(value) {
  const numeric = Number(value || 0)
  return numeric.toLocaleString()
}

function formatBytes(value) {
  const numeric = Number(value || 0)
  if (numeric < 1024) {
    return `${numeric}B`
  }
  if (numeric < 1024 * 1024) {
    return `${(numeric / 1024).toFixed(1)}KB`
  }
  return `${(numeric / 1024 / 1024).toFixed(1)}MB`
}
</script>

<style scoped lang="scss">
.database-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.database-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  color: #f8fafc;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(108, 63, 245, 0.42), transparent 38%),
    linear-gradient(115deg, #111827 0%, #2d2d2d 62%, #1f2937 100%);
  box-shadow: 0 24px 70px rgba(17, 24, 39, 0.24);
}

.eyebrow {
  margin: 0 0 8px;
  color: #e8d754;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.database-hero h2,
.database-panel h3,
.table-navigator h3 {
  margin: 0;
}

.database-hero h2 {
  font-size: 30px;
  font-weight: 800;
}

.hero-copy {
  max-width: 580px;
  margin: 10px 0 0;
  color: rgba(248, 250, 252, 0.72);
  line-height: 1.7;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  gap: 12px;
}

.metric {
  min-width: 120px;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
}

.metric span {
  display: block;
  margin-bottom: 8px;
  color: rgba(248, 250, 252, 0.62);
  font-size: 12px;
}

.metric strong {
  display: block;
  color: #fff;
  font-size: 20px;
}

.database-workbench {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
  min-height: 680px;
}

.table-navigator,
.database-panel {
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.74);
  box-shadow: 0 22px 60px rgba(17, 24, 39, 0.12);
  backdrop-filter: blur(14px);
}

.table-navigator {
  padding: 18px;
  overflow: hidden;
}

.navigator-head,
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.table-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 590px;
  margin-top: 14px;
  padding-right: 4px;
  overflow: auto;
}

.table-item {
  width: 100%;
  padding: 13px 14px;
  text-align: left;
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 14px;
  background: rgba(245, 242, 234, 0.82);
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.table-item:hover,
.table-item.active {
  transform: translateY(-1px);
  border-color: rgba(108, 63, 245, 0.42);
  background: #fff;
}

.table-item.active {
  box-shadow: inset 4px 0 0 #6c3ff5;
}

.table-name,
.table-meta {
  display: block;
}

.table-name {
  color: #111827;
  font-size: 14px;
  font-weight: 800;
}

.table-meta {
  margin-top: 6px;
  color: rgba(17, 24, 39, 0.55);
  font-size: 12px;
}

.database-panel {
  min-width: 0;
  padding: 20px;
}

.database-tabs {
  min-width: 0;
}

.cell-value {
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .database-hero,
  .database-workbench {
    grid-template-columns: 1fr;
  }

  .database-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-metrics {
    width: 100%;
  }
}
</style>
