<template>
  <div v-if="activeKey === 'defense'" class="app-container defense-calculator-page">
    <section class="tool-header">
      <div>
        <p class="eyebrow">PERSONAL TOOLKIT</p>
        <h1>防守计算器</h1>
        <p class="source-line">7.8日新世界防守团内功计算器，原作者：月望舒（逆水寒手游）</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="resetToDefault">重置</el-button>
        <el-button type="primary" :icon="Document" @click="loadExample">载入示例</el-button>
      </div>
    </section>

    <section class="summary-strip">
      <article v-for="item in summaryCards" :key="item.label" class="summary-item">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section class="workspace-grid">
      <el-card shadow="never" class="work-panel input-panel">
        <template #header>
          <div class="panel-header">
            <span>参数输入</span>
            <el-select v-model="manualInput['周天']" class="zhou-select" size="small">
              <el-option v-for="option in ZHOU_TIAN_OPTIONS" :key="option" :label="option" :value="option" />
            </el-select>
          </div>
        </template>

        <el-tabs v-model="activeInputTab" stretch>
          <el-tab-pane label="词条" name="entries">
            <div class="entry-grid">
              <div v-for="field in ENTRY_FIELDS" :key="field.name" class="field-row">
                <span>{{ field.name }}</span>
                <el-radio-group
                  v-if="isSpiritEntryField(field.name)"
                  v-model="manualInput['词条'][field.name]"
                  class="yes-no-toggle entry-spirit-toggle"
                  size="small"
                >
                  <el-radio-button :value="1">是</el-radio-button>
                  <el-radio-button :value="0">否</el-radio-button>
                </el-radio-group>
                <el-input-number
                  v-else
                  v-model="manualInput['词条'][field.name]"
                  :controls="false"
                  :precision="2"
                  class="field-number"
                  size="small"
                />
                <strong>{{ getEntryScore(field.name) }}</strong>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane label="特性" name="traits">
            <div class="trait-list">
              <div v-for="field in TRAIT_FIELDS" :key="field.name" class="trait-row">
                <span>{{ field.name }}</span>
                <el-radio-group
                  v-model="manualInput['特性'][field.name]"
                  class="yes-no-toggle trait-toggle"
                  size="small"
                >
                  <el-radio-button :value="true">是</el-radio-button>
                  <el-radio-button :value="false">否</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <el-card shadow="never" class="work-panel json-panel">
        <template #header>
          <div class="panel-header">
            <span>JSON 输入</span>
            <div class="panel-actions">
              <el-button size="small" :icon="Document" @click="loadExample">载入示例</el-button>
              <el-button size="small" type="primary" :icon="Check" @click="applyJson">应用 JSON</el-button>
            </div>
          </div>
        </template>

        <el-alert v-if="jsonError" :title="jsonError" type="error" show-icon :closable="false" class="json-alert" />
        <el-input
          v-model="jsonText"
          type="textarea"
          :autosize="{ minRows: 18, maxRows: 30 }"
          spellcheck="false"
          class="json-textarea"
        />
      </el-card>
    </section>

    <section class="result-grid">
      <el-card shadow="never" class="work-panel result-panel">
        <template #header>
          <div class="panel-header">
            <span>词条明细</span>
            <el-tag type="success" effect="plain">{{ formatScore(calculation.summary['词条分']) }}</el-tag>
          </div>
        </template>
        <el-table :data="calculation['词条明细']" height="360" size="small">
          <el-table-column prop="名称" label="名称" min-width="140" />
          <el-table-column prop="满词条输入" label="满词条" width="100" align="right">
            <template #default="{ row }">{{ formatNullableValue(row['满词条输入']) }}</template>
          </el-table-column>
          <el-table-column prop="满词条评分" label="满评分" width="110" align="right">
            <template #default="{ row }">{{ formatNullableScore(row['满词条评分']) }}</template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never" class="work-panel result-panel">
        <template #header>
          <div class="panel-header">
            <span>特性明细</span>
            <el-tag type="warning" effect="plain">{{ formatScore(calculation.summary['特性分']) }}</el-tag>
          </div>
        </template>
        <el-table :data="calculation['特性明细']" height="360" size="small">
          <el-table-column prop="名称" label="名称" min-width="130" />
          <el-table-column prop="携带" label="携带" width="112" align="center">
            <template #default="{ row }">
              <el-radio-group
                v-model="manualInput['特性'][row['名称']]"
                class="yes-no-toggle trait-table-toggle"
                size="small"
              >
                <el-radio-button :value="true">是</el-radio-button>
                <el-radio-button :value="false">否</el-radio-button>
              </el-radio-group>
            </template>
          </el-table-column>
          <el-table-column prop="收益" label="收益" width="100" align="right">
            <template #default="{ row }">{{ formatScore(row['收益']) }}</template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never" class="work-panel output-panel result-panel">
        <template #header>
          <div class="panel-header">
            <span>结构化输出</span>
            <el-button size="small" :icon="DocumentCopy" @click="copyOutput">复制</el-button>
          </div>
        </template>
        <el-input
          :model-value="outputJson"
          type="textarea"
          readonly
          :autosize="{ minRows: 16, maxRows: 26 }"
          spellcheck="false"
          class="json-textarea"
        />
      </el-card>
    </section>

    <p class="credit-line">无偿分享。感谢 杰少、满天星河、智齿提供帮助；计算公式来源于 折字愿为安。</p>
  </div>

  <div v-else class="app-container calculator-page">
    <section class="calculator-hero" :class="activeConfig.tone">
      <div class="hero-copy">
        <p class="eyebrow">PERSONAL TOOLKIT</p>
        <h1>{{ activeConfig.title }}</h1>
        <p class="hero-desc">{{ activeConfig.description }}</p>
      </div>
      <div class="hero-badge">
        <span>待开发</span>
        <strong>{{ activeConfig.stage }}</strong>
      </div>
    </section>

    <section class="calculator-grid">
      <article v-for="item in featureCards" :key="item.title" class="feature-card">
        <span class="feature-index">{{ item.index }}</span>
        <h3>{{ item.title }}</h3>
        <p>{{ item.text }}</p>
      </article>
    </section>

    <el-card shadow="never" class="placeholder-panel">
      <template #header>
        <div class="panel-header">
          <span>{{ activeConfig.title }}功能占位</span>
          <el-tag type="info" effect="plain">算法待接入</el-tag>
        </div>
      </template>

      <div class="empty-state">
        <div class="empty-mark">{{ activeConfig.mark }}</div>
        <div>
          <h2>这里先作为入口保留</h2>
          <p>
            当前页面已经接入个人管理菜单。后续确认计算公式、输入项和输出指标后，
            可以直接在这里补齐真实计算器。
          </p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Document, DocumentCopy, Refresh } from '@element-plus/icons-vue'
import {
  DEFENSE_CALCULATOR_EXAMPLE,
  ENTRY_FIELDS,
  TRAIT_FIELDS,
  ZHOU_TIAN_OPTIONS,
  calculatePersonalDefense,
  createDefaultDefenseInput,
  isSpiritEntryField,
  normalizeDefenseInput,
  stringifyDefenseJson
} from '@/utils/personalDefenseCalculator'

const route = useRoute()
const activeInputTab = ref('entries')
const jsonError = ref('')
const manualInput = reactive(createDefaultDefenseInput())
const jsonText = ref(stringifyDefenseJson(DEFENSE_CALCULATOR_EXAMPLE))

const calculatorConfigs = {
  defense: {
    title: '防守计算器',
    description: '预留给防守承伤、减伤、治疗压力和队伍容错的计算入口。',
    stage: '防守模型',
    mark: '守',
    tone: 'tone-defense',
    features: [
      ['承伤拆解', '后续用于录入防御、减伤、承伤倍率等数据。'],
      ['治疗压力', '预留治疗缺口、复活压力和重伤风险展示。'],
      ['阵容容错', '后续联动帮会成员和排表阵容做防守评估。']
    ]
  },
  tower: {
    title: '拆塔计算器',
    description: '预留给拆塔效率、建筑伤害、破塔卸甲和职业分工的计算入口。',
    stage: '拆塔模型',
    mark: '塔',
    tone: 'tone-tower',
    features: [
      ['建筑伤害', '后续用于录入对建筑伤害和破塔卸甲数据。'],
      ['拆塔节奏', '预留不同阶段、不同队伍拆塔效率对比。'],
      ['职业分工', '后续按职业与队伍位置评估拆塔收益。']
    ]
  },
  suhong: {
    title: '素/鸿计算器',
    description: '预留给素问、鸿音相关治疗、增益、收益与队伍搭配的计算入口。',
    stage: '素鸿模型',
    mark: '素',
    tone: 'tone-suhong',
    features: [
      ['治疗收益', '后续用于整理治疗值、承伤转化和续航表现。'],
      ['增益评估', '预留鸿音增益、辅助收益和团队覆盖计算。'],
      ['队伍搭配', '后续联动排表，评估素问/鸿音在队伍中的配置。']
    ]
  }
}

const activeKey = computed(() => {
  const path = route.path || ''
  if (path.includes('tower-calculator')) return 'tower'
  if (path.includes('suhong-calculator')) return 'suhong'
  return 'defense'
})

const activeConfig = computed(() => calculatorConfigs[activeKey.value])

const featureCards = computed(() => {
  return activeConfig.value.features.map(([title, text], index) => ({
    title,
    text,
    index: String(index + 1).padStart(2, '0')
  }))
})

const calculation = computed(() => calculatePersonalDefense(manualInput))

const entryScoreByName = computed(() => {
  return Object.fromEntries(calculation.value['词条明细'].map(item => [item['名称'], item['评分']]))
})

const summaryCards = computed(() => [
  { label: '词条分', value: formatScore(calculation.value.summary['词条分']) },
  { label: '特性分', value: formatScore(calculation.value.summary['特性分']) },
  { label: '周天加成', value: formatScore(calculation.value.summary['周天加成']) },
  { label: '总分', value: formatScore(calculation.value.summary['总分']) }
])

const outputJson = computed(() => stringifyDefenseJson(calculation.value))

function setInput(value) {
  const normalized = normalizeDefenseInput(value)
  manualInput['周天'] = normalized['周天']
  ENTRY_FIELDS.forEach(field => {
    manualInput['词条'][field.name] = normalized['词条'][field.name]
  })
  TRAIT_FIELDS.forEach(field => {
    manualInput['特性'][field.name] = normalized['特性'][field.name]
  })
}

function resetToDefault() {
  setInput(createDefaultDefenseInput())
  jsonText.value = stringifyDefenseJson(createDefaultDefenseInput())
  jsonError.value = ''
}

function loadExample() {
  setInput(DEFENSE_CALCULATOR_EXAMPLE)
  jsonText.value = stringifyDefenseJson(DEFENSE_CALCULATOR_EXAMPLE)
  jsonError.value = ''
}

function applyJson() {
  try {
    const parsed = JSON.parse(jsonText.value)
    setInput(parsed)
    jsonText.value = stringifyDefenseJson(normalizeDefenseInput(parsed))
    jsonError.value = ''
    ElMessage.success('JSON 已应用')
  } catch (error) {
    jsonError.value = `JSON 解析失败：${error.message}`
  }
}

async function copyOutput() {
  try {
    await navigator.clipboard.writeText(outputJson.value)
    ElMessage.success('结构化输出已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选中复制')
  }
}

function formatScore(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0.00'
  return n.toFixed(2)
}

function getEntryScore(name) {
  return formatScore(entryScoreByName.value[name])
}

function formatNullableScore(value) {
  return value == null ? '--' : formatScore(value)
}

function formatNullableValue(value) {
  if (value == null) return '--'
  const n = Number(value)
  if (!Number.isFinite(n)) return '--'
  return n.toFixed(2)
}
</script>

<style scoped lang="scss">
.defense-calculator-page {
  --ink: #172033;
  --muted: #667085;
  --line: rgba(23, 32, 51, 0.1);
  --panel: #ffffff;
  --soft: #f5f7fb;
  display: flex;
  flex-direction: column;
  gap: 14px;
  color: var(--ink);
}

.tool-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: linear-gradient(135deg, #ffffff 0%, #f5fbf7 48%, #f6f8ff 100%);
}

.eyebrow {
  margin: 0 0 6px;
  color: #65758f;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.tool-header h1 {
  margin: 0;
  color: #111827;
  font-size: 28px;
  line-height: 1.2;
}

.source-line,
.credit-line {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.header-actions,
.panel-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.summary-item {
  min-height: 76px;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
}

.summary-item span,
.summary-item strong {
  display: block;
}

.summary-item span {
  color: var(--muted);
  font-size: 13px;
}

.summary-item strong {
  margin-top: 8px;
  color: #0f766e;
  font-size: 24px;
  line-height: 1;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(380px, 0.92fr);
  gap: 14px;
  align-items: start;
}

.result-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 0.9fr) minmax(360px, 1.05fr);
  gap: 14px;
  align-items: start;
}

.work-panel {
  border-radius: 8px;
}

.result-panel :deep(.el-card__header) {
  padding: 12px 16px;
}

.result-panel :deep(.el-card__body) {
  padding: 10px 12px 12px;
}

.result-panel :deep(.el-table) {
  border-radius: 8px;
}

.result-panel :deep(.el-table .cell) {
  padding: 0 8px;
  line-height: 1.35;
}

.result-panel :deep(.el-table__cell) {
  padding: 5px 0;
}

.result-panel :deep(.el-table__header .el-table__cell) {
  padding: 8px 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.zhou-select {
  width: 128px;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 12px;
}

.field-row,
.trait-row {
  display: grid;
  grid-template-columns: minmax(110px, 1fr) 120px 72px;
  gap: 10px;
  align-items: center;
  min-height: 32px;
}

.field-row span,
.trait-row span {
  color: #344054;
  font-size: 13px;
}

.field-row strong {
  justify-self: end;
  color: #0f766e;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.field-number {
  width: 120px;
}

.trait-row {
  grid-template-columns: minmax(110px, 1fr) 92px;
}

.yes-no-toggle {
  display: inline-flex;
  width: 92px;
}

.entry-spirit-toggle {
  width: 120px;
}

.trait-toggle,
.trait-table-toggle {
  width: 92px;
}

.yes-no-toggle :deep(.el-radio-button) {
  flex: 1;
}

.yes-no-toggle :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 5px 0;
  border-color: #d8dee9;
  font-size: 12px;
  line-height: 1;
  box-shadow: none;
}

.trait-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
}

.json-alert {
  margin-bottom: 10px;
}

.json-textarea :deep(.el-textarea__inner) {
  font-family: Consolas, 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.55;
}

.output-panel {
  min-width: 0;
}

.credit-line {
  padding: 0 2px 8px;
}

.calculator-page {
  --ink: #172033;
  --muted: #667085;
  --paper: #fffdf7;
  --line: rgba(23, 32, 51, 0.1);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.calculator-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 24px;
  min-height: 190px;
  padding: 34px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--ink);
  background: linear-gradient(135deg, #fff8df 0%, #eaf5ff 52%, #eef1ff 100%);
  box-shadow: 0 16px 40px rgba(57, 75, 110, 0.1);
}

.calculator-hero.tone-defense {
  background: linear-gradient(135deg, #e8f7ef 0%, #dceeff 55%, #f9f5e5 100%);
}

.calculator-hero.tone-tower {
  background: linear-gradient(135deg, #fff1db 0%, #ffe3cc 45%, #eef3ff 100%);
}

.calculator-hero.tone-suhong {
  background: linear-gradient(135deg, #fff0f5 0%, #edf8ff 52%, #f7f1ff 100%);
}

.hero-copy h1 {
  margin: 0;
  color: #121826;
  font-size: 38px;
  line-height: 1.1;
}

.hero-desc {
  max-width: 680px;
  margin: 16px 0 0;
  color: var(--muted);
  font-size: 16px;
  line-height: 1.8;
}

.hero-badge {
  align-self: end;
  min-width: 150px;
  padding: 18px;
  border: 1px solid rgba(255, 255, 255, 0.68);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.62);
}

.hero-badge span,
.hero-badge strong {
  display: block;
}

.hero-badge span {
  color: #6f7787;
  font-size: 13px;
}

.hero-badge strong {
  margin-top: 8px;
  color: #172033;
  font-size: 21px;
}

.calculator-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.feature-card {
  min-height: 150px;
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  box-shadow: 0 10px 28px rgba(23, 32, 51, 0.05);
}

.feature-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 26px;
  border-radius: 6px;
  color: #2454c6;
  background: #edf3ff;
  font-size: 12px;
  font-weight: 900;
}

.feature-card h3 {
  margin: 18px 0 8px;
  color: var(--ink);
  font-size: 18px;
}

.feature-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.placeholder-panel {
  border-radius: 8px;
}

.empty-state {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 20px;
  align-items: center;
  min-height: 160px;
}

.empty-mark {
  display: grid;
  place-items: center;
  width: 104px;
  height: 104px;
  border-radius: 8px;
  color: #1f3b68;
  background: linear-gradient(145deg, #f8fbff, #dceaff);
  font-size: 46px;
  font-weight: 900;
  box-shadow: inset 0 0 0 1px rgba(72, 113, 172, 0.16);
}

.empty-state h2 {
  margin: 0 0 8px;
  color: var(--ink);
}

.empty-state p {
  max-width: 720px;
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

@media (max-width: 1180px) {
  .workspace-grid,
  .result-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .tool-header,
  .calculator-hero,
  .empty-state {
    grid-template-columns: 1fr;
  }

  .summary-strip,
  .calculator-grid,
  .entry-grid,
  .trait-list {
    grid-template-columns: 1fr;
  }

  .header-actions,
  .panel-header {
    align-items: stretch;
    flex-direction: column;
  }

  .zhou-select,
  .field-number,
  .entry-spirit-toggle,
  .trait-toggle,
  .trait-table-toggle {
    width: 100%;
  }

  .field-row,
  .trait-row {
    grid-template-columns: 1fr;
  }

  .field-row strong {
    justify-self: start;
  }
}
</style>
