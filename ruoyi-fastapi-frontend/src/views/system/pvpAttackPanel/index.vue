<template>
  <div class="app-container attack-panel-page">
    <el-form :model="queryParams" inline class="query-bar" @submit.prevent>
      <el-form-item label="面板名称">
        <el-input v-model="queryParams.panelName" clearable placeholder="请输入面板名称" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="queryParams.status" clearable placeholder="全部状态">
          <el-option label="启用" value="0" />
          <el-option label="停用" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">查询</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <div class="toolbar">
      <el-button v-hasPermi="['system:pvp-attack-panel:add']" type="primary" icon="Plus" @click="handleAdd">新增面板</el-button>
      <el-button v-hasPermi="['system:pvp-attack-panel:edit']" :disabled="selectedRows.length !== 1" icon="Edit" @click="handleEdit()">编辑</el-button>
      <el-button v-hasPermi="['system:pvp-attack-panel:remove']" :disabled="!selectedRows.length" type="danger" plain icon="Delete" @click="handleDelete()">删除</el-button>
      <el-button v-hasPermi="['system:pvp-attack-panel:add']" icon="Upload" @click="openJsonDialog('import')">导入 JSON</el-button>
      <el-button :disabled="selectedRows.length !== 1" icon="Download" @click="openJsonDialog('export')">导出 JSON</el-button>
      <el-button icon="DocumentCopy" @click="openJsonDialog('example')">示例 JSON</el-button>
    </div>

    <el-table v-loading="loading" :data="rows" @selection-change="selectedRows = $event">
      <el-table-column type="selection" width="52" />
      <el-table-column prop="panelName" label="面板名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="attack" label="攻击" width="100" align="right" />
      <el-table-column prop="breakDefense" label="破防" width="100" align="right" />
      <el-table-column prop="restraintValue" label="克制" width="100" align="right" />
      <el-table-column prop="crit" label="会心" width="100" align="right" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.status" active-value="0" inactive-value="1" @change="changeStatus(row)" />
        </template>
      </el-table-column>
      <el-table-column prop="updateTime" label="更新时间" width="170">
        <template #default="{ row }">{{ parseTime(row.updateTime) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="92" fixed="right">
        <template #default="{ row }">
          <el-button v-hasPermi="['system:pvp-attack-panel:edit']" link type="primary" icon="Edit" @click="handleEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" :total="total" @pagination="getList" />

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="820px" append-to-body @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="116px" @submit.prevent>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="面板名称" prop="panelName"><el-input v-model.trim="form.panelName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="状态"><el-radio-group v-model="form.status"><el-radio value="0">启用</el-radio><el-radio value="1">停用</el-radio></el-radio-group></el-form-item></el-col>
          <el-col v-for="field in coreFields" :key="field.key" :span="8">
            <el-form-item :label="field.label"><el-input-number v-model="form[field.key]" :precision="field.precision || 0" :step="field.step || 1" :min="0" controls-position="right" style="width: 100%" /></el-form-item>
          </el-col>
          <el-col :span="24">
            <el-collapse>
              <el-collapse-item title="额外伤害乘区" name="advanced">
                <el-row :gutter="16">
                  <el-col v-for="field in advancedFields" :key="field.key" :span="8">
                    <el-form-item :label="field.label"><el-input-number v-model="form[field.key]" :precision="3" :step="0.01" :min="0" controls-position="right" style="width: 100%" /></el-form-item>
                  </el-col>
                </el-row>
              </el-collapse-item>
            </el-collapse>
          </el-col>
          <el-col :span="24"><el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="3" maxlength="500" show-word-limit /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitForm">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="jsonDialog.visible" :title="jsonDialog.title" width="720px" append-to-body>
      <p class="json-help">{{ jsonDialog.mode === 'import' ? '粘贴单个中文字段面板对象，校验后将回填新增表单。' : 'JSON 中的百分比数值按面板当前值原样输出。' }}</p>
      <el-input v-model="jsonDialog.text" type="textarea" :rows="20" resize="vertical" :readonly="jsonDialog.mode !== 'import'" spellcheck="false" />
      <template #footer>
        <el-button @click="jsonDialog.visible = false">关闭</el-button>
        <el-button v-if="jsonDialog.mode !== 'import'" v-copyText="jsonDialog.text" v-copyText:callback="copyJsonSuccess" icon="DocumentCopy">复制</el-button>
        <el-button v-else type="primary" icon="Check" @click="applyJsonImport">校验并回填</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="SystemPvpAttackPanel">
import {
  addPvpAttackPanel,
  changePvpAttackPanelStatus,
  deletePvpAttackPanel,
  getPvpAttackPanel,
  listPvpAttackPanels,
  updatePvpAttackPanel
} from '@/api/system/pvpAttackPanel'
import { formatAttackPanelJson, formatAttackPanelJsonExample, parseAttackPanelJson } from '@/utils/pvpAttackPanelJson'

const { proxy } = getCurrentInstance()
const formRef = ref()
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const rows = ref([])
const total = ref(0)
const selectedRows = ref([])
const jsonDialog = reactive({ visible: false, mode: 'example', title: '', text: '' })
const queryParams = reactive({ pageNum: 1, pageSize: 10, panelName: '', status: undefined })
const form = reactive(createForm())
const rules = { panelName: [{ required: true, message: '请输入面板名称', trigger: 'blur' }] }

const coreFields = [
  { key: 'attack', label: '攻击' }, { key: 'breakDefense', label: '破防' }, { key: 'restraintValue', label: '克制数值' },
  { key: 'crit', label: '会心' }, { key: 'critDmg', label: '会伤增幅', precision: 3, step: 0.01 }, { key: 'extraCritRate', label: '额外会心率', precision: 3, step: 0.01 },
  { key: 'restraintPct', label: '流派克制', precision: 3, step: 0.01 },
  { key: 'skillBonus', label: '技能增强' }, { key: 'skillBonusPct', label: '技能增强%', precision: 3, step: 0.01 }, { key: 'techniqueRestraint', label: '技巧克制' }
]
const advancedFields = [
  { key: 'internalBonus', label: '内功增伤' }, { key: 'gearBonus', label: '装备增伤' }, { key: 'martialBonus', label: '武蕴增伤' }, { key: 'otherBonus', label: '其他增伤' }
]

onMounted(getList)

async function getList() {
  loading.value = true
  try {
    const res = await listPvpAttackPanels(queryParams)
    rows.value = res.rows || []
    total.value = Number(res.total || 0)
  } finally { loading.value = false }
}

function handleQuery() { queryParams.pageNum = 1; getList() }
function resetQuery() { queryParams.panelName = ''; queryParams.status = undefined; handleQuery() }
function handleAdd() { resetForm(); dialogTitle.value = '新增进攻方面板'; dialogVisible.value = true }

function openJsonDialog(mode) {
  jsonDialog.mode = mode
  if (mode === 'import') {
    jsonDialog.title = '导入进攻方面板 JSON'
    jsonDialog.text = formatAttackPanelJsonExample()
  } else if (mode === 'export') {
    const panel = selectedRows.value[0]
    if (!panel) return
    jsonDialog.title = `导出 ${panel.panelName}`
    jsonDialog.text = formatAttackPanelJson(panel)
  } else {
    jsonDialog.title = '进攻方面板示例 JSON'
    jsonDialog.text = formatAttackPanelJsonExample()
  }
  jsonDialog.visible = true
}

function applyJsonImport() {
  try {
    const imported = parseAttackPanelJson(jsonDialog.text)
    resetForm(imported)
    dialogTitle.value = '新增进攻方面板'
    jsonDialog.visible = false
    dialogVisible.value = true
    proxy.$modal.msgSuccess('JSON 校验通过，请确认后保存')
  } catch (error) {
    proxy.$modal.msgError(error.message || 'JSON 导入失败')
  }
}

function copyJsonSuccess() {
  proxy.$modal.msgSuccess('JSON 已复制')
}

async function handleEdit(row) {
  const target = row || selectedRows.value[0]
  if (!target?.panelId) return
  const res = await getPvpAttackPanel(target.panelId)
  resetForm(res.data)
  dialogTitle.value = '编辑进攻方面板'
  dialogVisible.value = true
}

async function changeStatus(row) {
  try {
    await changePvpAttackPanelStatus(row.panelId, { status: row.status })
    proxy.$modal.msgSuccess('状态已更新')
  } catch { row.status = row.status === '0' ? '1' : '0' }
}

async function handleDelete(row) {
  const items = row ? [row] : selectedRows.value
  const ids = items.map(item => item.panelId).filter(Boolean)
  if (!ids.length) return
  await proxy.$modal.confirm(`确定删除选中的 ${ids.length} 套进攻方面板吗？`)
  await deletePvpAttackPanel(ids.join(','))
  proxy.$modal.msgSuccess('删除成功')
  getList()
}

function submitForm() {
  formRef.value?.validate(async valid => {
    if (!valid) return
    saving.value = true
    try {
      if (form.panelId) await updatePvpAttackPanel(form)
      else await addPvpAttackPanel(form)
      proxy.$modal.msgSuccess('保存成功')
      dialogVisible.value = false
      getList()
    } finally { saving.value = false }
  })
}

function resetForm(source = null) {
  Object.assign(form, createForm(), source || {})
  nextTick(() => formRef.value?.clearValidate())
}

function createForm() {
  return { panelId: undefined, panelName: '', status: '0', remark: '', attack: 1750, breakDefense: 1100, restraintValue: 285, crit: 1100, critDmg: 0.575, extraCritRate: 0, restraintPct: 0, skillBonus: 0, skillBonusPct: 0, internalBonus: 0, gearBonus: 0, martialBonus: 0, otherBonus: 0, techniqueRestraint: 0 }
}
</script>

<style scoped>
.attack-panel-page { display: grid; gap: 14px; }
.query-bar { margin-bottom: 0; }
.toolbar { display: flex; gap: 8px; }
.json-help { margin: 0 0 12px; color: #68788c; font-size: 13px; }
.toolbar { flex-wrap: wrap; }
</style>
