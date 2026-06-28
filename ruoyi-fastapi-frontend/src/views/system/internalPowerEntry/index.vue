<template>
  <div class="app-container internal-power-entry-admin">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="76px">
      <el-form-item label="词条名称" prop="entryName">
        <el-input v-model.trim="queryParams.entryName" clearable placeholder="请输入词条名称" style="width: 220px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" clearable placeholder="全部状态" style="width: 160px">
          <el-option label="正常" value="0" />
          <el-option label="停用" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['system:internal-power-entry:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="success" plain icon="Edit" :disabled="single" @click="handleUpdate" v-hasPermi="['system:internal-power-entry:edit']">修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['system:internal-power-entry:remove']">删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList" />
    </el-row>

    <el-table v-loading="loading" :data="entryList" border stripe @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="词条ID" prop="entryId" align="center" width="90" />
      <el-table-column label="词条名称" prop="entryName" min-width="180" :show-overflow-tooltip="true" />
      <el-table-column label="转换百分比" align="center" width="140">
        <template #default="{ row }">
          <span class="percent-cell" :class="{ empty: row.conversionPercent === null || row.conversionPercent === undefined }">
            {{ formatPercent(row.conversionPercent) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="转换说明" prop="conversionDesc" min-width="240" :show-overflow-tooltip="true">
        <template #default="{ row }">
          <span>{{ row.conversionDesc || '待配置转换公式' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" align="center" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === '0' ? 'success' : 'info'">{{ row.status === '0' ? '正常' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" prop="updateTime" align="center" width="180">
        <template #default="{ row }">
          <span>{{ parseTime(row.updateTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(row)" v-hasPermi="['system:internal-power-entry:edit']">修改</el-button>
          <el-button link type="primary" icon="Delete" @click="handleDelete(row)" v-hasPermi="['system:internal-power-entry:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <el-drawer v-model="open" :title="title" size="min(620px, 96vw)" append-to-body destroy-on-close>
      <el-form ref="entryRef" :model="form" :rules="rules" label-position="top" class="entry-form">
        <el-form-item label="词条名称" prop="entryName">
          <el-input v-model.trim="form.entryName" maxlength="64" show-word-limit placeholder="例如：攻击" />
        </el-form-item>
        <el-form-item label="数值转换百分比">
          <el-input-number
            v-model="form.conversionPercent"
            :min="0"
            :max="100"
            :precision="4"
            controls-position="right"
            placeholder="暂未配置"
            style="width: 220px"
          />
          <p class="field-hint">可以留空；后续做词条数值公式时再填写。</p>
        </el-form-item>
        <el-form-item label="转换说明">
          <el-input v-model.trim="form.conversionDesc" type="textarea" :rows="3" maxlength="255" show-word-limit placeholder="记录这个词条如何换算为百分比，当前可留空。" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="0">正常</el-radio>
            <el-radio value="1">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model.trim="form.remark" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <span>个人内功页只能选择状态为“正常”的词条。</span>
          <div>
            <el-button @click="cancel">取消</el-button>
            <el-button type="primary" @click="submitForm">确定</el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup name="SystemInternalPowerEntry">
import {
  addInternalPowerEntry,
  delInternalPowerEntry,
  getInternalPowerEntry,
  listInternalPowerEntry,
  updateInternalPowerEntry
} from '@/api/system/internalPowerEntry'

const { proxy } = getCurrentInstance()

const entryList = ref([])
const loading = ref(true)
const showSearch = ref(true)
const open = ref(false)
const title = ref('')
const ids = ref([])
const single = ref(true)
const multiple = ref(true)
const total = ref(0)

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    entryName: undefined,
    status: undefined
  },
  rules: {
    entryName: [{ required: true, message: '词条名称不能为空', trigger: 'blur' }]
  }
})

const { queryParams, form, rules } = toRefs(data)

function getList() {
  loading.value = true
  listInternalPowerEntry(queryParams.value).then(response => {
    entryList.value = (response.rows || []).map(normalizeEntry)
    total.value = response.total || 0
    loading.value = false
  }).catch(() => {
    loading.value = false
  })
}

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

function reset() {
  form.value = normalizeEntry({
    entryId: undefined,
    entryName: '',
    conversionPercent: null,
    conversionDesc: '',
    status: '0',
    remark: ''
  })
  proxy.resetForm('entryRef')
}

function handleAdd() {
  reset()
  open.value = true
  title.value = '新增内功词条'
}

function handleUpdate(row) {
  reset()
  const entryId = row.entryId || ids.value
  getInternalPowerEntry(entryId).then(response => {
    form.value = normalizeEntry(response.data)
    open.value = true
    title.value = '修改内功词条'
  })
}

function submitForm() {
  proxy.$refs.entryRef.validate(valid => {
    if (!valid) return
    const payload = toPayload(form.value)
    const request = payload.entryId ? updateInternalPowerEntry(payload) : addInternalPowerEntry(payload)
    request.then(() => {
      proxy.$modal.msgSuccess(payload.entryId ? '修改成功' : '新增成功')
      open.value = false
      getList()
    })
  })
}

function handleDelete(row) {
  const entryIds = row.entryId || ids.value
  proxy.$modal.confirm(`是否确认删除内功词条编号为"${entryIds}"的数据项？`).then(() => {
    return delInternalPowerEntry(entryIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.entryId)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

function cancel() {
  open.value = false
  reset()
}

function normalizeEntry(value = {}) {
  const percent = value.conversionPercent
  return {
    entryId: value.entryId,
    entryName: value.entryName || '',
    conversionPercent: percent === null || percent === undefined || percent === '' ? null : Number(percent),
    conversionDesc: value.conversionDesc || '',
    status: value.status || '0',
    remark: value.remark || '',
    createTime: value.createTime,
    updateTime: value.updateTime
  }
}

function toPayload(value) {
  return normalizeEntry(value)
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') return '未配置'
  return `${Number(value || 0).toFixed(4)}%`
}

getList()
</script>

<style scoped>
.internal-power-entry-admin {
  --line: rgba(32, 38, 52, 0.12);
}

.percent-cell {
  color: #2563eb;
  font-weight: 900;
}

.percent-cell.empty {
  color: #94a3b8;
}

.entry-form {
  padding-right: 8px;
}

.field-hint {
  width: 100%;
  margin: 8px 0 0;
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.drawer-footer span {
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.drawer-footer > div {
  display: flex;
  gap: 8px;
}
</style>
