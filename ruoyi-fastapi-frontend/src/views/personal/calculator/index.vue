<template>
  <div class="app-container calculator-page">
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
      <article
        v-for="item in featureCards"
        :key="item.title"
        class="feature-card"
      >
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
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

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
</script>

<style scoped lang="scss">
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
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 24px;
  overflow: hidden;
  min-height: 190px;
  padding: 34px;
  border: 1px solid var(--line);
  border-radius: 28px;
  color: var(--ink);
  background:
    radial-gradient(circle at 18% 15%, rgba(255, 255, 255, 0.95), transparent 28%),
    linear-gradient(135deg, #fff8df 0%, #eaf5ff 52%, #eef1ff 100%);
  box-shadow: 0 24px 70px rgba(57, 75, 110, 0.13);
}

.calculator-hero::after {
  content: '';
  position: absolute;
  right: -80px;
  bottom: -120px;
  width: 320px;
  height: 320px;
  border-radius: 999px;
  border: 42px solid rgba(255, 255, 255, 0.55);
}

.calculator-hero.tone-defense {
  background:
    radial-gradient(circle at 12% 10%, rgba(255, 255, 255, 0.96), transparent 26%),
    linear-gradient(135deg, #e8f7ef 0%, #dceeff 55%, #f9f5e5 100%);
}

.calculator-hero.tone-tower {
  background:
    radial-gradient(circle at 14% 12%, rgba(255, 255, 255, 0.94), transparent 28%),
    linear-gradient(135deg, #fff1db 0%, #ffe3cc 45%, #eef3ff 100%);
}

.calculator-hero.tone-suhong {
  background:
    radial-gradient(circle at 16% 12%, rgba(255, 255, 255, 0.94), transparent 28%),
    linear-gradient(135deg, #fff0f5 0%, #edf8ff 52%, #f7f1ff 100%);
}

.hero-copy {
  position: relative;
  z-index: 1;
}

.eyebrow {
  margin: 0 0 8px;
  color: #5a6d90;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.hero-copy h1 {
  margin: 0;
  color: #121826;
  font-size: clamp(32px, 5vw, 56px);
  line-height: 1;
  letter-spacing: -0.06em;
}

.hero-desc {
  max-width: 680px;
  margin: 16px 0 0;
  color: var(--muted);
  font-size: 16px;
  line-height: 1.8;
}

.hero-badge {
  position: relative;
  z-index: 1;
  align-self: end;
  min-width: 150px;
  padding: 18px;
  border: 1px solid rgba(255, 255, 255, 0.68);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.62);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(14px);
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
  border-radius: 22px;
  background: var(--paper);
  box-shadow: 0 14px 34px rgba(23, 32, 51, 0.06);
}

.feature-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 26px;
  border-radius: 999px;
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
  border-radius: 22px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
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
  border-radius: 30px;
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

@media (max-width: 960px) {
  .calculator-hero,
  .empty-state {
    grid-template-columns: 1fr;
  }

  .calculator-grid {
    grid-template-columns: 1fr;
  }

  .hero-badge {
    align-self: start;
  }
}

@media (max-width: 640px) {
  .calculator-hero {
    padding: 24px;
    border-radius: 22px;
  }

  .feature-card {
    min-height: auto;
  }
}
</style>
