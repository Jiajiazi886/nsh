import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const source = fs.readFileSync(new URL('./index.vue', import.meta.url), 'utf8')

test('guild analysis uses saved lineup templates and local CSV box analysis without charts', () => {
  assert.match(source, /activityLineupTemplates/)
  assert.match(source, /parseBattleCsv/)
  assert.match(source, /buildBoxAnalysis/)
  assert.match(source, /最新排表/)
  assert.match(source, /分析盒子/)
  assert.doesNotMatch(source, /AnalysisChartPanel|echarts|柱状图|饼图|折线图/)
})
