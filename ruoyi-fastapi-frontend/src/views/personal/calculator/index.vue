<template>
  <div v-if="isDefenseCalculator" class="app-container defense-page">
    <section class="page-header">
      <div><h1>防守计算器</h1><p>基于 PVP 计算器 4.1.1 的防御减免、会心率与伤害期望公式。</p></div>
      <el-select v-model="selectedPanelId" class="panel-select" placeholder="选择进攻方面板">
        <el-option v-for="panel in attackPanels" :key="panel.panelId" :label="panel.panelName" :value="panel.panelId" />
      </el-select>
    </section>

    <section class="curve-grid">
      <div class="chart-section"><h2>防御减免曲线</h2><div ref="defenseChartRef" class="chart"></div></div>
      <div class="chart-section"><h2>会心率曲线</h2><div ref="critChartRef" class="chart"></div></div>
      <div class="chart-section"><h2>防御边际收益</h2><p>每增加 100 点剩余防御，防御减免的理论增量。</p><div ref="defenseDerivativeChartRef" class="chart"></div></div>
      <div class="chart-section"><h2>会心边际收益</h2><p>每增加 100 点净会心，会心率的理论增量。</p><div ref="critDerivativeChartRef" class="chart"></div></div>
    </section>

    <section class="calculator-grid">
      <div class="input-section">
        <h2>防守方面板</h2>
        <div class="field-grid">
          <label v-for="field in DEFENDER_FIELDS" :key="field.key" class="number-field">
            <span>{{ field.label }}</span>
            <el-input-number v-model="defender[field.key]" :min="0" :step="field.step" :precision="field.precision ?? (field.step < 1 ? 1 : 0)" controls-position="right">
              <template v-if="field.suffix" #suffix>{{ field.suffix }}</template>
            </el-input-number>
          </label>
        </div>
      </div>

      <div class="result-section">
        <h2>承伤结果</h2>
        <div class="metric-grid">
          <div><span>伤害期望</span><strong>{{ formatNumber(calculation.expectedDamage) }}</strong></div>
          <div><span>血量/伤害期望</span><strong>{{ formatNumber(calculation.durability) }}</strong></div>
          <div><span>防御减免</span><strong>{{ formatPercent(calculation.defenseMitigation) }}</strong></div>
          <div><span>实际会心率</span><strong>{{ formatPercent(calculation.critRate) }}</strong></div>
        </div>
        <div class="detail-grid">
          <span>剩余防御 <b>{{ formatNumber(calculation.remainingDefense) }}</b></span>
          <span>净会心 <b>{{ formatNumber(calculation.netCrit) }}</b></span>
          <span>技巧克制差 <b>{{ formatNumber(calculation.techniqueDifference) }}</b></span>
          <span>未会心伤害 <b>{{ formatNumber(calculation.nonCritDamage) }}</b></span>
        </div>
      </div>
    </section>

    <section class="advice-section">
      <h2>内功词条提升建议</h2>
      <div class="recommendations">
        <div v-for="item in recommendations" :key="item.label"><span>{{ item.label }}</span><strong>肉度 +{{ formatPercent(item.gainPct / 100) }}</strong><small>血量/伤害期望 {{ formatNumber(item.durability) }}</small></div>
      </div>
    </section>

    <section class="comparison-section">
      <div class="section-title"><h2>自定义内功词条对比</h2><span>仅计算数值词条，不计入内功增伤占比。</span></div>
      <div class="comparison-inputs">
        <div v-for="(entries, index) in compareEntries" :key="index" class="entry-set">
          <h3>方案 {{ index === 0 ? 'A' : 'B' }}</h3>
          <label v-for="field in INNER_POWER_FIELDS" :key="field.key"><span>{{ field.label }}</span><el-input-number v-model="entries[field.key]" :step="field.step" :precision="field.precision ?? (field.step < 1 ? 1 : 0)" controls-position="right" /></label>
        </div>
      </div>
      <div class="comparison-results">
        <div v-for="item in [comparison.buildA, comparison.buildB]" :key="item.name"><span>{{ item.name }}</span><strong>肉度 {{ item.gainPct >= 0 ? '+' : '' }}{{ formatPercent(item.gainPct / 100) }}</strong><small>血量/伤害期望 {{ formatNumber(item.durability) }}</small></div>
      </div>
    </section>
  </div>

  <div v-else class="app-container empty-calculator"><el-empty description="该计算器正在整理中" /></div>
</template>

<script setup name="PersonalDefenseCalculator">
import * as echarts from 'echarts'
import { useRoute } from 'vue-router'
import { listDefenseAttackPanels } from '@/api/personal/defenseCalculator'
import {
  DEFAULT_ATTACK_PANEL,
  DEFENDER_FIELDS,
  INNER_POWER_FIELDS,
  calculateDefense,
  calculateInnerPowerComparison,
  calculateRecommendation,
  createDefaultDefender,
  createEmptyInnerPowerEntries
} from '@/utils/personalDefenseCalculator'

const route = useRoute()
const isDefenseCalculator = computed(() => route.path.includes('defense-calculator') || route.name === 'PersonalDefenseCalculator')
const defender = reactive(createDefaultDefender())
const attackPanels = ref([])
const selectedPanelId = ref(0)
const defenseChartRef = ref()
const critChartRef = ref()
const defenseDerivativeChartRef = ref()
const critDerivativeChartRef = ref()
const compareEntries = reactive([createEmptyInnerPowerEntries(), createEmptyInnerPowerEntries()])
let defenseChart
let critChart
let defenseDerivativeChart
let critDerivativeChart

const activePanel = computed(() => attackPanels.value.find(item => item.panelId === selectedPanelId.value) || DEFAULT_ATTACK_PANEL)
const calculation = computed(() => calculateDefense(defender, activePanel.value))
const recommendations = computed(() => calculateRecommendation(defender, activePanel.value))
const comparison = computed(() => calculateInnerPowerComparison(defender, activePanel.value, compareEntries[0], compareEntries[1]))

onMounted(async () => {
  await loadAttackPanels()
  initCharts()
  window.addEventListener('resize', resizeCharts)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  defenseChart?.dispose()
  critChart?.dispose()
  defenseDerivativeChart?.dispose()
  critDerivativeChart?.dispose()
})
watch(calculation, updateCharts, { deep: true })

async function loadAttackPanels() {
  try {
    const res = await listDefenseAttackPanels()
    attackPanels.value = res.data?.length ? res.data : [DEFAULT_ATTACK_PANEL]
  } catch {
    attackPanels.value = [DEFAULT_ATTACK_PANEL]
  }
  selectedPanelId.value = attackPanels.value[0].panelId
}

function initCharts() {
  defenseChart = echarts.init(defenseChartRef.value)
  critChart = echarts.init(critChartRef.value)
  defenseDerivativeChart = echarts.init(defenseDerivativeChartRef.value)
  critDerivativeChart = echarts.init(critDerivativeChartRef.value)
  updateCharts()
}

function updateCharts() {
  if (!defenseChart || !critChart || !defenseDerivativeChart || !critDerivativeChart) return
  defenseChart.setOption(lineOption('剩余防御', '防御减免比例', calculation.value.defenseCurve, '#27689d'))
  critChart.setOption(lineOption('净会心', '会心率', calculation.value.critCurve, '#b87819', { inverseX: true }))
  defenseDerivativeChart.setOption(lineOption('剩余防御', '每 +100 点减免增量', calculation.value.defenseDerivativeCurve, '#427d45', { yMax: curveMaximum(calculation.value.defenseDerivativeCurve) }))
  critDerivativeChart.setOption(lineOption('净会心', '每 +100 点会心率增量', calculation.value.critDerivativeCurve, '#925189', { inverseX: true, yMax: curveMaximum(calculation.value.critDerivativeCurve) }))
}

function lineOption(xName, yName, data, color, options = {}) {
  const yMax = options.yMax || 1
  return {
    grid: { left: 52, right: 24, top: 22, bottom: 42 },
    tooltip: { trigger: 'axis', valueFormatter: value => `${(Number(value) * 100).toFixed(2)}%` },
    xAxis: { type: 'value', name: xName, nameLocation: 'end', inverse: Boolean(options.inverseX), splitLine: { lineStyle: { color: '#edf0f5' } } },
    yAxis: { type: 'value', name: yName, min: 0, max: yMax, interval: yMax / 4, axisLabel: { formatter: value => `${value}` }, splitLine: { lineStyle: { color: '#dbe3ed' } } },
    series: [{ type: 'line', smooth: true, showSymbol: false, data, lineStyle: { color, width: 3 }, areaStyle: { color: `${color}18` } }]
  }
}

function curveMaximum(data) {
  return Math.max(...data.map(([, value]) => Number(value) || 0), 0.000001)
}

function resizeCharts() {
  defenseChart?.resize()
  critChart?.resize()
  defenseDerivativeChart?.resize()
  critDerivativeChart?.resize()
}
function formatNumber(value) { return Number(value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 }) }
function formatPercent(value) { return `${(Number(value || 0) * 100).toFixed(2)}%` }
</script>

<style scoped>
.defense-page { display: grid; gap: 18px; color: #233247; }
.page-header { display: flex; align-items: end; justify-content: space-between; gap: 20px; padding-bottom: 16px; border-bottom: 1px solid #dbe3ed; }
.page-header h1, h2, h3 { margin: 0; letter-spacing: 0; }
.page-header h1 { font-size: 26px; }
.page-header p, .section-title span { margin: 8px 0 0; color: #6c7b8d; font-size: 14px; }
.panel-select { width: 240px; }
.curve-grid, .calculator-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.chart-section, .input-section, .result-section, .advice-section, .comparison-section { border: 1px solid #dbe3ed; border-radius: 8px; background: #fff; }
.chart-section { padding: 18px; }
.chart-section h2, .input-section h2, .result-section h2, .advice-section h2, .comparison-section h2 { font-size: 17px; }
.chart { height: 310px; margin-top: 12px; }
.input-section, .result-section { padding: 20px; }
.field-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }
.number-field, .entry-set label { display: grid; gap: 7px; color: #526176; font-size: 13px; }
.number-field :deep(.el-input-number), .entry-set :deep(.el-input-number) { width: 100%; }
.metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; margin-top: 18px; background: #e5eaf0; }
.metric-grid div { min-height: 94px; padding: 16px; background: #f8fafc; }
.metric-grid span, .detail-grid span, .recommendations span, .comparison-results span { display: block; color: #69788b; font-size: 13px; }
.metric-grid strong { display: block; margin-top: 10px; color: #173a62; font-size: 22px; font-variant-numeric: tabular-nums; }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 20px; }
.detail-grid b { margin-left: 8px; color: #26394f; font-variant-numeric: tabular-nums; }
.advice-section, .comparison-section { padding: 20px; }
.recommendations, .comparison-results { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 16px; }
.recommendations div, .comparison-results div { padding: 16px; border-left: 4px solid #3c7bb2; background: #f6f9fc; }
.recommendations strong, .comparison-results strong { display: block; margin-top: 8px; color: #16634e; font-size: 18px; }
.recommendations small, .comparison-results small { display: block; margin-top: 7px; color: #69788b; }
.section-title { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; }
.comparison-inputs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-top: 18px; }
.entry-set { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 16px; border: 1px solid #e1e7ef; }
.entry-set h3 { grid-column: 1 / -1; color: #305675; font-size: 15px; }
.empty-calculator { display: grid; min-height: 360px; place-items: center; }
@media (max-width: 980px) { .curve-grid, .calculator-grid, .comparison-inputs { grid-template-columns: 1fr; } }
@media (max-width: 640px) { .page-header, .section-title { align-items: stretch; flex-direction: column; } .panel-select { width: 100%; } .field-grid, .metric-grid, .detail-grid, .recommendations, .comparison-results, .entry-set { grid-template-columns: 1fr; } }
</style>
