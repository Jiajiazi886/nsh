<template>
  <div ref="chartRef" class="analysis-chart-panel" />
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: {
    type: Object,
    default: () => ({})
  },
  autoresizeKey: {
    type: [String, Number],
    default: ''
  }
})

const chartRef = ref(null)
let chartInstance = null

function initChart() {
  if (!chartRef.value) return null
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  return chartInstance
}

async function renderChart() {
  await nextTick()
  const chart = initChart()
  if (!chart) return
  chart.setOption(props.option || {}, true)
  chart.resize()
}

function resizeChart() {
  chartInstance?.resize()
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

watch(
  () => props.option,
  renderChart,
  { deep: true }
)

watch(
  () => props.autoresizeKey,
  () => nextTick(resizeChart)
)

defineExpose({
  resize: resizeChart
})
</script>

<style scoped>
.analysis-chart-panel {
  width: 100%;
  height: 100%;
  min-height: 180px;
}
</style>
