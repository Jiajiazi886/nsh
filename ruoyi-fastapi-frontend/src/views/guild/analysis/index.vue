<template>
  <div ref="pageRef" class="app-container analysis-page" :class="{ 'is-fullscreen': isFullscreen }">
    <section class="analysis-hero" data-guild-motion="hero">
      <div class="hero-copy">
        <span class="eyebrow">Battle review console</span>
        <h1>约战数据分析</h1>
        <p>
          先选择一次已导入的历史数据；如果这场约战有保存过排表，再叠加历史排表查看出勤匹配、团队表现和未排表参战成员。
        </p>
      </div>
      <div class="hero-scope">
        <span>流程</span>
        <strong>报名 → 排表 → 保存历史 → 导入数据 → 分析</strong>
        <button type="button" class="fullscreen-button" @click="toggleFullscreen">
          {{ isFullscreen ? '退出全屏' : '全屏分析' }}
        </button>
      </div>
    </section>

    <section class="source-status-board" data-guild-reveal>
      <article
        v-for="item in sourceStatusItems"
        :key="item.key"
        class="source-status-card"
        :class="[item.tone, { ready: item.ready, muted: !item.count && !item.loading }]"
      >
        <span>{{ item.label }}</span>
        <strong>{{ item.loading ? '同步中' : item.title }}</strong>
        <em>{{ item.detail }}</em>
      </article>
    </section>

    <section v-if="isFullscreen" class="analysis-cockpit" data-guild-reveal>
      <header class="cockpit-header">
        <div>
          <span>dense analyst terminal</span>
          <h2>约战数据矩阵</h2>
          <p>对象池、A/B 选择和指标矩阵放在同一视线区域，按人看表格的习惯连续读取。</p>
        </div>
        <div class="cockpit-source-line">
          <strong>{{ selectedBattle?.battle_name || '未选择历史数据' }}</strong>
          <em>{{ selectedSchedule?.schedule_name || '未关联排表' }}</em>
        </div>
        <button type="button" class="cockpit-exit" @click="toggleFullscreen">退出全屏</button>
      </header>

      <div class="dense-workbench">
        <div class="dense-toolbar">
          <div class="mode-tabs">
            <button
              v-for="mode in compareModes"
              :key="mode.value"
              type="button"
              class="mode-tab"
              :class="{ active: compareMode === mode.value }"
              @click="setCompareMode(mode.value)"
            >
              {{ mode.label }}
            </button>
          </div>
          <div class="dense-flags">
            <label v-for="option in analysisOptionSwitches" :key="option.key">
              <input v-model="option.model.value" type="checkbox">
              <span>{{ option.label }}</span>
            </label>
            <button type="button" class="layout-reset-button" @click="resetAnalysisPanelLayout">重置布局</button>
          </div>
          <strong class="option-count">{{ comparisonOptionCountLabel }}</strong>
        </div>

        <div class="dense-selector-row">
          <div class="dense-select-cell side-a">
            <span>A</span>
            <el-select
              v-model="compareLeftId"
              filterable
              class="cockpit-select"
              :placeholder="compareLeftPlaceholder"
              @change="handleComparisonSelect('left')"
            >
              <el-option
                v-for="item in comparisonOptions"
                :key="item.id"
                :label="item.label"
                :value="item.id"
              >
                <div class="option-line">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.subtitle }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
          <button type="button" class="swap-button" title="交换 A/B" @click="swapComparisonSides">↔</button>
          <div class="dense-select-cell side-b">
            <span>B</span>
            <el-select
              v-model="compareRightId"
              filterable
              class="cockpit-select"
              :placeholder="compareRightPlaceholder"
              @change="handleComparisonSelect('right')"
            >
              <el-option
                v-for="item in comparisonOptions"
                :key="item.id"
                :label="item.label"
                :value="item.id"
              >
                <div class="option-line">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.subtitle }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
        </div>

        <div class="dense-summary-strip">
          <span>{{ compareModeLabel }}</span>
          <strong>{{ comparisonHeadline }}</strong>
          <em>{{ comparisonSubtitle }}</em>
          <b>{{ comparisonDeltaLabel }}</b>
        </div>

        <div
          class="dense-grid"
          @dragover.prevent
          @drop="handleComparisonDrop"
        >
          <ResizablePanel
            :key="`comparison-pool-${panelLayoutKey}`"
            storage-key="comparison-pool"
            panel-class="comparison-pool"
            :default-width="420"
            :default-height="720"
            :min-width="320"
            :min-height="420"
            @resize="refreshAnalysisCharts"
          >
            <div class="pool-head">
              <div>
                <h3>对象池</h3>
                <span>{{ comparisonSourceHint }}</span>
              </div>
              <b>{{ visibleComparisonOptions.length }}/{{ comparisonOptions.length }}</b>
            </div>
            <input
              v-model="comparisonSearch"
              class="pool-search"
              type="search"
              :placeholder="compareMode === 'team' ? '搜索队伍' : '搜索玩家 / 职业 / 帮会'"
            >
            <div class="pool-list">
              <button
                v-for="item in visibleComparisonOptions"
                :key="item.id"
                type="button"
                class="pool-row"
                :class="{ left: item.id === compareLeftId, right: item.id === compareRightId }"
                draggable="true"
                @dragstart="handleComparisonDragStart($event, item.id)"
                @dblclick="addComparisonItem(item.id)"
              >
                <i :style="getComparisonAccentStyle(item)"></i>
                <strong>{{ item.label }}</strong>
                <em>{{ item.subtitle }}</em>
                <b>{{ formatCompact(item.metrics?.total_kills) }}</b>
                <span>
                  <small @click.stop="addComparisonItem(item.id)">加入</small>
                  <small @click.stop="setComparisonSide(item.id, 'left')">设 A</small>
                  <small @click.stop="setComparisonSide(item.id, 'right')">设 B</small>
                </span>
              </button>
              <el-empty v-if="!visibleComparisonOptions.length" description="没有匹配对象" :image-size="58" />
            </div>
          </ResizablePanel>

          <main class="dense-center">
            <ResizablePanel
              :key="`comparison-tray-${panelLayoutKey}`"
              storage-key="comparison-tray"
              panel-class="comparison-tray-panel"
              :default-width="1040"
              :default-height="190"
              :min-width="620"
              :min-height="150"
              @resize="refreshAnalysisCharts"
            >
              <div class="tray-head">
                <div>
                  <h3>多人对比托盘</h3>
                  <span>双击对象或拖入这里；不限制人数，图表横向滚动。</span>
                </div>
                <button type="button" @click="clearSelectedComparisonItems">清空</button>
              </div>
              <div
                class="comparison-tray"
                @dragover.prevent
                @drop.stop="handleComparisonDrop"
              >
                <button
                  v-for="item in selectedComparisonItems"
                  :key="item.id"
                  type="button"
                  class="tray-chip"
                  :style="getComparisonAccentStyle(item)"
                  @click="removeComparisonItem(item.id)"
                >
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.subtitle }}</span>
                  <em>{{ formatCompact(item.metrics?.total_kills) }}</em>
                </button>
                <div v-if="!selectedComparisonItems.length" class="tray-empty">
                  从左侧拖入玩家/队伍，或双击对象加入对比。
                </div>
              </div>
            </ResizablePanel>

            <ResizablePanel
              :key="`comparison-matrix-${panelLayoutKey}`"
              storage-key="comparison-matrix"
              panel-class="dense-matrix"
              :default-width="1040"
              :default-height="520"
              :min-width="680"
              :min-height="360"
              @resize="refreshAnalysisCharts"
            >
              <div v-if="isMultiComparison" class="multi-matrix">
                <div class="multi-matrix-head" :style="multiMatrixGridStyle">
                  <span>指标</span>
                  <span v-for="item in selectedComparisonItems" :key="item.id">{{ item.label }}</span>
                  <span>判断</span>
                </div>
                <div class="matrix-body">
                  <div
                    v-for="row in multiComparisonRows"
                    :key="row.key"
                    class="multi-matrix-row"
                    :style="multiMatrixGridStyle"
                  >
                    <strong>{{ row.label }}</strong>
                    <span
                      v-for="cell in row.cells"
                      :key="cell.id"
                      :class="{ peak: cell.isMax, low: cell.isMin }"
                    >
                      {{ cell.text }}
                    </span>
                    <em>{{ row.judgement }}</em>
                  </div>
                </div>
              </div>
              <template v-else>
                <div class="matrix-head">
                  <span>指标</span>
                  <span>A：{{ leftComparison?.label || '未选' }}</span>
                  <span>B：{{ rightComparison?.label || '未选' }}</span>
                  <span>差值</span>
                  <span>占比</span>
                  <span>判断</span>
                </div>
                <div class="matrix-body">
                  <div v-for="row in comparisonRows" :key="row.key" class="matrix-row" :class="row.leader">
                    <strong>{{ row.label }}</strong>
                    <span>{{ row.leftText }}</span>
                    <span>{{ row.rightText }}</span>
                    <span class="delta-cell">{{ row.deltaText }}</span>
                    <div class="mini-ratio">
                      <i :style="{ width: `${row.leftPct}%` }"></i>
                      <b :style="{ width: `${row.rightPct}%` }"></b>
                      <small>{{ row.ratioText }}</small>
                    </div>
                    <em>{{ row.leaderText }}</em>
                  </div>
                  <el-empty v-if="!comparisonRows.length" description="请选择两个不同对象，并保留至少一个指标" :image-size="72" />
                </div>
              </template>
            </ResizablePanel>

            <div class="chart-wall">
              <ResizablePanel
                :key="`bar-chart-${panelLayoutKey}`"
                storage-key="bar-chart"
                panel-class="chart-card"
                :default-width="520"
                :default-height="360"
                :min-width="360"
                :min-height="260"
                @resize="refreshAnalysisCharts"
              >
                <div class="panel-title compact">
                  <div>
                    <span>Bar scanner</span>
                    <h3>指标柱状图</h3>
                  </div>
                </div>
                <AnalysisChartPanel :option="barChartOption" :autoresize-key="chartResizeKey" />
              </ResizablePanel>

              <ResizablePanel
                :key="`line-chart-${panelLayoutKey}`"
                storage-key="line-chart"
                panel-class="chart-card"
                :default-width="520"
                :default-height="360"
                :min-width="360"
                :min-height="260"
                @resize="refreshAnalysisCharts"
              >
                <div class="panel-title compact">
                  <div>
                    <span>Line trace</span>
                    <h3>指标折线图</h3>
                  </div>
                </div>
                <AnalysisChartPanel :option="lineChartOption" :autoresize-key="chartResizeKey" />
              </ResizablePanel>

              <ResizablePanel
                :key="`pie-chart-${panelLayoutKey}`"
                storage-key="pie-chart"
                panel-class="chart-card"
                :default-width="520"
                :default-height="340"
                :min-width="360"
                :min-height="260"
                @resize="refreshAnalysisCharts"
              >
                <div class="panel-title compact">
                  <div>
                    <span>Share cut</span>
                    <h3>总量占比饼图</h3>
                  </div>
                </div>
                <AnalysisChartPanel :option="pieChartOption" :autoresize-key="chartResizeKey" />
              </ResizablePanel>

              <ResizablePanel
                :key="`class-analysis-${panelLayoutKey}`"
                storage-key="class-analysis"
                panel-class="class-analysis-panel"
                :default-width="520"
                :default-height="340"
                :min-width="360"
                :min-height="260"
                @resize="refreshAnalysisCharts"
              >
                <div class="panel-title compact">
                  <div>
                    <span>Same class</span>
                    <h3>同职业分析</h3>
                  </div>
                </div>
                <div class="class-analysis-list">
                  <div v-for="group in classAnalysisGroups" :key="group.className" class="class-analysis-group">
                    <div class="class-analysis-head">
                      <strong>{{ group.className }}</strong>
                      <span>{{ group.selectedCount }} / {{ group.totalCount }} 人</span>
                    </div>
                    <div
                      v-for="metric in group.metrics"
                      :key="metric.key"
                      class="class-analysis-row"
                    >
                      <span>{{ metric.label }}</span>
                      <b>均值 {{ metric.avgText }}</b>
                      <em>最高 {{ metric.maxText }}</em>
                    </div>
                  </div>
                  <el-empty v-if="!classAnalysisGroups.length" description="请选择玩家查看同职业分析" :image-size="62" />
                </div>
              </ResizablePanel>
            </div>
          </main>

          <ResizablePanel
            :key="`dense-side-${panelLayoutKey}`"
            storage-key="dense-side"
            panel-class="dense-side"
            :default-width="380"
            :default-height="720"
            :min-width="300"
            :min-height="420"
            @resize="refreshAnalysisCharts"
          >
            <section>
              <h3>A/B 贴身摘要</h3>
              <div class="compact-entity side-a">
                <span>A</span>
                <strong>{{ leftComparison?.label || '未选' }}</strong>
                <em>{{ leftComparison?.subtitle || '等待选择' }}</em>
                <small>{{ leftComparison?.membersText || leftComparison?.countText || '--' }}</small>
              </div>
              <div class="compact-entity side-b">
                <span>B</span>
                <strong>{{ rightComparison?.label || '未选' }}</strong>
                <em>{{ rightComparison?.subtitle || '等待选择' }}</em>
                <small>{{ rightComparison?.membersText || rightComparison?.countText || '--' }}</small>
              </div>
            </section>

            <section>
              <h3>指标开关</h3>
              <div class="dense-metric-picks">
                <button
                  v-for="metric in metricOptions"
                  :key="metric.key"
                  type="button"
                  :class="{ active: selectedMetricKeys.includes(metric.key) }"
                  @click="toggleMetric(metric.key)"
                >
                  {{ metric.label }}
                </button>
              </div>
            </section>

            <section>
              <h3>数据源</h3>
              <p>{{ selectedBattle?.battle_name || '历史数据未选中' }}</p>
              <p>{{ selectedSchedule?.schedule_name || '未关联排表' }}</p>
            </section>
          </ResizablePanel>
        </div>
      </div>
    </section>

    <section v-else class="analysis-shell">
      <aside class="selection-deck" data-guild-reveal>
        <div class="deck-card required-card">
          <div class="deck-heading">
            <span class="step-mark">必选</span>
            <div>
              <h3>历史导入数据</h3>
              <p>选择数据导入中保存过的一场战斗。</p>
            </div>
          </div>
          <el-select
            v-model="selectedBattleId"
            filterable
            placeholder="选择一场历史数据"
            class="deck-select"
            :loading="battleLoading"
            @change="handleBattleChange"
          >
            <el-option
              v-for="battle in battleRows"
              :key="battle.battle_id"
              :label="formatBattleLabel(battle)"
              :value="battle.battle_id"
            >
              <div class="option-line">
                <strong>{{ battle.battle_name }}</strong>
                <span>{{ battle.battle_date }} · {{ battle.opponent_name || '未知对手' }}</span>
              </div>
            </el-option>
          </el-select>
          <div class="source-ledger">
            <div class="ledger-head">
              <span>{{ battleLoading ? '同步历史数据中' : `已发现 ${battleRows.length} 场历史数据` }}</span>
              <button type="button" @click="fetchBattles">刷新</button>
            </div>
            <div v-if="battleRows.length" class="ledger-list">
              <button
                v-for="battle in battleRows.slice(0, 6)"
                :key="battle.battle_id"
                type="button"
                class="ledger-item"
                :class="{ active: selectedBattleId === battle.battle_id }"
                @click="selectBattle(battle)"
              >
                <strong>{{ battle.battle_name || `历史数据 #${battle.battle_id}` }}</strong>
                <span>{{ battle.battle_date || '未填日期' }} · {{ battle.opponent_name || '未知对手' }}</span>
              </button>
            </div>
            <div v-else class="ledger-empty">
              {{ battleLoadError || '历史数据管理有记录时，这里会自动出现。' }}
            </div>
          </div>
        </div>

        <div class="deck-card optional-card">
          <div class="deck-heading">
            <span class="step-mark optional">可选</span>
            <div>
              <h3>历史排表阵容</h3>
              <p>不选择时，只分析本场我方数据榜单。</p>
            </div>
          </div>
          <el-select
            v-model="selectedScheduleId"
            filterable
            clearable
            placeholder="选择一份历史排表"
            class="deck-select"
            :loading="scheduleLoading"
            @change="handleScheduleChange"
            @clear="handleScheduleChange"
          >
            <el-option
              v-for="schedule in scheduleRows"
              :key="schedule.schedule_id"
              :label="schedule.schedule_name"
              :value="schedule.schedule_id"
            >
              <div class="option-line">
                <strong>{{ schedule.schedule_name }}</strong>
                <span>{{ schedule.create_time || '无保存时间' }}</span>
              </div>
            </el-option>
          </el-select>
          <div class="source-ledger">
            <div class="ledger-head">
              <span>{{ scheduleLoading ? '同步排表历史中' : `已发现 ${scheduleRows.length} 份历史排表` }}</span>
              <button type="button" @click="fetchSchedules">刷新</button>
            </div>
            <div v-if="scheduleRows.length" class="ledger-list">
              <button
                v-for="schedule in scheduleRows.slice(0, 6)"
                :key="schedule.schedule_id"
                type="button"
                class="ledger-item optional"
                :class="{ active: selectedScheduleId === schedule.schedule_id }"
                @click="selectSchedule(schedule)"
              >
                <strong>{{ schedule.schedule_name || `历史排表 #${schedule.schedule_id}` }}</strong>
                <span>{{ schedule.create_time || '无保存时间' }}</span>
              </button>
            </div>
            <div v-else class="ledger-empty">
              {{ scheduleLoadError || '约战排表保存历史后，这里会自动出现。' }}
            </div>
          </div>
        </div>

        <button
          type="button"
          class="scan-button"
          :disabled="!selectedBattleId || analysisLoading"
          @click="runAnalysis"
        >
          <span>{{ analysisLoading ? '正在扫描数据' : '开始分析' }}</span>
          <i></i>
        </button>

        <div class="selection-note">
          <span class="note-dot"></span>
          <p>数据是必选项；排表只用于阵容匹配。如果成员名和战斗记录玩家名一致，就会自动关联。</p>
        </div>
      </aside>

      <main class="result-stage" data-guild-reveal>
        <div v-if="!analysisResult" class="empty-console">
          <div class="radar">
            <span></span>
          </div>
          <h2>{{ selectedBattleId ? '历史数据已锁定' : '等待选择一场历史数据' }}</h2>
          <p>
            {{ selectedBattleId
              ? '左侧已自动选中一场历史数据；确认排表阵容后点击开始分析。'
              : '这里会生成出勤匹配率、团队伤害/治疗、未参战名单和未排表参战名单。'
            }}
          </p>
          <button
            v-if="selectedBattleId"
            type="button"
            class="empty-scan-button"
            :disabled="analysisLoading"
            @click="runAnalysis"
          >
            {{ analysisLoading ? '正在扫描数据' : '用当前数据开始分析' }}
          </button>
        </div>

        <template v-else>
          <div class="battle-banner">
            <div>
              <span>{{ analysisResult.battle?.battle_date || '未填写日期' }}</span>
              <h2>{{ analysisResult.battle?.battle_name || '历史数据' }}</h2>
              <p>
                {{ analysisResult.battle?.my_guild_name || '全部帮会数据' }}
                <template v-if="analysisResult.battle?.opponent_name">
                  vs {{ analysisResult.battle.opponent_name }}
                </template>
              </p>
            </div>
            <el-tag :type="analysisResult.schedule ? 'success' : 'info'" size="large">
              {{ analysisResult.schedule ? `已关联：${analysisResult.schedule.schedule_name}` : '未关联排表' }}
            </el-tag>
          </div>

          <div class="metric-grid">
            <article
              v-for="metric in heroMetrics"
              :key="metric.label"
              class="metric-card"
              :class="metric.tone"
            >
              <span>{{ metric.label }}</span>
              <strong>{{ metric.value }}</strong>
              <small>{{ metric.hint }}</small>
            </article>
          </div>

          <div class="review-grid">
            <section class="review-panel team-panel">
              <div class="panel-title">
                <div>
                  <span>Team board</span>
                  <h3>团队复盘</h3>
                </div>
                <strong>{{ analysisResult.teams?.length || 0 }} 个团队</strong>
              </div>

              <div v-if="analysisResult.teams?.length" class="team-stack">
                <article v-for="team in analysisResult.teams" :key="team.team_id" class="team-card">
                  <div class="team-card-head">
                    <div>
                      <strong>{{ team.team_name }}</strong>
                      <span>{{ team.matched_count }} / {{ team.scheduled_count }} 人匹配</span>
                    </div>
                    <em>{{ team.match_rate }}%</em>
                  </div>
                  <div class="team-bars">
                    <span :style="{ width: `${Math.min(team.match_rate || 0, 100)}%` }"></span>
                  </div>
                  <div class="team-metrics">
                    <span>总击败 {{ team.metrics.total_kills }}</span>
                    <span>人伤 {{ formatCompact(team.metrics.dmg_to_players) }}</span>
                    <span>治疗 {{ formatCompact(team.metrics.healing) }}</span>
                  </div>
                  <div class="squad-strip">
                    <span v-for="squad in team.squads" :key="squad.squad_id">
                      {{ squad.squad_name }} {{ squad.match_rate }}%
                    </span>
                  </div>
                </article>
              </div>

              <el-empty v-else description="未选择排表，仅展示战斗数据榜单" />
            </section>

            <section class="review-panel">
              <div class="panel-title">
                <div>
                  <span>Top output</span>
                  <h3>关键榜单</h3>
                </div>
              </div>

              <el-tabs v-model="topTab" class="rank-tabs">
                <el-tab-pane label="击败" name="kills" />
                <el-tab-pane label="人伤" name="dmg_to_players" />
                <el-tab-pane label="治疗" name="healing" />
                <el-tab-pane label="承伤" name="dmg_taken" />
              </el-tabs>

              <div class="rank-list">
                <div v-for="(record, index) in currentTopRecords" :key="record.record_id || record.player_name" class="rank-row">
                  <span class="rank-index">{{ index + 1 }}</span>
                  <span class="class-pill" :style="getGuildClassStyle(record.player_class)">{{ record.player_class || '--' }}</span>
                  <strong>{{ record.player_name }}</strong>
                  <em>{{ formatTopValue(record, topTab) }}</em>
                </div>
                <el-empty v-if="!currentTopRecords.length" description="暂无榜单数据" :image-size="72" />
              </div>
            </section>
          </div>

          <div class="detail-grid">
            <section class="review-panel">
              <div class="panel-title">
                <div>
                  <span>Class heat</span>
                  <h3>职业贡献</h3>
                </div>
              </div>
              <div class="class-grid">
                <div
                  v-for="item in analysisResult.class_summary"
                  :key="item.player_class"
                  class="class-card"
                  :style="getGuildClassStyle(item.player_class)"
                >
                  <strong>{{ item.player_class }}</strong>
                  <span>{{ item.count }} 人</span>
                  <em>人伤 {{ formatCompact(item.metrics.dmg_to_players) }}</em>
                </div>
              </div>
            </section>

            <section class="review-panel exception-panel">
              <div class="panel-title">
                <div>
                  <span>Exception queue</span>
                  <h3>需要人工确认</h3>
                </div>
              </div>

              <div class="exception-columns">
                <div>
                  <h4>排表内未匹配</h4>
                  <div class="exception-list">
                    <span
                      v-for="member in analysisResult.unmatched_schedule_members"
                      :key="`${member.team_id}-${member.squad_id}-${member.member_id}`"
                    >
                      {{ member.player_name }} · {{ member.team_name }}/{{ member.squad_name }}
                    </span>
                    <em v-if="!analysisResult.unmatched_schedule_members?.length">无</em>
                  </div>
                </div>

                <div>
                  <h4>数据内未排表</h4>
                  <div class="exception-list">
                    <span v-for="record in analysisResult.unscheduled_records" :key="record.record_id || record.player_name">
                      {{ record.player_name }} · {{ record.player_class || '--' }}
                    </span>
                    <em v-if="!analysisResult.unscheduled_records?.length">无</em>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </template>
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getBattleList, getBattleRecords } from '@/api/guild/battle'
import { getScheduleDetail, getScheduleHistory } from '@/api/guild/schedule'
import { analyzeScheduleBattle } from '@/api/guild/analysis'
import { useGuildClassColors } from '@/utils/guildClassColor'
import { useGuildPageMotion } from '@/composables/useGuildPageMotion'
import AnalysisChartPanel from './components/AnalysisChartPanel.vue'
import ResizablePanel from './components/ResizablePanel.vue'

let analysisGsapLoader = null
function loadAnalysisGsap() {
  if (!analysisGsapLoader) {
    analysisGsapLoader = import('gsap').then(gsapModule => gsapModule.gsap || gsapModule.default || gsapModule)
  }
  return analysisGsapLoader
}

const pageRef = ref(null)
const battleRows = ref([])
const scheduleRows = ref([])
const selectedBattleId = ref(null)
const selectedScheduleId = ref(null)
const battleLoading = ref(false)
const scheduleLoading = ref(false)
const analysisLoading = ref(false)
const analysisResult = ref(null)
const topTab = ref('kills')
const battleLoadError = ref('')
const scheduleLoadError = ref('')
const battleRecords = ref([])
const scheduleDetail = ref(null)
const battleRecordsLoading = ref(false)
const scheduleDetailLoading = ref(false)
const isFullscreen = ref(false)
const compareMode = ref('player')
const compareLeftId = ref('')
const compareRightId = ref('')
const selectedMetricKeys = ref([
  'kills',
  'qingquan_kills',
  'assists',
  'dmg_to_players',
  'armor_break_players',
  'dmg_to_buildings',
  'armor_break_buildings',
  'healing',
  'dmg_taken',
  'deaths',
  'revives',
  'burn_bones',
  'resources',
  'total_kills'
])
const selectedComparisonIds = ref([])
const comparisonSearch = ref('')
const draggingComparisonId = ref('')
const chartResizeKey = ref(0)
const panelLayoutKey = ref(0)
const onlyMyGuildScope = ref(true)
const hideZeroRows = ref(false)
const { getGuildClassStyle, loadGuildClassColors } = useGuildClassColors()

useGuildPageMotion(pageRef)

const metricOptions = [
  { key: 'kills', label: '击败' },
  { key: 'qingquan_kills', label: '清泉' },
  { key: 'assists', label: '助攻' },
  { key: 'dmg_to_players', label: '对玩家伤害' },
  { key: 'armor_break_players', label: '人伤卸甲' },
  { key: 'dmg_to_buildings', label: '对建筑伤害' },
  { key: 'armor_break_buildings', label: '破塔卸甲' },
  { key: 'healing', label: '治疗值' },
  { key: 'dmg_taken', label: '承受伤害' },
  { key: 'deaths', label: '重伤' },
  { key: 'revives', label: '复活' },
  { key: 'burn_bones', label: '焚骨' },
  { key: 'resources', label: '资源' },
  { key: 'total_kills', label: '总击败' }
]

const compareModes = [
  { value: 'player', label: '玩家对玩家', hint: '任意选择两名玩家' },
  { value: 'team', label: '队伍对队伍', hint: '任意选择两个排表队伍' }
]

const analysisOptionSwitches = computed(() => [
  { key: 'guild', label: '只看我方帮会', model: onlyMyGuildScope },
  { key: 'zero', label: '隐藏零数据指标', model: hideZeroRows }
])

const heroMetrics = computed(() => {
  const summary = analysisResult.value?.summary || {}
  return [
    {
      label: '匹配率',
      value: analysisResult.value?.schedule ? `${summary.match_rate || 0}%` : '未关联',
      hint: analysisResult.value?.schedule ? `${summary.matched_count || 0}/${summary.scheduled_count || 0} 人` : '只看导入数据',
      tone: 'signal'
    },
    {
      label: '总击败',
      value: formatCompact(summary.total_kills),
      hint: `击败 ${summary.kills || 0} / 清泉 ${summary.qingquan_kills || 0}`,
      tone: 'impact'
    },
    {
      label: '对玩家伤害',
      value: formatCompact(summary.dmg_to_players),
      hint: `承伤 ${formatCompact(summary.dmg_taken)}`,
      tone: 'damage'
    },
    {
      label: '治疗量',
      value: formatCompact(summary.healing),
      hint: `复活 ${summary.revives || 0} 次`,
      tone: 'heal'
    }
  ]
})

const currentTopRecords = computed(() => {
  const records = analysisResult.value?.top_records?.[topTab.value] || []
  return records
})

const selectedBattle = computed(() => {
  return battleRows.value.find(item => item.battle_id === selectedBattleId.value) || null
})

const selectedSchedule = computed(() => {
  return scheduleDetail.value || scheduleRows.value.find(item => item.schedule_id === selectedScheduleId.value) || null
})

const sourceStatusItems = computed(() => [
  {
    key: 'battle',
    label: '历史数据管理',
    title: `${battleRows.value.length} 场可分析`,
    detail: selectedBattle.value
      ? `当前：${selectedBattle.value.battle_name || `#${selectedBattle.value.battle_id}`}`
      : (battleLoadError.value || '数据是必选项，加载后会自动选中最近一场。'),
    count: battleRows.value.length,
    loading: battleLoading.value,
    ready: Boolean(selectedBattleId.value),
    tone: 'battle'
  },
  {
    key: 'schedule',
    label: '约战排表历史',
    title: `${scheduleRows.value.length} 份可关联`,
    detail: selectedSchedule.value
      ? `当前：${selectedSchedule.value.schedule_name || `#${selectedSchedule.value.schedule_id}`}`
      : (scheduleRows.value.length ? '可选：点击左侧排表卡片关联阵容。' : (scheduleLoadError.value || '没有关联排表时仍可分析导入数据。')),
    count: scheduleRows.value.length,
    loading: scheduleLoading.value,
    ready: Boolean(selectedScheduleId.value),
    tone: 'schedule'
  }
])

const battleScopeRecords = computed(() => {
  const records = battleRecords.value
  if (!onlyMyGuildScope.value) return records
  const guildName = selectedBattle.value?.my_guild_name?.trim()
  if (!guildName) return records
  return records.filter(record => String(record.guild_name || '').trim() === guildName)
})

const playerComparisonItems = computed(() => aggregateComparisonRows(
  battleScopeRecords.value,
  record => normalizeComparisonKey(record.player_name),
  record => ({
    id: `player:${normalizeComparisonKey(record.player_name)}:${normalizeComparisonKey(record.player_class)}`,
    label: record.player_name || '未知成员',
    subtitle: [record.player_class || '未设置', record.guild_name || '未知帮会'].filter(Boolean).join(' · '),
    tagText: record.player_class || '未设置',
    metrics: record.metrics,
    membersText: `${record.count} 次记录`,
    countText: `${record.count} 条`,
    accent: record.player_class
  })
))

const teamComparisonItems = computed(() => {
  return (analysisResult.value?.teams || []).map(team => ({
    id: `team:${team.team_id}`,
    label: team.team_name || `团队 #${team.team_id}`,
    subtitle: `${team.matched_count || 0}/${team.scheduled_count || 0} 人匹配`,
    tagText: `${team.match_rate || 0}% 匹配率`,
    metrics: team.metrics || {},
    membersText: `${team.squads?.length || 0} 个小队`,
    countText: `${team.scheduled_count || 0} 人`,
    accent: team.team_name
  }))
})

const comparisonOptions = computed(() => {
  switch (compareMode.value) {
    case 'team':
      return teamComparisonItems.value
    default:
      return playerComparisonItems.value
  }
})

const compareModeLabel = computed(() => compareModes.find(mode => mode.value === compareMode.value)?.label || '对比模式')
const compareLeftPlaceholder = computed(() => compareMode.value === 'team' ? '选择队伍 A' : '选择玩家 A')
const compareRightPlaceholder = computed(() => compareMode.value === 'team' ? '选择队伍 B' : '选择玩家 B')
const comparisonOptionCountLabel = computed(() => `${comparisonOptions.value.length} 个${compareMode.value === 'team' ? '队伍' : '玩家'}可选`)
const comparisonSourceHint = computed(() => compareMode.value === 'team'
  ? '来自历史排表匹配后的团队结果'
  : '来自导入战斗数据，可任意指定 A/B')

const visibleComparisonOptions = computed(() => {
  const keyword = comparisonSearch.value.trim().toLowerCase()
  const items = comparisonOptions.value
  if (!keyword) return items.slice(0, 80)
  return items.filter(item => [
    item.label,
    item.subtitle,
    item.tagText
  ].some(value => String(value || '').toLowerCase().includes(keyword))).slice(0, 80)
})

const compareLeftItem = computed(() => comparisonOptions.value.find(item => item.id === compareLeftId.value) || comparisonOptions.value[0] || null)
const compareRightItem = computed(() => {
  return comparisonOptions.value.find(item => item.id === compareRightId.value)
    || comparisonOptions.value[1]
    || comparisonOptions.value[0]
    || null
})

const leftComparison = computed(() => compareLeftItem.value)
const rightComparison = computed(() => compareRightItem.value)

const comparisonHeadline = computed(() => {
  if (!comparisonOptions.value.length) {
    return compareMode.value === 'team'
      ? '先关联历史排表并运行分析，再选择两个队伍'
      : '等待加载战斗记录'
  }
  return `${leftComparison.value?.label || '对象 A'} vs ${rightComparison.value?.label || '对象 B'}`
})

const comparisonSubtitle = computed(() => {
  if (!comparisonOptions.value.length) {
    return compareMode.value === 'team'
      ? '队伍数据来自历史排表和导入数据的匹配结果。'
      : '玩家数据来自当前导入的战斗明细。'
  }
  return `${selectedMetricKeys.value.length} 个指标 · ${onlyMyGuildScope.value ? '仅我方帮会' : '全部帮会'}`
})

const comparisonDeltaLabel = computed(() => {
  const left = leftComparison.value
  const right = rightComparison.value
  if (!left || !right || left.id === right.id) return '等待选择不同对象'
  const leftValue = left.metrics?.total_kills || 0
  const rightValue = right.metrics?.total_kills || 0
  const delta = leftValue - rightValue
  if (delta === 0) return '总击败相同'
  return `${delta > 0 ? 'A 侧领先' : 'B 侧领先'} ${formatCompact(Math.abs(delta))}`
})

const comparisonRows = computed(() => {
  const left = leftComparison.value
  const right = rightComparison.value
  if (!left || !right || left.id === right.id) return []
  return selectedMetricKeys.value
    .map(metricKey => {
      const metric = metricOptions.find(item => item.key === metricKey)
      if (!metric) return null
      const leftValue = Number(left.metrics?.[metricKey] || 0)
      const rightValue = Number(right.metrics?.[metricKey] || 0)
      if (hideZeroRows.value && !leftValue && !rightValue) return null
      const total = leftValue + rightValue
      const leftPct = total ? Math.max(12, Math.round((leftValue / total) * 100)) : 50
      const rightPct = total ? Math.max(12, 100 - leftPct) : 50
      return {
        key: metricKey,
        label: metric.label,
        leftPct,
        rightPct,
        leftText: formatComparisonMetric(metricKey, leftValue),
        rightText: formatComparisonMetric(metricKey, rightValue),
        deltaText: buildMetricDelta(leftValue, rightValue),
        ratioText: `${leftPct}:${rightPct}`,
        leader: leftValue > rightValue ? 'leader-a' : (rightValue > leftValue ? 'leader-b' : 'leader-even'),
        leaderText: leftValue > rightValue ? 'A 高' : (rightValue > leftValue ? 'B 高' : '持平')
      }
    })
    .filter(Boolean)
})

const activeMetricOptions = computed(() => {
  const selected = new Set(selectedMetricKeys.value)
  return metricOptions.filter(metric => selected.has(metric.key))
})

const selectedComparisonItems = computed(() => {
  const optionMap = new Map(comparisonOptions.value.map(item => [item.id, item]))
  return selectedComparisonIds.value
    .map(id => optionMap.get(id))
    .filter(Boolean)
})

const isMultiComparison = computed(() => selectedComparisonItems.value.length > 2)

const multiMatrixGridStyle = computed(() => ({
  gridTemplateColumns: `170px repeat(${Math.max(selectedComparisonItems.value.length, 1)}, minmax(170px, 1fr)) minmax(260px, 0.9fr)`
}))

const multiComparisonRows = computed(() => activeMetricOptions.value
  .map(metric => {
    const values = selectedComparisonItems.value.map(item => ({
      id: item.id,
      label: item.label,
      value: getMetricValue(item, metric.key),
      text: formatComparisonMetric(metric.key, getMetricValue(item, metric.key))
    }))
    if (hideZeroRows.value && values.every(item => !item.value)) return null
    const maxValue = Math.max(...values.map(item => item.value), 0)
    const minValue = Math.min(...values.map(item => item.value), 0)
    const avgValue = values.length
      ? values.reduce((sum, item) => sum + item.value, 0) / values.length
      : 0
    const maxItems = values.filter(item => item.value === maxValue)
    const minItems = values.filter(item => item.value === minValue)
    const gap = maxValue - minValue
    return {
      key: metric.key,
      label: metric.label,
      cells: values.map(item => ({
        ...item,
        isMax: values.length > 1 && item.value === maxValue,
        isMin: values.length > 1 && item.value === minValue
      })),
      judgement: `最高 ${maxItems.map(item => item.label).join('、') || '--'} · 最低 ${minItems.map(item => item.label).join('、') || '--'} · 均值 ${formatComparisonMetric(metric.key, Math.round(avgValue))} · 差距 ${formatComparisonMetric(metric.key, gap)}`
    }
  })
  .filter(Boolean))

const barChartOption = computed(() => {
  const items = selectedComparisonItems.value
  const metrics = activeMetricOptions.value
  if (!items.length || !metrics.length) return buildEmptyChartOption('拖入对象后显示柱状图')
  return {
    color: buildChartColors(metrics.length),
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: {
      top: 0,
      type: 'scroll',
      textStyle: { color: '#17212b', fontWeight: 800 }
    },
    grid: { top: 44, left: 46, right: 16, bottom: items.length > 8 ? 58 : 34, containLabel: true },
    xAxis: {
      type: 'category',
      data: items.map(item => item.label),
      axisLabel: { color: '#17212b', fontWeight: 800, interval: 0, rotate: items.length > 6 ? 28 : 0 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#6e746f', formatter: value => formatCompact(value) },
      splitLine: { lineStyle: { color: 'rgba(28, 39, 51, 0.1)' } }
    },
    dataZoom: items.length > 8
      ? [{ type: 'slider', height: 18, bottom: 16 }, { type: 'inside' }]
      : [],
    series: metrics.map(metric => ({
      name: metric.label,
      type: 'bar',
      barMaxWidth: 18,
      emphasis: { focus: 'series' },
      data: items.map(item => getMetricValue(item, metric.key))
    }))
  }
})

const lineChartOption = computed(() => {
  const items = selectedComparisonItems.value
  const metrics = activeMetricOptions.value
  if (!items.length || !metrics.length) return buildEmptyChartOption('拖入对象后显示折线图')
  return {
    color: buildChartColors(items.length),
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      type: 'scroll',
      textStyle: { color: '#17212b', fontWeight: 800 }
    },
    grid: { top: 44, left: 46, right: 18, bottom: metrics.length > 8 ? 58 : 34, containLabel: true },
    xAxis: {
      type: 'category',
      data: metrics.map(metric => metric.label),
      axisLabel: { color: '#17212b', fontWeight: 800, interval: 0, rotate: metrics.length > 7 ? 28 : 0 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#6e746f', formatter: value => formatCompact(value) },
      splitLine: { lineStyle: { color: 'rgba(28, 39, 51, 0.1)' } }
    },
    dataZoom: metrics.length > 8
      ? [{ type: 'slider', height: 18, bottom: 16 }, { type: 'inside' }]
      : [],
    series: items.map(item => ({
      name: item.label,
      type: 'line',
      symbolSize: 6,
      smooth: true,
      emphasis: { focus: 'series' },
      data: metrics.map(metric => getMetricValue(item, metric.key))
    }))
  }
})

const pieChartOption = computed(() => {
  const items = selectedComparisonItems.value
  const metrics = activeMetricOptions.value
  if (!items.length || !metrics.length) return buildEmptyChartOption('拖入对象后显示占比')
  const data = items.map(item => ({
    name: item.label,
    value: metrics.reduce((sum, metric) => sum + getMetricValue(item, metric.key), 0)
  }))
  return {
    color: buildChartColors(items.length),
    tooltip: { trigger: 'item', formatter: params => `${params.name}<br/>${formatCompact(params.value)} (${params.percent}%)` },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 4,
      top: 18,
      bottom: 18,
      textStyle: { color: '#17212b', fontWeight: 800 }
    },
    series: [{
      name: '总量占比',
      type: 'pie',
      radius: ['42%', '72%'],
      center: ['36%', '54%'],
      minAngle: 4,
      avoidLabelOverlap: true,
      label: {
        formatter: params => `${params.name}\n${params.percent}%`,
        color: '#17212b',
        fontWeight: 800
      },
      data
    }]
  }
})

const classAnalysisGroups = computed(() => {
  if (compareMode.value !== 'player') return []
  const selectedPlayers = selectedComparisonItems.value
    .filter(item => item.id?.startsWith('player:'))
    .filter(item => item.accent)
  if (!selectedPlayers.length) return []
  const selectedClasses = Array.from(new Set(selectedPlayers.map(item => item.accent || '未设置')))
  return selectedClasses.map(className => {
    const peers = playerComparisonItems.value.filter(item => (item.accent || '未设置') === className)
    const selectedCount = selectedPlayers.filter(item => (item.accent || '未设置') === className).length
    return {
      className,
      selectedCount,
      totalCount: peers.length,
      metrics: activeMetricOptions.value.map(metric => {
        const values = peers.map(item => getMetricValue(item, metric.key))
        const avg = values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0
        const max = values.length ? Math.max(...values) : 0
        return {
          key: metric.key,
          label: metric.label,
          avgText: formatComparisonMetric(metric.key, Math.round(avg)),
          maxText: formatComparisonMetric(metric.key, max)
        }
      })
    }
  })
})

watch(comparisonOptions, items => {
  if (!items.length) {
    compareLeftId.value = ''
    compareRightId.value = ''
    selectedComparisonIds.value = []
    return
  }
  const hasLeft = items.some(item => item.id === compareLeftId.value)
  const hasRight = items.some(item => item.id === compareRightId.value)
  if (!hasLeft) {
    compareLeftId.value = items[0].id
  }
  if (!hasRight) {
    compareRightId.value = items[1]?.id || items[0].id
  }
  const validIds = new Set(items.map(item => item.id))
  const nextSelected = selectedComparisonIds.value.filter(id => validIds.has(id))
  if (!nextSelected.length) {
    nextSelected.push(items[0].id)
    if (items[1]) nextSelected.push(items[1].id)
  }
  selectedComparisonIds.value = nextSelected
}, { immediate: true })

watch(
  [selectedComparisonItems, activeMetricOptions, isFullscreen, hideZeroRows],
  () => refreshAnalysisCharts(),
  { deep: true }
)

watch(selectedBattleId, async battleId => {
  analysisResult.value = null
  battleRecords.value = []
  if (battleId) {
    await fetchBattleRecords(battleId)
  }
}, { immediate: true })

watch(selectedScheduleId, async scheduleId => {
  analysisResult.value = null
  scheduleDetail.value = null
  if (scheduleId) {
    await fetchScheduleDetail(scheduleId)
  }
}, { immediate: true })

watch(compareMode, () => {
  comparisonSearch.value = ''
  compareLeftId.value = ''
  compareRightId.value = ''
})

function formatBattleLabel(battle) {
  return `${battle.battle_date || '未填日期'} · ${battle.battle_name || `#${battle.battle_id}`}`
}

function formatCompact(value) {
  const number = Number(value || 0)
  if (number >= 100000000) return `${(number / 100000000).toFixed(2)}亿`
  if (number >= 10000) return `${(number / 10000).toFixed(1)}万`
  return number.toLocaleString()
}

function formatTopValue(record, field) {
  if (field === 'kills') return `${record.total_kills || 0} 击败`
  return formatCompact(record[field])
}

function formatComparisonMetric(field, value) {
  if (field === 'deaths') return `${value || 0} 次`
  return formatCompact(value)
}

function buildMetricDelta(leftValue, rightValue) {
  const delta = leftValue - rightValue
  if (delta === 0) return '持平'
  return `${delta > 0 ? '+' : '-'}${formatCompact(Math.abs(delta))}`
}

function getMetricValue(item, metricKey) {
  return Number(item?.metrics?.[metricKey] || 0)
}

function buildChartColors(count) {
  const palette = [
    '#28576a',
    '#a35b37',
    '#d9b66f',
    '#426b4f',
    '#7a4f6f',
    '#49618c',
    '#9a7a34',
    '#35424c',
    '#c06f45',
    '#6f8c74'
  ]
  return Array.from({ length: count }, (_, index) => palette[index % palette.length])
}

function buildEmptyChartOption(text) {
  return {
    title: {
      text,
      left: 'center',
      top: 'middle',
      textStyle: {
        color: '#6e746f',
        fontSize: 16,
        fontWeight: 900
      }
    },
    xAxis: { show: false },
    yAxis: { show: false },
    series: []
  }
}

function refreshAnalysisCharts() {
  chartResizeKey.value += 1
}

function resetAnalysisPanelLayout() {
  try {
    localStorage.removeItem('guild-analysis:panel-sizes:v1')
  } catch {
    // localStorage can be unavailable in restricted browser contexts.
  }
  panelLayoutKey.value += 1
  refreshAnalysisCharts()
}

function getComparisonAccentStyle(item) {
  if (compareMode.value === 'player' && item?.accent) {
    return getGuildClassStyle(item.accent)
  }
  return {
    background: item?.id === compareLeftId.value
      ? 'var(--analysis-sea)'
      : (item?.id === compareRightId.value ? 'var(--analysis-rust)' : 'var(--analysis-glow)')
  }
}

function unwrapResponseData(res) {
  return res?.data ?? res ?? {}
}

function normalizeBattleRows(payload) {
  const data = unwrapResponseData(payload)
  if (Array.isArray(data)) return data
  if (Array.isArray(data.rows)) return data.rows
  if (Array.isArray(data.data?.rows)) return data.data.rows
  return []
}

function normalizeBattleRecordRows(payload) {
  const data = unwrapResponseData(payload)
  if (Array.isArray(data)) return data
  if (Array.isArray(data.rows)) return data.rows
  if (Array.isArray(data.data)) return data.data
  if (Array.isArray(data.data?.rows)) return data.data.rows
  return []
}

function normalizeScheduleRows(payload) {
  const data = unwrapResponseData(payload)
  if (Array.isArray(data)) return data
  if (Array.isArray(data.rows)) return data.rows
  if (Array.isArray(data.data)) return data.data
  return []
}

function normalizeComparisonKey(value) {
  return String(value || '').trim().toLowerCase()
}

function emptyMetricBucket() {
  return metricOptions.reduce((acc, metric) => {
    acc[metric.key] = 0
    return acc
  }, { total_kills: 0, kills: 0, qingquan_kills: 0, assists: 0, resources: 0, dmg_to_players: 0, armor_break_players: 0, dmg_to_buildings: 0, armor_break_buildings: 0, healing: 0, dmg_taken: 0, deaths: 0, revives: 0, burn_bones: 0 })
}

function sumMetricBucket(target, source) {
  const result = { ...target }
  Object.keys(result).forEach(key => {
    if (key === 'total_kills') return
    result[key] += Number(source?.[key] || 0)
  })
  result.total_kills = result.kills + result.qingquan_kills
  return result
}

function normalizeBattleRecord(record) {
  const metrics = emptyMetricBucket()
  Object.keys(metrics).forEach(key => {
    if (key === 'total_kills') return
    metrics[key] = Number(record?.[key] || 0)
  })
  metrics.total_kills = metrics.kills + metrics.qingquan_kills
  return {
    player_name: record?.player_name || '',
    player_class: record?.player_class || '',
    guild_name: record?.guild_name || '',
    metrics
  }
}

function aggregateComparisonRows(records, keyGetter, mapper) {
  const groups = new Map()
  records.forEach(record => {
    const normalized = normalizeBattleRecord(record)
    const key = keyGetter(normalized)
    if (!key) return
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        labelSource: normalized,
        count: 0,
        metrics: emptyMetricBucket()
      })
    }
    const bucket = groups.get(key)
    bucket.count += 1
    bucket.metrics = sumMetricBucket(bucket.metrics, normalized.metrics)
    if (!bucket.labelSource.player_name && normalized.player_name) {
      bucket.labelSource = normalized
    }
    if (!bucket.labelSource.player_class && normalized.player_class) {
      bucket.labelSource.player_class = normalized.player_class
    }
    if (!bucket.labelSource.guild_name && normalized.guild_name) {
      bucket.labelSource.guild_name = normalized.guild_name
    }
  })

  return Array.from(groups.values())
    .map(item => mapper({
      ...item.labelSource,
      count: item.count,
      metrics: item.metrics
    }))
    .filter(Boolean)
    .sort((a, b) => (b.metrics?.total_kills || 0) - (a.metrics?.total_kills || 0))
}

function selectBattle(battle) {
  selectedBattleId.value = battle?.battle_id || null
  handleBattleChange()
}

function selectSchedule(schedule) {
  selectedScheduleId.value = schedule?.schedule_id || null
  handleScheduleChange()
}

function handleBattleChange() {
  analysisResult.value = null
}

function handleScheduleChange() {
  analysisResult.value = null
}

function toggleMetric(metricKey) {
  if (selectedMetricKeys.value.includes(metricKey)) {
    if (selectedMetricKeys.value.length === 1) return
    selectedMetricKeys.value = selectedMetricKeys.value.filter(key => key !== metricKey)
    return
  }
  selectedMetricKeys.value = [...selectedMetricKeys.value, metricKey]
}

function setCompareMode(mode) {
  compareMode.value = mode
}

function addComparisonItem(id) {
  if (!comparisonOptions.value.some(item => item.id === id)) return
  if (selectedComparisonIds.value.includes(id)) return
  selectedComparisonIds.value = [...selectedComparisonIds.value, id]
  refreshAnalysisCharts()
}

function removeComparisonItem(id) {
  selectedComparisonIds.value = selectedComparisonIds.value.filter(itemId => itemId !== id)
  refreshAnalysisCharts()
}

function clearSelectedComparisonItems() {
  selectedComparisonIds.value = []
  refreshAnalysisCharts()
}

function handleComparisonDragStart(event, id) {
  draggingComparisonId.value = id
  event?.dataTransfer?.setData('text/plain', id)
  if (event?.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy'
  }
}

function handleComparisonDrop(event) {
  const id = event?.dataTransfer?.getData('text/plain') || draggingComparisonId.value
  if (id) addComparisonItem(id)
  draggingComparisonId.value = ''
}

function setComparisonSide(id, side) {
  if (!comparisonOptions.value.some(item => item.id === id)) return
  addComparisonItem(id)
  if (side === 'left') {
    compareLeftId.value = id
    if (compareRightId.value === id) {
      compareRightId.value = comparisonOptions.value.find(item => item.id !== id)?.id || ''
    }
    return
  }
  compareRightId.value = id
  if (compareLeftId.value === id) {
    compareLeftId.value = comparisonOptions.value.find(item => item.id !== id)?.id || ''
  }
}

function handleComparisonSelect(side) {
  addComparisonItem(side === 'left' ? compareLeftId.value : compareRightId.value)
  if (compareLeftId.value !== compareRightId.value) return
  const fallback = comparisonOptions.value.find(item => item.id !== compareLeftId.value)?.id || ''
  if (side === 'left') {
    compareRightId.value = fallback
    addComparisonItem(fallback)
    return
  }
  compareLeftId.value = fallback
  addComparisonItem(fallback)
}

function swapComparisonSides() {
  const left = compareLeftId.value
  compareLeftId.value = compareRightId.value
  compareRightId.value = left
  addComparisonItem(compareLeftId.value)
  addComparisonItem(compareRightId.value)
}

async function fetchBattleRecords(battleId) {
  if (!battleId) {
    battleRecords.value = []
    return
  }
  battleRecordsLoading.value = true
  try {
    const res = await getBattleRecords(battleId)
    battleRecords.value = normalizeBattleRecordRows(res)
  } catch {
    battleRecords.value = []
    ElMessage.error('加载战斗明细失败')
  } finally {
    battleRecordsLoading.value = false
  }
}

async function fetchScheduleDetail(scheduleId) {
  if (!scheduleId) {
    scheduleDetail.value = null
    return
  }
  scheduleDetailLoading.value = true
  try {
    const res = await getScheduleDetail(scheduleId)
    scheduleDetail.value = res.data || null
  } catch {
    scheduleDetail.value = null
    ElMessage.error('加载排表详情失败')
  } finally {
    scheduleDetailLoading.value = false
  }
}

async function ensureAnalysisContext() {
  if (selectedBattleId.value && !battleRecords.value.length) {
    await fetchBattleRecords(selectedBattleId.value)
  }
  if (selectedScheduleId.value && !scheduleDetail.value) {
    await fetchScheduleDetail(selectedScheduleId.value)
  }
  if (selectedBattleId.value && !analysisResult.value) {
    await runAnalysis()
  }
}

async function toggleFullscreen() {
  if (isFullscreen.value) {
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else {
      isFullscreen.value = false
    }
    return
  }

  try {
    await pageRef.value?.requestFullscreen?.()
  } catch {
    // 若浏览器限制全屏，仍切换到全屏布局。
  }
  isFullscreen.value = true
  await ensureAnalysisContext()
}

function syncFullscreenState() {
  isFullscreen.value = Boolean(document.fullscreenElement)
}

async function animateResults() {
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  await nextTick()
  const root = pageRef.value
  if (!root) return
  const gsap = await loadAnalysisGsap()
  const targets = root.querySelectorAll('.battle-banner, .metric-card, .review-panel')
  gsap.fromTo(
    targets,
    { autoAlpha: 0, y: 14 },
    {
      autoAlpha: 1,
      y: 0,
      duration: 0.42,
      ease: 'power3.out',
      stagger: 0.045,
      overwrite: true
    }
  )
}

async function runAnalysis() {
  if (!selectedBattleId.value) {
    ElMessage.warning('请先选择历史导入数据')
    return
  }

  analysisLoading.value = true
  try {
    const res = await analyzeScheduleBattle({
      battle_id: selectedBattleId.value,
      schedule_id: selectedScheduleId.value || undefined
    })
    analysisResult.value = res.data || null
    await animateResults()
  } catch {
    ElMessage.error('分析失败')
  } finally {
    analysisLoading.value = false
  }
}

async function fetchBattles() {
  battleLoading.value = true
  battleLoadError.value = ''
  try {
    const res = await getBattleList({ page: 1, size: 100 })
    battleRows.value = normalizeBattleRows(res)
    if (!selectedBattleId.value && battleRows.value.length) {
      selectedBattleId.value = battleRows.value[0].battle_id
    }
    if (!battleRows.value.length) {
      battleLoadError.value = '接口已响应，但没有返回历史数据。'
    }
  } catch {
    battleLoadError.value = '历史数据加载失败，请检查接口权限或登录状态。'
    ElMessage.error('加载历史数据失败')
  } finally {
    battleLoading.value = false
  }
}

async function fetchSchedules() {
  scheduleLoading.value = true
  scheduleLoadError.value = ''
  try {
    const res = await getScheduleHistory()
    scheduleRows.value = normalizeScheduleRows(res)
    if (!scheduleRows.value.length) {
      scheduleLoadError.value = '接口已响应，但没有返回历史排表。'
    }
  } catch {
    scheduleLoadError.value = '历史排表加载失败，请检查 guild:schedule:history 权限。'
    ElMessage.error('加载历史排表失败')
  } finally {
    scheduleLoading.value = false
  }
}

onMounted(() => {
  fetchBattles()
  fetchSchedules()
  loadGuildClassColors()
  document.addEventListener('fullscreenchange', syncFullscreenState)
  syncFullscreenState()
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', syncFullscreenState)
})
</script>

<style scoped>
.analysis-page {
  --analysis-ink: #17231d;
  --analysis-muted: #6d7a70;
  --analysis-panel: rgba(251, 249, 240, 0.86);
  --analysis-line: rgba(68, 84, 72, 0.18);
  --analysis-field: #e8e0cd;
  --analysis-glow: #d9ff6a;
  --analysis-rust: #b95530;
  --analysis-sea: #1f7d70;
  --analysis-blueprint: #213f36;
  min-height: calc(100vh - 84px);
  background:
    radial-gradient(circle at 8% 8%, rgba(217, 255, 106, 0.3), transparent 24%),
    radial-gradient(circle at 90% 20%, rgba(31, 125, 112, 0.16), transparent 28%),
    linear-gradient(135deg, #f7f2df 0%, #ece4cf 45%, #d9d2bf 100%);
  color: var(--analysis-ink);
  overflow: hidden;
}

.analysis-hero {
  position: relative;
  min-height: 190px;
  border: 1px solid var(--analysis-line);
  border-radius: 28px;
  padding: 30px;
  background:
    linear-gradient(90deg, rgba(23, 35, 29, 0.08) 1px, transparent 1px) 0 0 / 38px 38px,
    linear-gradient(180deg, rgba(23, 35, 29, 0.07) 1px, transparent 1px) 0 0 / 38px 38px,
    rgba(255, 252, 241, 0.74);
  box-shadow: 0 24px 70px rgba(60, 54, 38, 0.16);
  display: flex;
  justify-content: space-between;
  gap: 28px;
  overflow: hidden;
}

.analysis-hero::after {
  content: "";
  position: absolute;
  right: -80px;
  top: -120px;
  width: 310px;
  height: 310px;
  border: 1px solid rgba(23, 35, 29, 0.18);
  border-radius: 50%;
  background: conic-gradient(from 130deg, transparent, rgba(217, 255, 106, 0.48), transparent 45%);
  animation: radarSweep 7s linear infinite;
}

.hero-copy {
  position: relative;
  z-index: 1;
  max-width: 760px;
}

.eyebrow,
.panel-title span,
.hero-scope span {
  color: var(--analysis-rust);
  font-family: "Bahnschrift", "DIN Condensed", sans-serif;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.hero-copy h1 {
  margin: 8px 0 12px;
  font-family: "STZhongsong", "Songti SC", serif;
  font-size: clamp(34px, 5vw, 64px);
  font-weight: 900;
  letter-spacing: -0.06em;
}

.hero-copy p,
.hero-scope,
.deck-heading p,
.empty-console p,
.battle-banner p {
  color: var(--analysis-muted);
  line-height: 1.75;
}

.hero-scope {
  position: relative;
  z-index: 1;
  align-self: flex-end;
  width: min(340px, 100%);
  border-left: 3px solid var(--analysis-glow);
  padding: 14px 0 14px 18px;
  background: rgba(255, 255, 255, 0.34);
  backdrop-filter: blur(10px);
}

.hero-scope strong {
  display: block;
  margin-top: 7px;
  font-size: 16px;
}

.fullscreen-button,
.cockpit-exit {
  border: 0;
  border-radius: 999px;
  background: var(--analysis-ink);
  color: #f8f3dc;
  cursor: pointer;
  font-weight: 900;
  letter-spacing: 0.06em;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.fullscreen-button {
  margin-top: 12px;
  padding: 10px 16px;
}

.fullscreen-button:hover,
.cockpit-exit:hover {
  box-shadow: 0 12px 28px rgba(33, 63, 54, 0.24);
  transform: translateY(-2px);
}

.analysis-page.is-fullscreen {
  --analysis-ink: #17212b;
  --analysis-muted: #6e746f;
  --analysis-panel: rgba(250, 246, 235, 0.9);
  --analysis-line: rgba(28, 39, 51, 0.14);
  --analysis-field: #e6decc;
  --analysis-glow: #d9b66f;
  --analysis-rust: #a35b37;
  --analysis-sea: #28576a;
  --analysis-blueprint: #17212b;
  background:
    linear-gradient(90deg, rgba(23, 33, 43, 0.045) 1px, transparent 1px) 0 0 / 34px 34px,
    linear-gradient(180deg, rgba(23, 33, 43, 0.045) 1px, transparent 1px) 0 0 / 34px 34px,
    radial-gradient(circle at 12% 10%, rgba(217, 182, 111, 0.28), transparent 24%),
    radial-gradient(circle at 88% 14%, rgba(40, 87, 106, 0.14), transparent 23%),
    linear-gradient(135deg, #f7f0de 0%, #eee4cf 48%, #ded3bd 100%);
}

.analysis-page.is-fullscreen {
  min-height: 100vh;
  height: 100vh;
  padding: 10px;
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable both-edges;
}

.analysis-page:fullscreen {
  width: 100vw;
  height: 100vh;
  overflow: auto;
  background:
    linear-gradient(90deg, rgba(23, 33, 43, 0.045) 1px, transparent 1px) 0 0 / 34px 34px,
    linear-gradient(180deg, rgba(23, 33, 43, 0.045) 1px, transparent 1px) 0 0 / 34px 34px,
    radial-gradient(circle at 12% 10%, rgba(217, 182, 111, 0.28), transparent 24%),
    radial-gradient(circle at 88% 14%, rgba(40, 87, 106, 0.14), transparent 23%),
    linear-gradient(135deg, #f7f0de 0%, #eee4cf 48%, #ded3bd 100%);
}

.analysis-page.is-fullscreen > .analysis-hero,
.analysis-page.is-fullscreen > .source-status-board {
  display: none;
}

.analysis-page.is-fullscreen .deck-card,
.analysis-page.is-fullscreen .battle-banner,
.analysis-page.is-fullscreen .review-panel,
.analysis-page.is-fullscreen .metric-card,
.analysis-page.is-fullscreen .analysis-cockpit,
.analysis-page.is-fullscreen .dense-toolbar,
.analysis-page.is-fullscreen .dense-selector-row,
.analysis-page.is-fullscreen .dense-summary-strip,
.analysis-page.is-fullscreen .dense-grid,
.analysis-page.is-fullscreen .matrix-head,
.analysis-page.is-fullscreen .matrix-row,
.analysis-page.is-fullscreen .comparison-pool,
.analysis-page.is-fullscreen .comparison-tray-panel,
.analysis-page.is-fullscreen .chart-card,
.analysis-page.is-fullscreen .class-analysis-panel,
.analysis-page.is-fullscreen .multi-matrix-head,
.analysis-page.is-fullscreen .multi-matrix-row,
.analysis-page.is-fullscreen .pool-row,
.analysis-page.is-fullscreen .dense-side section,
.analysis-page.is-fullscreen .compact-entity {
  background: rgba(255, 252, 242, 0.82);
  border-color: rgba(28, 39, 51, 0.14);
  box-shadow: 0 12px 28px rgba(78, 68, 48, 0.1);
}

.analysis-page.is-fullscreen .analysis-shell {
  display: none;
}

.analysis-page.is-fullscreen .hero-scope,
.analysis-page.is-fullscreen .ledger-empty,
.analysis-page.is-fullscreen .selection-note {
  background: rgba(255, 255, 255, 0.42);
}

.analysis-page.is-fullscreen .source-status-board {
  margin-top: 14px;
}

.analysis-page.is-fullscreen .source-status-card::after {
  background: radial-gradient(circle, rgba(217, 182, 111, 0.28), transparent 62%);
}

.analysis-cockpit {
  min-height: calc(100vh - 20px);
  margin-top: 0;
  border: 1px solid rgba(28, 39, 51, 0.14);
  border-radius: 16px;
  padding: 10px;
  background:
    linear-gradient(90deg, rgba(23, 33, 43, 0.04) 1px, transparent 1px) 0 0 / 18px 18px,
    linear-gradient(180deg, rgba(23, 33, 43, 0.04) 1px, transparent 1px) 0 0 / 18px 18px,
  rgba(250, 246, 235, 0.72);
  backdrop-filter: blur(20px);
  box-shadow: 0 24px 72px rgba(78, 68, 48, 0.16);
  overflow: visible;
}

.cockpit-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 0.55fr) auto;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.cockpit-header span {
  color: var(--analysis-rust);
  font-family: "Bahnschrift", "DIN Condensed", sans-serif;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.cockpit-header h2 {
  margin: 2px 0 3px;
  font-size: 24px;
  letter-spacing: -0.04em;
}

.cockpit-header p {
  margin: 0;
  color: var(--analysis-muted);
  font-size: 12px;
  line-height: 1.45;
}

.cockpit-source-line {
  min-width: 0;
  border-left: 3px solid var(--analysis-glow);
  padding-left: 10px;
}

.cockpit-source-line strong,
.cockpit-source-line em {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cockpit-source-line strong {
  font-size: 13px;
}

.cockpit-source-line em {
  color: var(--analysis-muted);
  font-size: 12px;
  font-style: normal;
}

.cockpit-exit {
  padding: 8px 12px;
  background: var(--analysis-blueprint);
  color: #fff8e8;
}

.dense-workbench {
  display: grid;
  gap: 6px;
  overflow: visible;
}

.dense-toolbar,
.dense-selector-row,
.dense-summary-strip,
.dense-grid,
.matrix-head,
.matrix-row {
  border: 1px solid rgba(28, 39, 51, 0.14);
  background: rgba(255, 252, 242, 0.74);
}

.dense-toolbar {
  min-height: 34px;
  border-radius: 10px;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.mode-tabs {
  display: flex;
  gap: 4px;
}

.mode-tab,
.swap-button,
.dense-metric-picks button {
  border: 1px solid rgba(28, 39, 51, 0.14);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.55);
  color: var(--analysis-ink);
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
}

.mode-tab {
  padding: 5px 10px;
}

.mode-tab.active,
.dense-metric-picks button.active {
  border-color: rgba(163, 91, 55, 0.38);
  background: rgba(217, 182, 111, 0.24);
}

.dense-flags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--analysis-muted);
  font-size: 12px;
}

.dense-flags label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.dense-flags input {
  accent-color: var(--analysis-rust);
}

.layout-reset-button {
  border: 1px solid rgba(28, 39, 51, 0.14);
  border-radius: 999px;
  padding: 4px 9px;
  background: rgba(28, 39, 51, 0.08);
  color: var(--analysis-blueprint);
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
}

.layout-reset-button:hover {
  background: rgba(217, 182, 111, 0.3);
}

.option-count {
  color: var(--analysis-blueprint);
  font-size: 12px;
  white-space: nowrap;
}

.dense-selector-row {
  width: min(820px, 100%);
  border-radius: 10px;
  padding: 5px;
  display: grid;
  grid-template-columns: minmax(260px, 380px) 32px minmax(260px, 380px);
  gap: 4px;
  align-items: center;
}

.dense-select-cell {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr);
  gap: 4px;
  align-items: center;
}

.dense-select-cell > span {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  color: #fff8e8;
  font-size: 12px;
  font-weight: 900;
}

.dense-select-cell.side-a > span {
  background: var(--analysis-sea);
}

.dense-select-cell.side-b > span {
  background: var(--analysis-rust);
}

.swap-button {
  height: 26px;
  padding: 0;
  color: var(--analysis-blueprint);
}

.cockpit-select {
  width: 100%;
}

.dense-summary-strip {
  border-radius: 10px;
  padding: 6px 8px;
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr) minmax(180px, 0.7fr) minmax(120px, 0.45fr);
  gap: 8px;
  align-items: center;
  font-size: 12px;
}

.dense-summary-strip span {
  color: var(--analysis-rust);
  font-weight: 900;
}

.dense-summary-strip strong,
.dense-summary-strip em,
.dense-summary-strip b {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dense-summary-strip em {
  color: var(--analysis-muted);
  font-style: normal;
}

.dense-grid {
  border-radius: 10px;
  padding: 6px;
  display: grid;
  grid-template-columns: auto minmax(680px, 1fr) auto;
  gap: 6px;
  align-items: start;
  overflow: visible;
}

.comparison-pool {
  min-width: 0;
  border: 1px solid rgba(28, 39, 51, 0.14);
  border-radius: 10px;
  padding: 7px;
}

.pool-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.pool-head h3 {
  margin: 0;
  font-size: 13px;
}

.pool-head span,
.pool-head b {
  color: var(--analysis-muted);
  font-size: 12px;
  font-weight: 800;
}

.pool-search {
  width: 100%;
  height: 32px;
  border: 1px solid rgba(28, 39, 51, 0.14);
  border-radius: 7px;
  padding: 0 8px;
  background: rgba(255, 255, 255, 0.56);
  color: var(--analysis-ink);
  font-size: 13px;
  outline: none;
}

.pool-list {
  max-height: calc(100vh - 248px);
  margin-top: 6px;
  display: grid;
  gap: 3px;
  overflow: auto;
}

.pool-row {
  width: 100%;
  min-height: 36px;
  border: 1px solid rgba(28, 39, 51, 0.11);
  border-radius: 7px;
  padding: 4px 5px;
  display: grid;
  grid-template-columns: 5px minmax(58px, 0.8fr) minmax(78px, 1fr) 54px 68px;
  gap: 5px;
  align-items: center;
  color: var(--analysis-ink);
  cursor: default;
  text-align: left;
}

.pool-row.left {
  border-color: rgba(40, 87, 106, 0.42);
  background: rgba(40, 87, 106, 0.09);
}

.pool-row.right {
  border-color: rgba(163, 91, 55, 0.42);
  background: rgba(163, 91, 55, 0.09);
}

.pool-row i {
  width: 5px;
  height: 22px;
  border-radius: 99px;
}

.pool-row strong,
.pool-row em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pool-row strong {
  font-size: 13px;
}

.pool-row em {
  color: var(--analysis-muted);
  font-size: 12px;
  font-style: normal;
}

.pool-row b {
  color: var(--analysis-blueprint);
  font-size: 12px;
  text-align: right;
}

.pool-row span {
  display: flex;
  justify-content: flex-end;
  gap: 3px;
}

.pool-row small {
  border-radius: 5px;
  padding: 2px 4px;
  background: rgba(28, 39, 51, 0.08);
  color: var(--analysis-blueprint);
  cursor: pointer;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.pool-row small:hover {
  background: rgba(217, 182, 111, 0.28);
}

.dense-center {
  min-width: 0;
  display: grid;
  gap: 6px;
  overflow: visible;
}

.comparison-tray-panel,
.chart-card,
.class-analysis-panel {
  border: 1px solid rgba(28, 39, 51, 0.14);
  border-radius: 10px;
  padding: 7px;
  background: rgba(255, 252, 242, 0.76);
}

.tray-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.tray-head h3,
.panel-title.compact h3 {
  margin: 0;
  font-size: 13px;
}

.tray-head span,
.panel-title.compact span {
  color: var(--analysis-muted);
  font-size: 12px;
  font-weight: 800;
}

.tray-head button {
  align-self: flex-start;
  border: 1px solid rgba(28, 39, 51, 0.14);
  border-radius: 7px;
  padding: 4px 8px;
  background: rgba(28, 39, 51, 0.08);
  color: var(--analysis-blueprint);
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
}

.comparison-tray {
  min-height: 98px;
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 5px;
  overflow: auto;
}

.tray-chip {
  border: 1px solid rgba(28, 39, 51, 0.14);
  border-left: 6px solid currentColor;
  border-radius: 8px;
  padding: 5px 8px;
  background: rgba(255, 255, 255, 0.58);
  color: var(--analysis-ink);
  cursor: pointer;
  display: grid;
  grid-template-columns: minmax(82px, 1fr) auto;
  gap: 1px 8px;
  text-align: left;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.tray-chip:hover {
  box-shadow: 0 10px 20px rgba(78, 68, 48, 0.13);
  transform: translateY(-1px);
}

.tray-chip strong,
.tray-chip span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tray-chip strong {
  font-size: 13px;
}

.tray-chip span {
  grid-column: 1 / -1;
  color: var(--analysis-muted);
  font-size: 11px;
}

.tray-chip em {
  color: var(--analysis-blueprint);
  font-size: 12px;
  font-style: normal;
  font-weight: 900;
}

.tray-empty {
  width: 100%;
  border: 1px dashed rgba(28, 39, 51, 0.22);
  border-radius: 8px;
  padding: 18px;
  color: var(--analysis-muted);
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 800;
}

.dense-matrix {
  min-width: 0;
  overflow: auto;
}

.multi-matrix {
  min-width: max-content;
}

.matrix-head,
.matrix-row,
.multi-matrix-head,
.multi-matrix-row {
  display: grid;
  gap: 5px;
  align-items: center;
  justify-content: start;
}

.matrix-head,
.matrix-row {
  grid-template-columns: 96px 132px 132px 74px 104px 52px;
}

.matrix-head,
.multi-matrix-head {
  position: sticky;
  top: 0;
  z-index: 1;
  border-radius: 7px 7px 0 0;
  padding: 7px 8px;
  color: var(--analysis-muted);
  font-size: 12px;
  font-weight: 900;
}

.matrix-body {
  display: grid;
  gap: 2px;
}

.matrix-row,
.multi-matrix-row {
  min-height: 36px;
  padding: 6px 8px;
  font-size: 13px;
}

.matrix-row strong,
.multi-matrix-row strong {
  font-size: 13px;
}

.multi-matrix-head,
.multi-matrix-row {
  border: 1px solid rgba(28, 39, 51, 0.14);
  background: rgba(255, 252, 242, 0.72);
}

.multi-matrix-row span {
  border-radius: 5px;
  padding: 2px 5px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.multi-matrix-row span.peak {
  background: rgba(40, 87, 106, 0.12);
  color: var(--analysis-sea);
  font-weight: 900;
}

.multi-matrix-row span.low {
  background: rgba(163, 91, 55, 0.1);
  color: var(--analysis-rust);
}

.multi-matrix-row em {
  overflow: hidden;
  color: var(--analysis-muted);
  font-style: normal;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.matrix-head span:nth-child(2),
.matrix-head span:nth-child(3),
.matrix-head span:nth-child(4),
.matrix-head span:nth-child(5),
.matrix-row span:nth-child(2),
.matrix-row span:nth-child(3),
.matrix-row span:nth-child(4),
.matrix-row .mini-ratio {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.matrix-row .delta-cell {
  border-radius: 5px;
  padding: 2px 5px;
  background: rgba(28, 39, 51, 0.06);
  font-weight: 900;
}

.matrix-row em {
  font-style: normal;
  font-weight: 900;
}

.matrix-row.leader-a .delta-cell {
  color: var(--analysis-sea);
  background: rgba(40, 87, 106, 0.1);
}

.matrix-row.leader-b .delta-cell {
  color: var(--analysis-rust);
  background: rgba(163, 91, 55, 0.1);
}

.matrix-row.leader-even .delta-cell {
  color: var(--analysis-muted);
}

.matrix-row.leader-a em {
  color: var(--analysis-sea);
}

.matrix-row.leader-b em {
  color: var(--analysis-rust);
}

.matrix-row.leader-even em {
  color: var(--analysis-muted);
}

.mini-ratio {
  position: relative;
  display: flex;
  height: 16px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(28, 39, 51, 0.08);
}

.mini-ratio small {
  position: absolute;
  inset: 0 6px 0 auto;
  display: inline-flex;
  align-items: center;
  color: #17212b;
  font-size: 10px;
  font-weight: 900;
  line-height: 1;
  mix-blend-mode: multiply;
}

.mini-ratio i,
.mini-ratio b {
  display: block;
  height: 100%;
}

.mini-ratio i {
  background: #28576a;
}

.mini-ratio b {
  background: #a35b37;
}

.chart-wall {
  display: grid;
  grid-template-columns: repeat(2, max-content);
  gap: 6px;
  align-items: start;
  overflow: visible;
}

.chart-card,
.class-analysis-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 5px;
}

.panel-title.compact {
  min-height: 28px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.class-analysis-list {
  display: grid;
  gap: 6px;
  overflow: auto;
}

.class-analysis-group {
  border: 1px solid rgba(28, 39, 51, 0.13);
  border-radius: 8px;
  padding: 7px;
  background: rgba(255, 255, 255, 0.48);
}

.class-analysis-head,
.class-analysis-row {
  display: grid;
  grid-template-columns: minmax(92px, 1fr) 120px 120px;
  gap: 6px;
  align-items: center;
}

.class-analysis-head {
  margin-bottom: 5px;
  color: var(--analysis-blueprint);
  font-size: 13px;
  font-weight: 900;
}

.class-analysis-head span {
  color: var(--analysis-muted);
  text-align: right;
}

.class-analysis-row {
  min-height: 26px;
  border-top: 1px solid rgba(28, 39, 51, 0.08);
  color: var(--analysis-muted);
  font-size: 12px;
}

.class-analysis-row b,
.class-analysis-row em {
  color: var(--analysis-ink);
  font-style: normal;
  font-weight: 900;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.dense-side {
  display: grid;
  gap: 6px;
}

.dense-side section,
.compact-entity {
  border: 1px solid rgba(28, 39, 51, 0.13);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
}

.dense-side section {
  padding: 7px;
}

.dense-side h3 {
  margin: 0 0 6px;
  font-size: 13px;
}

.dense-side p {
  margin: 4px 0;
  color: var(--analysis-muted);
  font-size: 12px;
}

.compact-entity {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr);
  gap: 1px 5px;
  padding: 6px;
  margin-top: 4px;
}

.compact-entity > span {
  grid-row: span 3;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  color: #fff8e8;
  font-size: 11px;
  font-weight: 900;
}

.compact-entity.side-a > span {
  background: var(--analysis-sea);
}

.compact-entity.side-b > span {
  background: var(--analysis-rust);
}

.compact-entity strong,
.compact-entity em,
.compact-entity small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compact-entity em,
.compact-entity small {
  color: var(--analysis-muted);
  font-size: 12px;
  font-style: normal;
}

.dense-metric-picks {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.dense-metric-picks button {
  padding: 4px 6px;
}

.analysis-page.is-fullscreen :deep(.cockpit-select .el-select__wrapper),
.analysis-page.is-fullscreen :deep(.cockpit-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.54);
  box-shadow: inset 0 0 0 1px rgba(28, 39, 51, 0.14);
}

.analysis-page.is-fullscreen :deep(.cockpit-select .el-select__placeholder),
.analysis-page.is-fullscreen :deep(.cockpit-select .el-input__inner) {
  color: var(--analysis-muted);
}

.analysis-page.is-fullscreen .cockpit-header span {
  font-size: 24px;
}

.analysis-page.is-fullscreen .cockpit-header h2 {
  font-size: 48px;
}

.analysis-page.is-fullscreen .cockpit-header p,
.analysis-page.is-fullscreen .cockpit-source-line strong,
.analysis-page.is-fullscreen .cockpit-source-line em,
.analysis-page.is-fullscreen .cockpit-exit,
.analysis-page.is-fullscreen .mode-tab,
.analysis-page.is-fullscreen .swap-button,
.analysis-page.is-fullscreen .dense-flags,
.analysis-page.is-fullscreen .layout-reset-button,
.analysis-page.is-fullscreen .option-count,
.analysis-page.is-fullscreen .dense-summary-strip,
.analysis-page.is-fullscreen .pool-head span,
.analysis-page.is-fullscreen .pool-head b,
.analysis-page.is-fullscreen .tray-head span,
.analysis-page.is-fullscreen .tray-head button,
.analysis-page.is-fullscreen .panel-title.compact span,
.analysis-page.is-fullscreen .tray-empty,
.analysis-page.is-fullscreen .dense-side p,
.analysis-page.is-fullscreen .compact-entity em,
.analysis-page.is-fullscreen .compact-entity small {
  font-size: 24px;
}

.analysis-page.is-fullscreen .dense-side h3,
.analysis-page.is-fullscreen .pool-head h3,
.analysis-page.is-fullscreen .tray-head h3,
.analysis-page.is-fullscreen .panel-title.compact h3,
.analysis-page.is-fullscreen .class-analysis-head,
.analysis-page.is-fullscreen .matrix-head {
  font-size: 26px;
}

.analysis-page.is-fullscreen .pool-search,
.analysis-page.is-fullscreen .pool-row strong,
.analysis-page.is-fullscreen .pool-row em,
.analysis-page.is-fullscreen .pool-row b,
.analysis-page.is-fullscreen .matrix-row,
.analysis-page.is-fullscreen .matrix-row strong,
.analysis-page.is-fullscreen .multi-matrix-head,
.analysis-page.is-fullscreen .multi-matrix-row,
.analysis-page.is-fullscreen .multi-matrix-row strong,
.analysis-page.is-fullscreen .tray-chip strong,
.analysis-page.is-fullscreen .tray-chip em,
.analysis-page.is-fullscreen .class-analysis-row,
.analysis-page.is-fullscreen .dense-metric-picks button {
  font-size: 26px;
}

.analysis-page.is-fullscreen .pool-row small,
.analysis-page.is-fullscreen .tray-chip span,
.analysis-page.is-fullscreen .mini-ratio small {
  font-size: 22px;
}

.analysis-page.is-fullscreen :deep(.cockpit-select .el-select__placeholder),
.analysis-page.is-fullscreen :deep(.cockpit-select .el-input__inner),
.analysis-page.is-fullscreen :deep(.cockpit-select .el-select__selected-item) {
  font-size: 26px;
}

.analysis-page.is-fullscreen :deep(.cockpit-select .el-select__wrapper),
.analysis-page.is-fullscreen :deep(.cockpit-select .el-input__wrapper) {
  min-height: 52px;
}

.analysis-page.is-fullscreen .cockpit-exit {
  padding: 16px 24px;
}

.analysis-page.is-fullscreen .mode-tab {
  padding: 10px 20px;
}

.analysis-page.is-fullscreen .dense-selector-row {
  width: min(1320px, 100%);
  grid-template-columns: minmax(360px, 620px) 56px minmax(360px, 620px);
}

.analysis-page.is-fullscreen .dense-select-cell {
  grid-template-columns: 48px minmax(0, 1fr);
}

.analysis-page.is-fullscreen .dense-select-cell > span {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  font-size: 24px;
}

.analysis-page.is-fullscreen .swap-button {
  height: 52px;
}

.analysis-page.is-fullscreen .dense-grid {
  grid-template-columns: auto minmax(1020px, 1fr) auto;
  overflow: visible;
}

.analysis-page.is-fullscreen .pool-search {
  height: 56px;
}

.analysis-page.is-fullscreen .pool-row {
  min-height: 68px;
  grid-template-columns: 8px minmax(96px, 0.8fr) minmax(120px, 1fr) 92px 128px;
  gap: 8px;
}

.analysis-page.is-fullscreen .pool-row i {
  width: 8px;
  height: 48px;
}

.analysis-page.is-fullscreen .pool-row small {
  padding: 5px 8px;
}

.analysis-page.is-fullscreen .matrix-head,
.analysis-page.is-fullscreen .matrix-row {
  grid-template-columns: 160px 210px 210px 136px 180px 94px;
  gap: 8px;
}

.analysis-page.is-fullscreen .multi-matrix-head,
.analysis-page.is-fullscreen .multi-matrix-row {
  gap: 8px;
}

.analysis-page.is-fullscreen .matrix-head {
  padding: 12px 14px;
}

.analysis-page.is-fullscreen .matrix-row {
  min-height: 68px;
  padding: 10px 14px;
}

.analysis-page.is-fullscreen .mini-ratio {
  height: 30px;
}

.analysis-page.is-fullscreen .compact-entity {
  grid-template-columns: 44px minmax(0, 1fr);
  padding: 12px;
}

.analysis-page.is-fullscreen .compact-entity > span {
  width: 44px;
  height: 44px;
  font-size: 22px;
}

.analysis-page.is-fullscreen .dense-metric-picks button {
  padding: 8px 12px;
}

.analysis-page.is-fullscreen .comparison-tray {
  min-height: 116px;
}

.analysis-page.is-fullscreen .tray-chip {
  grid-template-columns: minmax(140px, 1fr) auto;
  padding: 8px 10px;
}

.analysis-page.is-fullscreen .chart-wall {
  grid-template-columns: repeat(2, max-content);
}

.analysis-page.is-fullscreen .class-analysis-head,
.analysis-page.is-fullscreen .class-analysis-row {
  grid-template-columns: minmax(150px, 1fr) 180px 180px;
}
.source-status-board {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.source-status-card {
  position: relative;
  min-height: 92px;
  border: 1px solid rgba(23, 35, 29, 0.13);
  border-radius: 22px;
  padding: 16px 18px 16px 20px;
  background:
    linear-gradient(90deg, rgba(23, 35, 29, 0.05) 1px, transparent 1px) 0 0 / 22px 22px,
    rgba(255, 252, 241, 0.7);
  box-shadow: 0 18px 44px rgba(60, 54, 38, 0.11);
  overflow: hidden;
}

.source-status-card::before {
  content: "";
  position: absolute;
  inset: 12px auto 12px 0;
  width: 5px;
  border-radius: 0 999px 999px 0;
  background: var(--analysis-rust);
  opacity: 0.38;
}

.source-status-card::after {
  content: "";
  position: absolute;
  right: -32px;
  top: -48px;
  width: 120px;
  height: 120px;
  border: 1px solid rgba(23, 35, 29, 0.12);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(217, 255, 106, 0.32), transparent 62%);
  transition: transform 0.22s ease;
}

.source-status-card.schedule::before {
  background: var(--analysis-sea);
}

.source-status-card.ready::before {
  opacity: 1;
}

.source-status-card.muted {
  opacity: 0.76;
}

.source-status-card:hover::after {
  transform: scale(1.08) rotate(10deg);
}

.source-status-card span {
  color: var(--analysis-rust);
  font-family: "Bahnschrift", "DIN Condensed", sans-serif;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.source-status-card strong,
.source-status-card em {
  position: relative;
  z-index: 1;
  display: block;
}

.source-status-card strong {
  margin-top: 8px;
  color: var(--analysis-ink);
  font-size: 20px;
}

.source-status-card em {
  margin-top: 6px;
  color: var(--analysis-muted);
  font-size: 13px;
  font-style: normal;
  line-height: 1.45;
}

.analysis-shell {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 18px;
  margin-top: 18px;
}

.selection-deck,
.result-stage {
  border: 1px solid var(--analysis-line);
  border-radius: 26px;
  background: var(--analysis-panel);
  box-shadow: 0 20px 54px rgba(60, 54, 38, 0.13);
  backdrop-filter: blur(16px);
}

.selection-deck {
  position: relative;
  padding: 16px;
  align-self: start;
}

.deck-card {
  border: 1px solid rgba(23, 35, 29, 0.14);
  border-radius: 20px;
  padding: 16px;
  margin-bottom: 12px;
  background: rgba(255, 252, 241, 0.72);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.deck-card:hover {
  border-color: rgba(31, 125, 112, 0.34);
  box-shadow: 0 16px 36px rgba(60, 54, 38, 0.12);
  transform: translateY(-2px);
}

.deck-heading {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}

.deck-heading h3,
.panel-title h3,
.empty-console h2,
.battle-banner h2 {
  margin: 0;
}

.deck-heading p {
  margin: 4px 0 0;
  font-size: 13px;
}

.step-mark {
  flex: 0 0 auto;
  height: 28px;
  border-radius: 999px;
  padding: 0 10px;
  background: var(--analysis-blueprint);
  color: #f8f3dc;
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 800;
}

.step-mark.optional {
  background: rgba(23, 35, 29, 0.1);
  color: var(--analysis-blueprint);
}

.deck-select {
  width: 100%;
}

.option-line {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.25;
}

.option-line span {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.source-ledger {
  margin-top: 12px;
  border: 1px solid rgba(23, 35, 29, 0.1);
  border-radius: 16px;
  padding: 10px;
  background:
    linear-gradient(90deg, rgba(23, 35, 29, 0.04) 1px, transparent 1px) 0 0 / 18px 18px,
    rgba(255, 255, 255, 0.34);
}

.ledger-head {
  min-height: 26px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--analysis-muted);
  font-size: 12px;
  font-weight: 800;
}

.ledger-head button {
  border: 0;
  border-radius: 999px;
  padding: 3px 8px;
  background: rgba(23, 35, 29, 0.08);
  color: var(--analysis-blueprint);
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
  transition: transform 0.16s ease, background 0.16s ease;
}

.ledger-head button:hover {
  background: rgba(217, 255, 106, 0.35);
  transform: translateY(-1px);
}

.ledger-list {
  display: grid;
  gap: 7px;
  margin-top: 8px;
}

.ledger-item {
  position: relative;
  width: 100%;
  border: 1px solid rgba(23, 35, 29, 0.11);
  border-radius: 13px;
  padding: 9px 10px 9px 12px;
  background: rgba(255, 252, 241, 0.66);
  color: var(--analysis-ink);
  cursor: pointer;
  display: grid;
  gap: 3px;
  text-align: left;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, box-shadow 0.16s ease;
  overflow: hidden;
}

.ledger-item::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--analysis-rust);
  opacity: 0;
  transition: opacity 0.16s ease;
}

.ledger-item.optional::before {
  background: var(--analysis-sea);
}

.ledger-item:hover,
.ledger-item.active {
  border-color: rgba(23, 35, 29, 0.28);
  background: rgba(255, 252, 241, 0.94);
  box-shadow: 0 10px 24px rgba(60, 54, 38, 0.1);
  transform: translateX(2px);
}

.ledger-list:has(.ledger-item.active) .ledger-item:not(.active) {
  opacity: 0.58;
  filter: saturate(0.72);
}

.ledger-list:has(.ledger-item.active) .ledger-item:not(.active):hover {
  opacity: 0.86;
  filter: none;
}

.ledger-item.active {
  border-color: rgba(163, 91, 55, 0.62);
  background:
    linear-gradient(90deg, rgba(217, 182, 111, 0.26), transparent 54%),
    rgba(255, 252, 241, 0.98);
  box-shadow: 0 14px 30px rgba(95, 71, 36, 0.18);
}

.ledger-item.optional.active {
  border-color: rgba(40, 87, 106, 0.62);
  background:
    linear-gradient(90deg, rgba(40, 87, 106, 0.16), transparent 54%),
    rgba(255, 252, 241, 0.98);
}

.ledger-item.active::after {
  content: "已选";
  position: absolute;
  top: 7px;
  right: 8px;
  border-radius: 999px;
  padding: 2px 6px;
  background: var(--analysis-rust);
  color: #fff8e8;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.ledger-item.optional.active::after {
  background: var(--analysis-sea);
}

.ledger-item.active::before {
  opacity: 1;
}

.ledger-item strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.ledger-item span,
.ledger-empty {
  color: var(--analysis-muted);
  font-size: 12px;
}

.ledger-empty {
  margin-top: 8px;
  border-radius: 12px;
  padding: 10px;
  background: rgba(23, 35, 29, 0.05);
  line-height: 1.6;
}

.scan-button {
  position: relative;
  width: 100%;
  height: 54px;
  border: 0;
  border-radius: 18px;
  margin: 6px 0 12px;
  background: var(--analysis-ink);
  color: #f8f3dc;
  cursor: pointer;
  font-size: 16px;
  font-weight: 900;
  letter-spacing: 0.08em;
  overflow: hidden;
}

.scan-button i {
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 0 35%, rgba(217, 255, 106, 0.44) 45%, transparent 56% 100%);
  transform: translateX(-100%);
}

.scan-button:not(:disabled):hover i {
  animation: scanLine 0.9s ease;
}

.scan-button:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.selection-note {
  border-radius: 18px;
  padding: 12px;
  background: rgba(217, 255, 106, 0.18);
  display: grid;
  grid-template-columns: 10px 1fr;
  gap: 10px;
}

.selection-note p {
  margin: 0;
  color: var(--analysis-muted);
  font-size: 13px;
  line-height: 1.7;
}

.note-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 6px;
  background: var(--analysis-glow);
  box-shadow: 0 0 0 6px rgba(217, 255, 106, 0.16);
}

.result-stage {
  min-height: 620px;
  padding: 18px;
}

.empty-console {
  min-height: 560px;
  border: 1px dashed rgba(23, 35, 29, 0.2);
  border-radius: 24px;
  display: grid;
  place-items: center;
  align-content: center;
  text-align: center;
  background:
    radial-gradient(circle, rgba(23, 35, 29, 0.08) 1px, transparent 1px) 0 0 / 26px 26px,
    rgba(255, 252, 241, 0.45);
}

.radar {
  position: relative;
  width: 128px;
  height: 128px;
  border: 1px solid rgba(23, 35, 29, 0.18);
  border-radius: 50%;
  margin-bottom: 18px;
  background: radial-gradient(circle, transparent 0 28%, rgba(31, 125, 112, 0.12) 29% 30%, transparent 31% 100%);
  overflow: hidden;
}

.radar span {
  position: absolute;
  inset: 50% 0 0 50%;
  transform-origin: 0 0;
  background: linear-gradient(60deg, rgba(217, 255, 106, 0.58), transparent 65%);
  animation: radarSweep 3.6s linear infinite;
}

.empty-scan-button {
  border: 0;
  border-radius: 999px;
  padding: 12px 18px;
  margin-top: 8px;
  background: var(--analysis-blueprint);
  color: #f8f3dc;
  cursor: pointer;
  font-weight: 900;
  letter-spacing: 0.04em;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.empty-scan-button:not(:disabled):hover {
  box-shadow: 0 12px 28px rgba(33, 63, 54, 0.22);
  transform: translateY(-2px);
}

.empty-scan-button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.battle-banner,
.review-panel,
.metric-card {
  border: 1px solid rgba(23, 35, 29, 0.13);
  background: rgba(255, 252, 241, 0.72);
  box-shadow: 0 16px 40px rgba(60, 54, 38, 0.1);
}

.battle-banner {
  border-radius: 24px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  gap: 18px;
}

.battle-banner span {
  color: var(--analysis-rust);
  font-weight: 900;
}

.battle-banner h2 {
  margin-top: 6px;
  font-size: 28px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 14px 0;
}

.metric-card {
  position: relative;
  min-height: 126px;
  border-radius: 22px;
  padding: 18px;
  overflow: hidden;
}

.metric-card::after {
  content: "";
  position: absolute;
  right: -28px;
  bottom: -42px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(23, 35, 29, 0.07);
}

.metric-card span,
.metric-card small {
  display: block;
  color: var(--analysis-muted);
}

.metric-card strong {
  display: block;
  margin: 10px 0;
  font-family: "Bahnschrift", "DIN Condensed", sans-serif;
  font-size: 34px;
}

.metric-card.signal {
  background: linear-gradient(135deg, rgba(217, 255, 106, 0.34), rgba(255, 252, 241, 0.74));
}

.metric-card.impact {
  background: linear-gradient(135deg, rgba(185, 85, 48, 0.16), rgba(255, 252, 241, 0.74));
}

.metric-card.damage {
  background: linear-gradient(135deg, rgba(31, 125, 112, 0.15), rgba(255, 252, 241, 0.74));
}

.metric-card.heal {
  background: linear-gradient(135deg, rgba(232, 224, 205, 0.9), rgba(255, 252, 241, 0.74));
}

.review-grid,
.detail-grid {
  display: grid;
  gap: 14px;
}

.review-grid {
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
}

.detail-grid {
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  margin-top: 14px;
}

.review-panel {
  border-radius: 24px;
  padding: 18px;
}

.panel-title,
.team-card-head,
.team-metrics,
.rank-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-title {
  margin-bottom: 14px;
}

.panel-title > strong {
  color: var(--analysis-muted);
}

.team-stack {
  display: grid;
  gap: 12px;
}

.team-card {
  border: 1px solid rgba(23, 35, 29, 0.1);
  border-radius: 18px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.38);
}

.team-card-head span,
.team-metrics,
.squad-strip {
  color: var(--analysis-muted);
  font-size: 12px;
}

.team-card-head em {
  font-family: "Bahnschrift", "DIN Condensed", sans-serif;
  font-size: 28px;
  font-style: normal;
  font-weight: 900;
}

.team-bars {
  height: 9px;
  border-radius: 999px;
  margin: 12px 0;
  background: rgba(23, 35, 29, 0.1);
  overflow: hidden;
}

.team-bars span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--analysis-sea), var(--analysis-glow));
}

.squad-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.squad-strip span {
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(23, 35, 29, 0.06);
}

.rank-tabs {
  margin-top: -6px;
}

.rank-list {
  display: grid;
  gap: 8px;
}

.rank-row {
  min-height: 42px;
  border-radius: 14px;
  padding: 8px;
  background: rgba(23, 35, 29, 0.05);
}

.rank-index {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--analysis-ink);
  color: #f8f3dc;
  display: inline-grid;
  place-items: center;
  font-weight: 900;
}

.class-pill,
.class-card {
  border: 1px solid currentColor;
  background: var(--el-fill-color-light);
}

.class-pill {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 800;
}

.rank-row strong {
  margin-right: auto;
}

.rank-row em {
  color: var(--analysis-blueprint);
  font-style: normal;
  font-weight: 900;
}

.class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
  gap: 10px;
}

.class-card {
  border-radius: 18px;
  padding: 12px;
  color: var(--el-text-color-regular);
  display: grid;
  gap: 4px;
}

.class-card strong {
  font-size: 16px;
}

.class-card span,
.class-card em {
  font-size: 12px;
  font-style: normal;
}

.exception-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.exception-columns h4 {
  margin: 0 0 10px;
}

.exception-list {
  max-height: 220px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.exception-list span,
.exception-list em {
  border-radius: 12px;
  padding: 8px 10px;
  background: rgba(23, 35, 29, 0.06);
  color: var(--analysis-muted);
  font-style: normal;
}

@keyframes scanLine {
  to {
    transform: translateX(100%);
  }
}

@keyframes radarSweep {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1180px) {
  .source-status-board,
  .analysis-shell,
  .review-grid,
  .detail-grid,
  .dense-grid {
    grid-template-columns: 1fr;
  }

  .dense-summary-strip,
  .matrix-head,
  .matrix-row {
    grid-template-columns: 92px 118px 118px 72px 96px 52px;
  }

  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .analysis-page {
    overflow: visible;
  }

  .analysis-hero,
  .battle-banner,
  .exception-columns {
    flex-direction: column;
    grid-template-columns: 1fr;
  }

  .analysis-hero {
    padding: 22px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .cockpit-header,
  .dense-toolbar,
  .dense-summary-strip {
    flex-direction: column;
    align-items: flex-start;
  }

  .dense-selector-row {
    grid-template-columns: 1fr;
  }

  .matrix-head,
  .matrix-row {
    grid-template-columns: 82px 96px 96px 78px;
  }

  .matrix-head span:nth-child(5),
  .matrix-head span:nth-child(6),
  .matrix-row .mini-ratio,
  .matrix-row em {
    display: none;
  }
}
</style>
