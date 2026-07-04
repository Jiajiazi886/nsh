<template>
  <div class="app-container formula-design-page">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="76px">
      <el-form-item label="版本名称" prop="versionName">
        <el-input v-model.trim="queryParams.versionName" clearable placeholder="请输入版本名称" style="width: 220px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" clearable placeholder="全部状态" style="width: 160px">
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
          <el-option label="历史" value="archived" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAddDefault" v-hasPermi="['system:formula-design:add']">新增默认草稿</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="success" plain icon="RefreshRight" @click="loadActiveAsDraft" v-hasPermi="['system:formula-design:add']">从当前发布复制</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList" />
    </el-row>

    <el-table v-loading="loading" :data="versionList" border stripe>
      <el-table-column label="版本ID" prop="versionId" width="90" align="center" />
      <el-table-column label="版本名称" prop="versionName" min-width="220" :show-overflow-tooltip="true" />
      <el-table-column label="状态" align="center" width="110">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发布时间" align="center" width="180">
        <template #default="{ row }">
          <span>{{ parseTime(row.publishTime) || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" align="center" width="180">
        <template #default="{ row }">
          <span>{{ parseTime(row.updateTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="备注" prop="remark" min-width="180" :show-overflow-tooltip="true" />
      <el-table-column label="操作" align="center" width="320" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" icon="View" @click="handleDetail(row)">查看</el-button>
          <el-button v-if="row.status === 'draft'" link type="primary" icon="Edit" @click="handleEdit(row)" v-hasPermi="['system:formula-design:edit']">编辑</el-button>
          <el-button link type="primary" icon="CopyDocument" @click="handleCopy(row)" v-hasPermi="['system:formula-design:add']">复制</el-button>
          <el-button v-if="row.status === 'draft'" link type="primary" icon="Promotion" @click="handlePublish(row)" v-hasPermi="['system:formula-design:publish']">发布</el-button>
          <el-button v-if="row.status !== 'published'" link type="primary" icon="RefreshLeft" @click="handleRollback(row)" v-hasPermi="['system:formula-design:publish']">回滚</el-button>
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

    <el-drawer v-model="open" :title="title" size="min(1120px, 96vw)" append-to-body destroy-on-close>
      <el-form ref="formulaRef" :model="form" :rules="rules" label-position="top" class="formula-form">
        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="版本名称" prop="versionName">
              <el-input v-model.trim="form.versionName" :disabled="readonly" maxlength="100" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="备注">
              <el-input v-model.trim="form.remark" :disabled="readonly" maxlength="500" show-word-limit />
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert v-if="readonly" type="info" show-icon :closable="false" title="已发布和历史版本只读；需要修改时请先复制为草稿。" />

        <el-tabs v-model="activeTab" class="formula-tabs">
          <el-tab-pane label="默认面板" name="defaults">
            <div class="panel-grid">
              <section>
                <h3>受击方面板</h3>
                <el-table :data="targetDefaultRows" border size="small">
                  <el-table-column label="字段" prop="key" width="160" />
                  <el-table-column label="数值">
                    <template #default="{ row }">
                      <el-input-number v-model="form.formulaPackage.defaults.targetPanel[row.key]" :disabled="readonly" controls-position="right" />
                    </template>
                  </el-table-column>
                </el-table>
              </section>
              <section>
                <h3>攻击方无内功基础面板</h3>
                <el-table :data="attackDefaultRows" border size="small">
                  <el-table-column label="字段" prop="key" width="160" />
                  <el-table-column label="数值">
                    <template #default="{ row }">
                      <el-input-number v-model="form.formulaPackage.defaults.attackPanel[row.key]" :disabled="readonly" controls-position="right" />
                    </template>
                  </el-table-column>
                </el-table>
              </section>
            </div>
          </el-tab-pane>

          <el-tab-pane label="字段映射" name="fields">
            <el-table :data="fieldRows" border size="small">
              <el-table-column label="分组" prop="group" width="100" />
              <el-table-column label="Key" prop="key" width="170" />
              <el-table-column label="名称" min-width="160">
                <template #default="{ row }">
                  <el-input v-model.trim="row.label" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="类型" width="130">
                <template #default="{ row }">
                  <el-select v-model="row.type" :disabled="readonly">
                    <el-option label="数值" value="number" />
                    <el-option label="百分比" value="percent" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="单元格" width="130">
                <template #default="{ row }">
                  <el-input v-model.trim="row.cell" :disabled="readonly" />
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="固定单元格" name="fixedCells">
            <el-button class="mb8" type="primary" plain icon="Plus" :disabled="readonly" @click="addFixedCell">添加固定单元格</el-button>
            <el-table :data="form.formulaPackage.fixedCells" border size="small">
              <el-table-column label="说明" min-width="160">
                <template #default="{ row }">
                  <el-input v-model.trim="row.label" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="表" width="160">
                <template #default="{ row }">
                  <el-input v-model.trim="row.sheet" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="单元格" width="130">
                <template #default="{ row }">
                  <el-input v-model.trim="row.cell" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="值" width="180">
                <template #default="{ row }">
                  <el-input-number v-model="row.value" :disabled="readonly" controls-position="right" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="90" align="center">
                <template #default="{ $index }">
                  <el-button link type="danger" :disabled="readonly" @click="form.formulaPackage.fixedCells.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="词条换算" name="entryRules">
            <el-button class="mb8" type="primary" plain icon="Plus" :disabled="readonly" @click="addEntryRule">添加词条规则</el-button>
            <el-table :data="form.formulaPackage.entryRules" border size="small">
              <el-table-column label="词条" min-width="150">
                <template #default="{ row }">
                  <el-input v-model.trim="row.name" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="上限" width="110">
                <template #default="{ row }">
                  <el-input v-model.trim="row.max" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="类型" width="120">
                <template #default="{ row }">
                  <el-select v-model="row.type" :disabled="readonly">
                    <el-option label="数值" value="number" />
                    <el-option label="百分比" value="percent" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="收益影响（JSON数组）" min-width="260">
                <template #default="{ row }">
                  <el-input v-model="row.effectsText" :disabled="readonly" placeholder='[{"key":"attack","factor":1}]' @blur="syncRuleEffects(row)" />
                </template>
              </el-table-column>
              <el-table-column label="不计入说明" min-width="220">
                <template #default="{ row }">
                  <el-input v-model.trim="row.ignoredNote" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="90" align="center">
                <template #default="{ $index }">
                  <el-button link type="danger" :disabled="readonly" @click="form.formulaPackage.entryRules.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="收益预设" name="benefitPresets">
            <el-button class="mb8" type="primary" plain icon="Plus" :disabled="readonly" @click="addBenefitPreset">添加收益预设</el-button>
            <el-table :data="form.formulaPackage.benefitPresets" border size="small">
              <el-table-column label="标签" min-width="180">
                <template #default="{ row }">
                  <el-input v-model.trim="row.label" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="增量JSON" min-width="260">
                <template #default="{ row }">
                  <el-input v-model="row.deltaText" :disabled="readonly" placeholder='{"attack":33}' @blur="syncPresetDelta(row)" />
                </template>
              </el-table-column>
              <el-table-column label="说明" min-width="260">
                <template #default="{ row }">
                  <el-input v-model.trim="row.explain" :disabled="readonly" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="90" align="center">
                <template #default="{ $index }">
                  <el-button link type="danger" :disabled="readonly" @click="form.formulaPackage.benefitPresets.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="高级 JSON" name="json">
            <div class="json-toolbar">
              <el-button icon="Refresh" @click="syncJsonFromPackage">从表格生成 JSON</el-button>
              <el-button type="primary" icon="Check" :disabled="readonly" @click="applyJsonToPackage">应用 JSON 到表格</el-button>
            </div>
            <el-input
              v-model="packageText"
              type="textarea"
              :rows="24"
              :disabled="readonly"
              spellcheck="false"
              class="json-editor"
            />
          </el-tab-pane>
        </el-tabs>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <span>{{ form.status === 'draft' ? '发布后会影响所有用户的内功收益计算。' : '复制为草稿后才能修改。' }}</span>
          <div>
            <el-button @click="open = false">关闭</el-button>
            <el-button v-if="form.status === 'draft'" type="primary" @click="submitForm" v-hasPermi="['system:formula-design:edit']">保存草稿</el-button>
            <el-button v-if="form.status === 'draft' && form.versionId" type="success" @click="handlePublish(form)" v-hasPermi="['system:formula-design:publish']">发布</el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup name="SystemFormulaDesign">
import {
  addFormulaVersion,
  copyFormulaVersion,
  getActiveFormulaVersion,
  getFormulaVersion,
  listFormulaVersion,
  publishFormulaVersion,
  rollbackFormulaVersion,
  updateFormulaVersion
} from '@/api/system/formulaDesign'
import {
  FORMULA_SCOPE_INTERNAL_POWER_PVP,
  createDefaultFormulaPackage,
  normalizeFormulaPackage
} from '@/utils/internalPowerBenefit'

const { proxy } = getCurrentInstance()

const loading = ref(true)
const showSearch = ref(true)
const versionList = ref([])
const total = ref(0)
const open = ref(false)
const title = ref('')
const activeTab = ref('defaults')
const packageText = ref('')

const data = reactive({
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    versionName: undefined,
    formulaScope: FORMULA_SCOPE_INTERNAL_POWER_PVP,
    status: undefined
  },
  form: createEmptyForm(),
  rules: {
    versionName: [{ required: true, message: '版本名称不能为空', trigger: 'blur' }]
  }
})

const { queryParams, form, rules } = toRefs(data)

const readonly = computed(() => form.value.status !== 'draft')
const targetDefaultRows = computed(() => Object.keys(form.value.formulaPackage.defaults.targetPanel || {}).map(key => ({ key })))
const attackDefaultRows = computed(() => Object.keys(form.value.formulaPackage.defaults.attackPanel || {}).map(key => ({ key })))
const fieldRows = computed(() => {
  const target = form.value.formulaPackage.fields.target || []
  const attack = form.value.formulaPackage.fields.attack || []
  target.forEach(item => {
    item.group = '受击方'
  })
  attack.forEach(item => {
    item.group = '攻击方'
  })
  return [...target, ...attack]
})

function getList() {
  loading.value = true
  listFormulaVersion(queryParams.value).then(response => {
    versionList.value = response.rows || []
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

function handleAddDefault() {
  resetForm({
    versionName: `内功PVP伤害公式 ${new Date().toLocaleString('zh-CN')}`,
    status: 'draft',
    formulaPackage: createDefaultFormulaPackage()
  })
  open.value = true
  title.value = '新增公式草稿'
}

async function loadActiveAsDraft() {
  try {
    const response = await getActiveFormulaVersion(FORMULA_SCOPE_INTERNAL_POWER_PVP)
    const source = normalizeFormulaPackage(response.data?.formulaPackage || {})
    resetForm({
      versionName: `${response.data?.versionName || '当前发布公式'} 副本`,
      status: 'draft',
      formulaPackage: source,
      remark: response.data?.remark || ''
    })
    open.value = true
    title.value = '从当前发布复制'
  } catch {
    proxy.$modal.msgError('当前发布公式加载失败')
  }
}

function handleDetail(row) {
  openDetail(row.versionId, true)
}

function handleEdit(row) {
  openDetail(row.versionId, false)
}

async function openDetail(versionId) {
  const response = await getFormulaVersion(versionId)
  resetForm(response.data || {})
  open.value = true
  title.value = form.value.status === 'draft' ? '编辑公式草稿' : '查看公式版本'
}

async function handleCopy(row) {
  await copyFormulaVersion(row.versionId)
  proxy.$modal.msgSuccess('复制成功')
  getList()
}

async function handlePublish(row) {
  await proxy.$modal.confirm(`发布"${row.versionName}"后会影响所有用户的内功收益计算，是否继续？`)
  await publishFormulaVersion(row.versionId)
  proxy.$modal.msgSuccess('发布成功')
  open.value = false
  getList()
}

async function handleRollback(row) {
  await proxy.$modal.confirm(`将"${row.versionName}"复制并发布为当前公式，是否继续？`)
  await rollbackFormulaVersion(row.versionId)
  proxy.$modal.msgSuccess('回滚发布成功')
  getList()
}

function submitForm() {
  proxy.$refs.formulaRef.validate(async valid => {
    if (!valid) return
    syncJsonFromPackage()
    const payload = toPayload(form.value)
    if (payload.versionId) {
      await updateFormulaVersion(payload)
      proxy.$modal.msgSuccess('保存成功')
    } else {
      await addFormulaVersion(payload)
      proxy.$modal.msgSuccess('新增成功')
    }
    open.value = false
    getList()
  })
}

function resetForm(value = {}) {
  const pkg = normalizeEditablePackage(value.formulaPackage || value.formula_package || createDefaultFormulaPackage())
  form.value = {
    ...createEmptyForm(),
    ...value,
    formulaScope: FORMULA_SCOPE_INTERNAL_POWER_PVP,
    status: value.status || 'draft',
    formulaPackage: pkg
  }
  syncJsonFromPackage()
}

function createEmptyForm() {
  return {
    versionId: undefined,
    versionName: '',
    formulaScope: FORMULA_SCOPE_INTERNAL_POWER_PVP,
    status: 'draft',
    formulaPackage: createDefaultFormulaPackage(),
    remark: ''
  }
}

function normalizeEditablePackage(value) {
  const pkg = normalizeFormulaPackage(value)
  pkg.entryRules = (pkg.entryRules || []).map(rule => ({
    ...rule,
    effects: Array.isArray(rule.effects) ? rule.effects : [],
    effectsText: JSON.stringify(Array.isArray(rule.effects) ? rule.effects : [])
  }))
  pkg.benefitPresets = (pkg.benefitPresets || []).map(item => ({
    ...item,
    delta: item.delta || {},
    deltaText: JSON.stringify(item.delta || {})
  }))
  return pkg
}

function toPayload(value) {
  const pkg = cloneJson(value.formulaPackage)
  pkg.entryRules = (pkg.entryRules || []).map(({ effectsText, ...rule }) => ({
    ...rule,
    effects: Array.isArray(rule.effects) ? rule.effects : []
  }))
  pkg.benefitPresets = (pkg.benefitPresets || []).map(({ deltaText, ...item }) => ({
    ...item,
    delta: item.delta || {}
  }))
  return {
    versionId: value.versionId,
    versionName: value.versionName,
    formulaScope: FORMULA_SCOPE_INTERNAL_POWER_PVP,
    status: 'draft',
    formulaPackage: pkg,
    remark: value.remark || ''
  }
}

function syncJsonFromPackage() {
  packageText.value = JSON.stringify(toPayload(form.value).formulaPackage, null, 2)
}

function applyJsonToPackage() {
  try {
    const parsed = JSON.parse(packageText.value)
    form.value.formulaPackage = normalizeEditablePackage(parsed)
    proxy.$modal.msgSuccess('JSON已应用')
  } catch (error) {
    proxy.$modal.msgError(`JSON格式错误：${error.message}`)
  }
}

function addFixedCell() {
  form.value.formulaPackage.fixedCells.push({ sheet: '属性输入', cell: '', value: 0, label: '' })
}

function addEntryRule() {
  form.value.formulaPackage.entryRules.push({
    name: '',
    max: '',
    type: 'number',
    role: 'offense',
    effects: [],
    effectsText: '[]',
    ignoredNote: ''
  })
}

function addBenefitPreset() {
  form.value.formulaPackage.benefitPresets.push({
    label: '',
    delta: {},
    deltaText: '{}',
    explain: ''
  })
}

function syncRuleEffects(row) {
  try {
    const value = JSON.parse(row.effectsText || '[]')
    if (!Array.isArray(value)) throw new Error('必须是数组')
    row.effects = value
  } catch (error) {
    proxy.$modal.msgError(`词条影响JSON错误：${error.message}`)
    row.effectsText = JSON.stringify(row.effects || [])
  }
}

function syncPresetDelta(row) {
  try {
    const value = JSON.parse(row.deltaText || '{}')
    if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error('必须是对象')
    row.delta = value
  } catch (error) {
    proxy.$modal.msgError(`收益预设JSON错误：${error.message}`)
    row.deltaText = JSON.stringify(row.delta || {})
  }
}

function statusText(status) {
  return { draft: '草稿', published: '已发布', archived: '历史' }[status] || status
}

function statusTagType(status) {
  return { draft: 'warning', published: 'success', archived: 'info' }[status] || 'info'
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value))
}

getList()
</script>

<style scoped>
.formula-design-page {
  --line: rgba(32, 38, 52, 0.12);
}

.formula-form {
  padding-right: 8px;
}

.formula-tabs {
  margin-top: 14px;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.panel-grid h3 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #1f2937;
}

.json-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.json-editor :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.55;
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

@media (max-width: 900px) {
  .panel-grid {
    grid-template-columns: 1fr;
  }
}
</style>
