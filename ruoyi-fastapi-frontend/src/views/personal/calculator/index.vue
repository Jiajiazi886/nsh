<template>
  <div v-if="isDefenseCalculator" class="app-container defense-page">
    <section class="page-header">
      <div><h1>坦度计算器</h1><p>基于 PVP 计算器 4.1.1 的防御减免、会心率与伤害期望公式。</p></div>
      <div class="header-actions">
        <el-button :icon="Edit" @click="openCustomAttackPanelDialog">攻击方面板设置</el-button>
        <el-button :icon="Picture" @click="openRecognitionDialog">面板识别</el-button>
        <el-select v-model="selectedPanelKey" class="panel-select" placeholder="选择进攻方面板">
          <el-option-group label="我的攻击方面板">
            <el-option v-for="panel in personalAttackPanels" :key="`personal-${panel.panelId}`" :label="panel.panelName" :value="panelKey('personal', panel.panelId)" />
          </el-option-group>
          <el-option-group label="系统参考面板">
            <el-option v-for="panel in systemAttackPanels" :key="`system-${panel.panelId}`" :label="panel.panelName" :value="panelKey('system', panel.panelId)" />
          </el-option-group>
        </el-select>
      </div>
    </section>

    <section class="profession-bar">
      <div class="profession-field">
        <span>防守方职业</span>
        <el-select v-model="professionId" placeholder="选择职业" filterable @change="changeProfession">
          <el-option v-for="item in professionBonuses" :key="item.professionId" :label="item.professionName" :value="item.professionId" />
        </el-select>
      </div>
      <div class="profession-field">
        <span>内功防御加成</span>
        <el-input-number v-model="professionDraft.defenseBonusPct" :min="0" :max="1000" :step="1" :precision="2" controls-position="right"><template #suffix>%</template></el-input-number>
      </div>
      <div class="profession-field">
        <span>内功气血加成</span>
        <el-input-number v-model="professionDraft.hpBonusPct" :min="0" :max="1000" :step="1" :precision="2" controls-position="right"><template #suffix>%</template></el-input-number>
      </div>
      <div class="profession-actions">
        <el-tag :type="professionIsCustomized ? 'warning' : 'info'">{{ professionIsCustomized ? '个人设置' : '管理员默认' }}</el-tag>
        <el-button type="primary" @click="saveProfessionOverride">保存个人设置</el-button>
        <el-button :icon="RefreshLeft" @click="restoreProfessionDefault">恢复默认</el-button>
      </div>
    </section>

    <el-dialog v-model="recognitionDialogVisible" title="防守面板识别" width="560px" append-to-body destroy-on-close>
      <el-upload
        drag
        accept="image/png,image/jpeg,image/webp"
        :auto-upload="false"
        :limit="1"
        :on-change="handleRecognitionFileChange"
        :on-remove="clearRecognitionFile"
        :on-exceed="handleRecognitionExceed"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="el-upload__text">上传逆水寒角色防御属性面板截图</div>
      </el-upload>
      <div v-if="recognizing" class="recognition-progress"><el-icon class="is-loading"><Loading /></el-icon> 正在识别并回填防守面板</div>
      <el-alert v-if="recognitionError" class="recognition-alert" type="error" :closable="false" :title="recognitionError" />
      <el-alert v-if="defenseRecognition.success" class="recognition-alert" type="success" :closable="false" title="识别成功，已回填防守方面板" />
      <template #footer>
        <el-button @click="recognitionDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="customAttackPanelDialogVisible" title="攻击方面板设置" width="820px" append-to-body destroy-on-close>
      <p class="attack-panel-description">管理员提供系统预设供所有用户直接使用；个人模板仅属于当前账号，名称按创建顺序自动生成。</p>
      <el-tabs v-model="attackPanelTab" class="attack-panel-tabs">
        <el-tab-pane label="系统预设" name="system">
          <div class="template-toolbar">
            <el-select v-model="selectedSystemPanelId" class="template-select" placeholder="选择系统预设">
              <el-option v-for="panel in systemAttackPanels" :key="panel.panelId" :label="panel.panelName" :value="panel.panelId" />
            </el-select>
            <el-button :icon="Download" @click="openAttackJsonDialog('export-system')">导出 JSON</el-button>
            <el-button type="primary" :icon="Check" @click="useSystemPreset">使用此预设</el-button>
          </div>
          <el-form :model="selectedSystemPanel" label-width="108px" class="attack-panel-form readonly-panel" @submit.prevent>
            <el-row :gutter="16">
              <el-col :span="24"><el-form-item label="面板名称"><el-input :model-value="selectedSystemPanel.panelName" disabled /></el-form-item></el-col>
              <el-col v-for="field in attackPanelCoreFields" :key="field.key" :span="8"><el-form-item :label="field.label"><el-input-number :model-value="selectedSystemPanel[field.key]" disabled style="width: 100%" /></el-form-item></el-col>
              <el-col :span="24"><el-collapse class="attack-panel-advanced"><el-collapse-item title="额外伤害乘区" name="system-advanced"><el-row :gutter="16"><el-col v-for="field in attackPanelAdvancedFields" :key="field.key" :span="8"><el-form-item :label="field.label"><el-input-number :model-value="selectedSystemPanel[field.key]" disabled :precision="3" style="width: 100%"><template #suffix>%</template></el-input-number></el-form-item></el-col></el-row></el-collapse-item></el-collapse></el-col>
            </el-row>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="我的模板" name="personal">
          <div class="template-toolbar">
            <el-select v-model="editingPersonalPanelId" class="template-select" placeholder="选择我的模板" @change="selectPersonalPanel">
              <el-option v-for="panel in personalAttackPanels" :key="panel.panelId" :label="panel.panelName" :value="panel.panelId" />
            </el-select>
            <el-button type="primary" plain :icon="Plus" :loading="templateSaving" @click="addPersonalPanel">新增模板</el-button>
            <el-button v-if="editingPersonalPanelId" type="danger" plain :icon="Delete" :loading="templateSaving" @click="removePersonalPanel">删除模板</el-button>
          </div>
          <div class="json-toolbar">
            <el-button :icon="Upload" :disabled="!editingPersonalPanelId" @click="openAttackJsonDialog('import-personal')">导入 JSON</el-button>
            <el-button :icon="Download" :disabled="!editingPersonalPanelId" @click="openAttackJsonDialog('export-personal')">导出 JSON</el-button>
            <el-button :icon="DocumentCopy" @click="openAttackJsonDialog('example')">示例 JSON</el-button>
          </div>
          <el-empty v-if="!editingPersonalPanelId" description="还没有个人攻击方面板，请新增一套模板" :image-size="90" />
          <el-form v-else :model="personalPanelDraft" label-width="108px" class="attack-panel-form" @submit.prevent>
            <el-row :gutter="16">
              <el-col :span="24"><el-form-item label="面板名称"><el-input :model-value="personalPanelDraft.panelName" disabled /></el-form-item></el-col>
              <el-col v-for="field in attackPanelCoreFields" :key="field.key" :span="8">
                <el-form-item :label="field.label"><el-input-number v-model="personalPanelDraft[field.key]" :min="0" :step="field.step || 1" :precision="field.precision || 0" controls-position="right" style="width: 100%"><template v-if="field.suffix" #suffix>{{ field.suffix }}</template></el-input-number></el-form-item>
              </el-col>
              <el-col :span="24">
                <el-collapse class="attack-panel-advanced"><el-collapse-item title="额外伤害乘区" name="advanced"><el-row :gutter="16"><el-col v-for="field in attackPanelAdvancedFields" :key="field.key" :span="8"><el-form-item :label="field.label"><el-input-number v-model="personalPanelDraft[field.key]" :min="0" :step="0.01" :precision="3" controls-position="right" style="width: 100%"><template #suffix>%</template></el-input-number></el-form-item></el-col></el-row></el-collapse-item></el-collapse>
              </el-col>
            </el-row>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="customAttackPanelDialogVisible = false">取消</el-button>
        <el-button v-if="attackPanelTab === 'personal'" type="primary" :disabled="!editingPersonalPanelId" :loading="templateSaving" @click="savePersonalPanel">保存并使用</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attackJsonDialog.visible" :title="attackJsonDialog.title" width="720px" append-to-body>
      <p class="json-help">{{ attackJsonDialog.mode === 'import-personal' ? '粘贴后只覆盖当前模板草稿，点击“保存并使用”后才会写入。' : 'JSON 百分比字段按当前面板值原样显示。' }}</p>
      <el-input v-model="attackJsonDialog.text" type="textarea" :rows="20" resize="vertical" :readonly="attackJsonDialog.mode !== 'import-personal'" spellcheck="false" />
      <template #footer>
        <el-button @click="attackJsonDialog.visible = false">关闭</el-button>
        <el-button v-if="attackJsonDialog.mode !== 'import-personal'" v-copyText="attackJsonDialog.text" v-copyText:callback="copyAttackJsonSuccess" :icon="DocumentCopy">复制</el-button>
        <el-button v-else type="primary" :icon="Check" @click="applyPersonalJsonImport">校验并回填</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="internalPowerDialogVisible" title="内功防御提升" width="1180px" append-to-body class="internal-power-picker-dialog">
      <div class="power-dialog-toolbar">
        <div>
          <strong>选择自己的内功</strong>
          <span>最多选择 6 本，攻击词条不计入坦度收益。</span>
        </div>
        <div class="power-picker-actions">
          <el-input v-model="internalPowerKeyword" clearable placeholder="搜索内功或词条" class="power-search" />
          <el-tag type="primary">已选 {{ selectedInternalPowerIds.length }} / 6</el-tag>
          <el-button v-if="selectedInternalPowerIds.length" plain @click="clearInternalPowerSelection">清空选择</el-button>
        </div>
      </div>
      <el-empty v-if="!internalPowers.length" description="内功管理中还没有已保存内功" :image-size="80" />
      <el-empty v-else-if="!filteredInternalPowers.length" description="没有匹配的内功或词条" :image-size="80" />
      <div v-else class="internal-power-picker-grid">
        <button
          v-for="power in filteredInternalPowers"
          :key="power.powerId"
          type="button"
          class="internal-power-picker-card"
          :class="{ selected: isInternalPowerSelected(power.powerId) }"
          :aria-pressed="isInternalPowerSelected(power.powerId)"
          @click="toggleInternalPower(power.powerId)"
        >
          <span class="power-selected-mark">{{ isInternalPowerSelected(power.powerId) ? '已选择' : '选择' }}</span>
          <div class="picker-power-media" :class="{ empty: !resolveInternalPowerImage(power) }">
            <img v-if="resolveInternalPowerImage(power)" :src="resolveInternalPowerImage(power)" :alt="`${power.name}图片`" />
            <span v-else>内功图片</span>
          </div>
          <div class="picker-power-heading">
            <strong>{{ power.name }}</strong>
            <span>{{ formatInternalPowerElements(power.elements) }}</span>
          </div>
          <div class="picker-entry-list">
            <span
              v-for="(entry, entryIndex) in power.entries"
              :key="entry.id || `${power.powerId}-${entryIndex}`"
              :class="{ ignored: isIgnoredInternalPowerEntry(entry) }"
              :title="getInternalPowerEntryTitle(entry)"
            >{{ formatInternalPowerEntryWithGain(entry) }}</span>
            <span v-if="!power.entries.length" class="empty-entry">暂无词条</span>
          </div>
          <div class="picker-power-benefit">
            <span>防御 +{{ formatNumber(getInternalPowerUpgrade(power.powerId).defense) }}</span>
            <span>气血 +{{ formatNumber(getInternalPowerUpgrade(power.powerId).hp) }}</span>
            <span>抗会心 +{{ formatNumber(getInternalPowerUpgrade(power.powerId).critResist) }}</span>
            <span>流派抵御 +{{ Number(getInternalPowerUpgrade(power.powerId).resistPct || 0).toFixed(2) }}%</span>
          </div>
          <div class="picker-power-gain">独立坦度 +{{ formatPercent(getInternalPowerUpgrade(power.powerId).gainPct / 100) }}</div>
        </button>
      </div>
      <div v-if="selectedInternalPowerIds.length" class="power-total">
        <span>共 {{ internalPowerUpgrade.powers.length }} 本</span>
        <span>实际防御 <b>+{{ formatNumber(internalPowerUpgrade.total.defense) }}</b></span>
        <span>实际气血 <b>+{{ formatNumber(internalPowerUpgrade.total.hp) }}</b></span>
        <span>会心抵抗 <b>+{{ formatNumber(internalPowerUpgrade.total.critResist) }}</b></span>
        <span>流派抵御 <b>+{{ Number(internalPowerUpgrade.total.resistPct || 0).toFixed(2) }}%</b></span>
        <strong>总坦度 +{{ formatPercent(internalPowerUpgrade.gainPct / 100) }}</strong>
      </div>
      <template #footer><el-button type="primary" @click="internalPowerDialogVisible = false">完成</el-button></template>
    </el-dialog>

    <section class="curve-grid">
      <div class="chart-section"><h2>防御减免曲线</h2><div ref="defenseChartRef" class="chart"></div><div class="curve-point-input"><span>剩余防御</span><el-input-number v-model="curveInputs.defense" :min="0" :max="10000" :step="10" controls-position="right" @change="markCurveInputManual('defense')" /></div></div>
      <div class="chart-section"><h2>会心率曲线</h2><div ref="critChartRef" class="chart"></div><div class="curve-point-input"><span>净会心</span><el-input-number v-model="curveInputs.crit" :min="-1000" :max="2000" :step="10" controls-position="right" @change="markCurveInputManual('crit')" /></div></div>
      <div class="chart-section"><h2>防御边际收益</h2><p>每增加 33 点剩余防御，防御减免的理论增量。</p><div ref="defenseDerivativeChartRef" class="chart"></div><div class="curve-point-input"><span>剩余防御</span><el-input-number v-model="curveInputs.defense" :min="0" :max="10000" :step="10" controls-position="right" @change="markCurveInputManual('defense')" /></div></div>
      <div class="chart-section"><h2>会心边际收益</h2><p>每增加 66 点净会心，会心率的理论增量。</p><div ref="critDerivativeChartRef" class="chart"></div><div class="curve-point-input"><span>净会心</span><el-input-number v-model="curveInputs.crit" :min="-1000" :max="2000" :step="10" controls-position="right" @change="markCurveInputManual('crit')" /></div></div>
    </section>

    <section class="calculator-grid">
      <div class="input-section defender-drop-zone" :class="{ 'is-dragging': defenseDropActive }" @dragenter.prevent="defenseDropActive = true" @dragover.prevent="defenseDropActive = true" @dragleave.prevent="defenseDropActive = false" @drop.prevent="handleDefensePanelDrop">
        <div class="section-title"><h2>变动前防守面板</h2><span>内功收益以此面板为计算基准，可拖入截图识别</span></div>
        <div class="field-grid">
          <label v-for="field in defenderCoreFields" :key="field.key" class="number-field">
            <span>{{ field.label }}</span>
            <el-input-number v-model="defender[field.key]" :min="0" :step="field.step" :precision="field.precision ?? (field.step < 1 ? 1 : 0)" controls-position="right">
              <template v-if="field.suffix" #suffix>{{ field.suffix }}</template>
            </el-input-number>
          </label>
        </div>
        <el-collapse class="defender-advanced">
          <el-collapse-item title="额外减伤乘区" name="reduction">
            <div class="field-grid defender-reduction-grid">
              <label v-for="field in defenderReductionFields" :key="field.key" class="number-field">
                <span>{{ field.label }}</span>
                <el-input-number v-model="defender[field.key]" :min="0" :step="field.step" :precision="field.precision ?? 3" controls-position="right">
                  <template v-if="field.suffix" #suffix>{{ field.suffix }}</template>
                </el-input-number>
              </label>
            </div>
          </el-collapse-item>
        </el-collapse>
        <div v-if="defenseRecognition.loading || defenseRecognition.error || defenseRecognition.success" class="inline-recognition">
          <div v-if="defenseRecognition.loading" class="recognition-progress"><el-icon class="is-loading"><Loading /></el-icon> 正在识别并回填防守面板</div>
          <el-alert v-if="defenseRecognition.error" class="recognition-alert" type="error" :closable="false" :title="defenseRecognition.error" />
          <el-alert v-if="defenseRecognition.success" class="recognition-alert" type="success" :closable="false" title="识别成功，已回填防守方面板" />
        </div>
      </div>

      <div class="input-section after-panel">
        <div class="section-title"><div><h2>变动后防守面板</h2><span>{{ afterDefenderOverrideActive ? '当前使用手动面板；基础条件变化后自动恢复计算' : '根据职业加成与所选内功自动生成，可手动调整' }}</span></div><el-button v-if="afterDefenderOverrideActive" :icon="RefreshLeft" @click="resetAfterDefenderToAuto">恢复自动计算</el-button></div>
        <div class="field-grid">
          <label v-for="field in defenderCoreFields" :key="field.key" class="number-field">
            <span>{{ field.label }}</span>
            <el-input-number :model-value="afterDefender[field.key]" :min="0" :step="field.step" :precision="field.precision ?? (field.step < 1 ? 1 : 0)" controls-position="right" @update:model-value="value => updateAfterDefenderField(field.key, value)"><template v-if="field.suffix" #suffix>{{ field.suffix }}</template></el-input-number>
          </label>
        </div>
        <el-collapse class="defender-advanced"><el-collapse-item title="额外减伤乘区" name="after-reduction"><div class="field-grid defender-reduction-grid"><label v-for="field in defenderReductionFields" :key="field.key" class="number-field"><span>{{ field.label }}</span><el-input-number :model-value="afterDefender[field.key]" :min="0" :step="field.step" :precision="field.precision ?? 3" controls-position="right" @update:model-value="value => updateAfterDefenderField(field.key, value)"><template v-if="field.suffix" #suffix>{{ field.suffix }}</template></el-input-number></label></div></el-collapse-item></el-collapse>
        <div class="after-summary">
          <span>内功实际防御 <b>+{{ formatNumber(internalPowerUpgrade.total.defense) }}</b></span>
          <span>内功实际气血 <b>+{{ formatNumber(internalPowerUpgrade.total.hp) }}</b></span>
          <span>内功会心抵抗 <b>+{{ formatNumber(internalPowerUpgrade.total.critResist) }}</b></span>
          <span>内功流派抵御 <b>+{{ Number(internalPowerUpgrade.total.resistPct || 0).toFixed(2) }}%</b></span>
        </div>
      </div>
    </section>

    <section class="result-section">
      <div class="section-title result-heading"><div><h2>承伤结果</h2><span>变动前为基础，变动后包含职业加成后的所选内功词条。</span></div><el-button type="primary" @click="openInternalPowerDialog">内功防御提升</el-button></div>
      <div class="result-comparison">
        <div class="result-snapshot"><h3>变动前</h3><div class="metric-grid"><div><span>伤害期望</span><strong>{{ formatNumber(beforeCalculation.expectedDamage) }}</strong></div><div><span>血量/伤害期望</span><strong>{{ formatNumber(beforeCalculation.durability) }}</strong></div><div><span>防御减免</span><strong>{{ formatPercent(beforeCalculation.defenseMitigation) }}</strong></div><div><span>实际会心率</span><strong>{{ formatPercent(beforeCalculation.critRate) }}</strong></div></div><div class="detail-grid"><span>剩余防御 <b>{{ formatNumber(beforeCalculation.remainingDefense) }}</b></span><span>净会心 <b>{{ formatNumber(beforeCalculation.netCrit) }}</b></span></div></div>
        <div class="result-snapshot result-after"><h3>变动后</h3><div class="metric-grid"><div><span>伤害期望</span><strong>{{ formatNumber(calculation.expectedDamage) }}</strong></div><div><span>血量/伤害期望</span><strong>{{ formatNumber(calculation.durability) }}</strong></div><div><span>防御减免</span><strong>{{ formatPercent(calculation.defenseMitigation) }}</strong></div><div><span>实际会心率</span><strong>{{ formatPercent(calculation.critRate) }}</strong></div></div><div class="detail-grid"><span>剩余防御 <b>{{ formatNumber(calculation.remainingDefense) }}</b></span><span>净会心 <b>{{ formatNumber(calculation.netCrit) }}</b></span></div></div>
      </div>
      <div class="durability-gain"><span>总体坦度提升</span><strong>{{ afterGainPct >= 0 ? '+' : '' }}{{ formatPercent(afterGainPct / 100) }}</strong></div>
    </section>

    <section class="advice-section">
      <div class="section-title"><div><h2>内功词条提升建议</h2><span>输入原始内功词条，分别计算职业乘区后的实际提升与独立收益。</span></div></div>
      <div class="recommendations recommendation-editor">
        <div v-for="item in recommendations" :key="item.key" class="recommendation-card">
          <div class="recommendation-heading">
            <span class="recommendation-name">{{ item.label }}</span>
            <small class="recommendation-actual">实际提升 +{{ formatNumber(item.actualValue) }} {{ item.actualUnit }}</small>
          </div>
          <el-input-number v-model="recommendationInputs[item.key]" :min="0" :step="RECOMMENDATION_FIELDS.find(field => field.key === item.key)?.step || 1" :precision="RECOMMENDATION_FIELDS.find(field => field.key === item.key)?.precision || 0" controls-position="right"><template v-if="RECOMMENDATION_FIELDS.find(field => field.key === item.key)?.suffix" #suffix>{{ RECOMMENDATION_FIELDS.find(field => field.key === item.key)?.suffix }}</template></el-input-number>
          <div class="recommendation-result">
            <strong>肉度 +{{ formatPercent(item.gainPct / 100) }}</strong>
            <small>血量/伤害期望 {{ formatNumber(item.durability) }}</small>
          </div>
        </div>
      </div>
    </section>

    <section class="comparison-section">
      <div class="section-title"><div><h2>自定义内功词条对比</h2><span>仅计算数值词条，不计入内功增伤占比。</span></div><el-button type="primary" plain :icon="Plus" @click="addComparisonPlan">新增方案</el-button></div>
      <div class="comparison-inputs">
        <div v-for="plan in comparePlans" :key="plan.id" class="entry-set plan-drop-zone" :class="{ 'is-dragging': plan.dropActive }" @dragenter.prevent="plan.dropActive = true" @dragover.prevent="plan.dropActive = true" @dragleave.prevent="plan.dropActive = false" @drop.prevent="handlePlanDrop($event, plan)">
          <div class="entry-heading">
            <h3>{{ plan.name }}</h3>
            <div class="entry-actions">
              <el-tooltip content="上传内功收益截图" placement="top"><el-upload accept="image/png,image/jpeg,image/webp" :auto-upload="false" :show-file-list="false" :on-change="file => handlePlanFileChange(file, plan)"><el-button :icon="Picture" circle :loading="plan.recognition.loading" aria-label="上传内功收益截图" /></el-upload></el-tooltip>
              <el-tooltip v-if="comparePlans.length > 1" content="删除方案" placement="top"><el-button :icon="Delete" circle type="danger" plain aria-label="删除方案" @click="removeComparisonPlan(plan.id)" /></el-tooltip>
            </div>
          </div>
          <div class="plan-drop-hint">拖拽内功词条总体收益截图到此处即可识别</div>
          <div v-if="plan.recognition.loading || plan.recognition.error || plan.recognition.success" class="inline-recognition">
            <div v-if="plan.recognition.loading" class="recognition-progress"><el-icon class="is-loading"><Loading /></el-icon> 正在识别并回填 {{ plan.name }}</div>
            <el-alert v-if="plan.recognition.error" class="recognition-alert" type="error" :closable="false" :title="plan.recognition.error" />
            <el-alert v-if="plan.recognition.success" class="recognition-alert" type="success" :closable="false" title="识别成功，已回填可识别词条" />
          </div>
          <label v-for="field in INNER_POWER_FIELDS" :key="field.key"><span>{{ field.label }}</span><el-input-number v-model="plan.entries[field.key]" :min="0" :step="field.step" :precision="field.precision ?? (field.step < 1 ? 1 : 0)" controls-position="right"><template v-if="field.suffix" #suffix>{{ field.suffix }}</template></el-input-number></label>
        </div>
      </div>
      <div class="comparison-results">
        <div v-for="item in comparison.plans" :key="item.id"><span>{{ item.name }}</span><strong>肉度 {{ item.gainPct >= 0 ? '+' : '' }}{{ formatPercent(item.gainPct / 100) }}</strong><small>血量/伤害期望 {{ formatNumber(item.durability) }}</small></div>
      </div>
    </section>
  </div>

  <div v-else class="app-container empty-calculator"><el-empty description="该计算器正在整理中" /></div>
</template>

<script setup name="PersonalDefenseCalculator">
import * as echarts from 'echarts'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Delete, DocumentCopy, Download, Edit, Loading, Picture, Plus, RefreshLeft, Upload, UploadFilled } from '@element-plus/icons-vue'
import {
  addPersonalDefenseAttackPanel,
  deletePersonalDefenseAttackPanel,
  getDefenseCalculatorSetting,
  listDefenseAttackPanels,
  listDefenseProfessionBonuses,
  listPersonalDefenseAttackPanels,
  recognizeDefensePanelImage,
  recognizeInternalPowerBenefitsImage,
  saveDefenseCalculatorSetting,
  updatePersonalDefenseAttackPanel
} from '@/api/personal/defenseCalculator'
import { listInternalPowerPresets, listInternalPowers } from '@/api/personal/internalPower'
import { getInternalPowerImageDisplayStatus } from '@/api/system/internalPowerImageDisplay'
import {
  DEFAULT_ATTACK_PANEL,
  DEFENDER_FIELDS,
  INNER_POWER_FIELDS,
  RECOMMENDATION_FIELDS,
  calculateDefense,
  calculateInternalPowerDefenseBenefit,
  calculateInternalPowerUpgrade,
  calculateInnerPowerComparisons,
  calculateRecommendation,
  areDefenderPanelsEqual,
  createDefaultDefender,
  createEmptyInnerPowerEntries,
  loadDefenseCalculatorPanelSetting,
  normalizeDefenderPanel,
  resolveAfterDefender,
  saveDefenseCalculatorPanelSetting
} from '@/utils/personalDefenseCalculator'
import { formatAttackPanelJson, formatAttackPanelJsonExample, parseAttackPanelJson } from '@/utils/pvpAttackPanelJson'
import useUserStore from '@/store/modules/user'
import { applyAiRecognitionQuota } from '@/utils/aiRecognitionQuota'

const route = useRoute()
const userStore = useUserStore()
const isDefenseCalculator = computed(() => route.path.includes('defense-calculator') || route.name === 'PersonalDefenseCalculator')
const defender = reactive(createDefaultDefender())
const professionBonuses = ref([])
const internalPowers = ref([])
const internalPowerPresets = ref([])
const internalPowerImageVisible = ref(true)
const internalPowerKeyword = ref('')
const professionId = ref(0)
const professionName = ref('')
const professionOverrides = reactive({})
const professionDraft = reactive({ defenseBonusPct: 0, hpBonusPct: 0 })
const selectedInternalPowerIds = ref([])
const recommendationInputs = reactive(createRecommendationInputs())
const internalPowerDialogVisible = ref(false)
const systemAttackPanels = ref([])
const personalAttackPanels = ref([])
const selectedPanelKey = ref(panelKey('system', 0))
const customAttackPanelDialogVisible = ref(false)
const attackPanelTab = ref('system')
const selectedSystemPanelId = ref(0)
const editingPersonalPanelId = ref(0)
const personalPanelDraft = reactive(createPersonalPanelDraft())
const attackJsonDialog = reactive({ visible: false, mode: 'example', title: '', text: '' })
const templateSaving = ref(false)
const settingLoaded = ref(false)
const afterDefenderDraft = reactive(createDefaultDefender())
const afterDefenderOverrideActive = ref(false)
const afterDefenderAutoBaseline = ref(null)
const recognitionDialogVisible = ref(false)
const recognitionFile = ref(null)
const recognizing = ref(false)
const recognitionError = ref('')
const defenseRecognition = reactive(createRecognitionState())
const defenseDropActive = ref(false)
const defenseChartRef = ref()
const critChartRef = ref()
const defenseDerivativeChartRef = ref()
const critDerivativeChartRef = ref()
const curveInputs = reactive({ defense: 2550, crit: 0 })
const curveInputManual = reactive({ defense: false, crit: false })
const comparePlans = reactive([createComparisonPlan(1), createComparisonPlan(2)])
const defenderCoreFields = DEFENDER_FIELDS.filter(field => !field.key.endsWith('Reduction'))
const defenderReductionFields = DEFENDER_FIELDS.filter(field => field.key.endsWith('Reduction'))
let nextPlanIndex = 3
let defenseChart
let critChart
let defenseDerivativeChart
let critDerivativeChart
let settingSaveTimer

const activePanel = computed(() => {
  const selected = parsePanelKey(selectedPanelKey.value)
  const panels = selected.source === 'personal' ? personalAttackPanels.value : systemAttackPanels.value
  return panels.find(item => item.panelId === selected.panelId) || DEFAULT_ATTACK_PANEL
})
const selectedSystemPanel = computed(() => systemAttackPanels.value.find(item => item.panelId === selectedSystemPanelId.value) || systemAttackPanels.value[0] || DEFAULT_ATTACK_PANEL)
const selectedProfession = computed(() => professionBonuses.value.find(item => item.professionId === professionId.value) || null)
const activeProfessionBonus = computed(() => ({
  defenseBonusPct: Number(professionDraft.defenseBonusPct || 0),
  hpBonusPct: Number(professionDraft.hpBonusPct || 0)
}))
const selectedInternalPowers = computed(() => internalPowers.value.filter(power => selectedInternalPowerIds.value.includes(Number(power.powerId || power.id))))
const internalPowerUpgrade = computed(() => calculateInternalPowerUpgrade(
  defender,
  activePanel.value,
  selectedInternalPowers.value,
  activeProfessionBonus.value
))
const availableInternalPowerUpgradeMap = computed(() => new Map(internalPowers.value.map(power => {
  const upgrade = calculateInternalPowerUpgrade(defender, activePanel.value, [power], activeProfessionBonus.value).powers[0]
  return [power.powerId, upgrade]
})))
const filteredInternalPowers = computed(() => {
  const keyword = internalPowerKeyword.value.trim().toLowerCase()
  if (!keyword) return internalPowers.value
  return internalPowers.value.filter(power => [
    power.name,
    power.category,
    ...power.entries.flatMap(entry => [entry.name, entry.value])
  ].some(value => String(value || '').toLowerCase().includes(keyword)))
})
const autoAfterDefender = computed(() => internalPowerUpgrade.value.afterDefender)
const afterDefender = computed(() => resolveAfterDefender(
  autoAfterDefender.value,
  afterDefenderOverrideActive.value ? afterDefenderDraft : null,
  afterDefenderAutoBaseline.value
))
const calculation = computed(() => calculateDefense(afterDefender.value, activePanel.value))
const beforeCalculation = computed(() => internalPowerUpgrade.value.base)
const afterGainPct = computed(() => beforeCalculation.value.durability > 0
  ? (calculation.value.durability / beforeCalculation.value.durability - 1) * 100
  : 0)
const recommendations = computed(() => calculateRecommendation(defender, activePanel.value, recommendationInputs, activeProfessionBonus.value))
const comparison = computed(() => calculateInnerPowerComparisons(defender, activePanel.value, comparePlans))
const professionIsCustomized = computed(() => Boolean(professionOverrides[String(professionId.value)]))

onMounted(async () => {
  await loadCalculatorData()
  initCharts()
  syncCurveInputsFromResult()
  window.addEventListener('resize', resizeCharts)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  defenseChart?.dispose()
  critChart?.dispose()
  defenseDerivativeChart?.dispose()
  critDerivativeChart?.dispose()
  window.clearTimeout(settingSaveTimer)
})
watch(calculation, () => {
  updateCharts()
  syncCurveInputsFromResult()
}, { deep: true })
watch(autoAfterDefender, value => {
  if (!settingLoaded.value) return
  if (afterDefenderOverrideActive.value && !areDefenderPanelsEqual(value, afterDefenderAutoBaseline.value)) {
    resetAfterDefenderToAuto(false)
    ElMessage.info('基础条件已变化，变动后面板已恢复自动计算')
  } else if (!afterDefenderOverrideActive.value) {
    Object.assign(afterDefenderDraft, normalizeDefenderPanel(value))
  }
}, { deep: true })
watch([defender, selectedPanelKey, professionId, professionDraft, selectedInternalPowerIds, recommendationInputs], () => {
  scheduleSettingSave()
}, { deep: true })
watch(() => curveInputs.defense, () => syncDefenseCurvePointers())
watch(() => curveInputs.crit, () => syncCritCurvePointers())

async function loadCalculatorData() {
  const legacySetting = loadDefenseCalculatorPanelSetting()
  try {
    const [settingResponse, systemResponse, personalResponse, professionResponse, powerResponse, presetResponse, imageDisplayResponse] = await Promise.all([
      getDefenseCalculatorSetting(),
      listDefenseAttackPanels(),
      listPersonalDefenseAttackPanels(),
      listDefenseProfessionBonuses(),
      listInternalPowers(),
      listInternalPowerPresets().catch(() => ({ presets: [] })),
      getInternalPowerImageDisplayStatus().catch(() => ({ data: { enabled: true } }))
    ])
    const setting = settingResponse.data || settingResponse || {}
    systemAttackPanels.value = systemResponse.data?.length ? systemResponse.data : [DEFAULT_ATTACK_PANEL]
    personalAttackPanels.value = personalResponse.data || []
    professionBonuses.value = professionResponse.data || []
    internalPowers.value = (powerResponse.powers || powerResponse.data?.powers || []).map(normalizeInternalPower)
    internalPowerPresets.value = presetResponse.presets || presetResponse.data || []
    internalPowerImageVisible.value = imageDisplayResponse.data?.enabled !== false
    Object.assign(defender, createDefaultDefender(), setting.defender || {})
    Object.assign(professionOverrides, setting.professionOverrides || {})
    Object.assign(recommendationInputs, createRecommendationInputs(), setting.recommendationInputs || {})
    selectedInternalPowerIds.value = normalizeSelectedPowerIds(setting.selectedInternalPowerIds)
    professionId.value = Number(setting.professionId || professionBonuses.value[0]?.professionId || 0)
    professionName.value = setting.professionName || selectedProfession.value?.professionName || ''
    loadProfessionDraft()
    selectedPanelKey.value = panelKey(setting.selectedPanelSource, setting.selectedPanelId)
    await migrateLegacyCustomPanel(legacySetting)
    afterDefenderAutoBaseline.value = setting.afterDefenderAutoBaseline || null
    if (setting.afterDefenderOverride && setting.afterDefenderAutoBaseline) {
      Object.assign(afterDefenderDraft, normalizeDefenderPanel(setting.afterDefenderOverride))
      afterDefenderOverrideActive.value = true
    }
  } catch {
    systemAttackPanels.value = [DEFAULT_ATTACK_PANEL]
    personalAttackPanels.value = []
    professionBonuses.value = []
    internalPowers.value = []
    internalPowerPresets.value = []
    internalPowerImageVisible.value = true
    Object.assign(defender, legacySetting.defender || createDefaultDefender())
    selectedPanelKey.value = panelKey('system', 0)
  }
  ensureSelectedPanel()
  cleanSelectedPowerIds()
  await nextTick()
  if (!afterDefenderOverrideActive.value || !areDefenderPanelsEqual(autoAfterDefender.value, afterDefenderAutoBaseline.value)) {
    resetAfterDefenderToAuto(false)
  }
  settingLoaded.value = true
  await saveCurrentSetting()
}

function openCustomAttackPanelDialog() {
  const current = parsePanelKey(selectedPanelKey.value)
  attackPanelTab.value = current.source
  selectedSystemPanelId.value = current.source === 'system'
    ? current.panelId
    : (systemAttackPanels.value[0]?.panelId || 0)
  if (editingPersonalPanelId.value) selectPersonalPanel(editingPersonalPanelId.value)
  else if (personalAttackPanels.value.length) selectPersonalPanel(personalAttackPanels.value[0].panelId)
  customAttackPanelDialogVisible.value = true
}

async function useSystemPreset() {
  const panel = selectedSystemPanel.value
  if (!panel?.panelId && panel !== DEFAULT_ATTACK_PANEL) return
  selectedPanelKey.value = panelKey('system', panel.panelId)
  customAttackPanelDialogVisible.value = false
  await saveCurrentSetting()
  ElMessage.success(`已使用系统预设“${panel.panelName}”`)
}

function openAttackJsonDialog(mode) {
  attackJsonDialog.mode = mode
  if (mode === 'import-personal') {
    if (!editingPersonalPanelId.value) {
      ElMessage.warning('请先新增或选择一个个人模板')
      return
    }
    attackJsonDialog.title = '导入个人进攻面板 JSON'
    attackJsonDialog.text = formatAttackPanelJsonExample()
  } else if (mode === 'export-system') {
    attackJsonDialog.title = `导出 ${selectedSystemPanel.value.panelName}`
    attackJsonDialog.text = formatAttackPanelJson(selectedSystemPanel.value)
  } else if (mode === 'export-personal') {
    attackJsonDialog.title = `导出 ${personalPanelDraft.panelName}`
    attackJsonDialog.text = formatAttackPanelJson({ ...personalPanelDraft, status: '0', remark: '' })
  } else {
    attackJsonDialog.title = '进攻方面板示例 JSON'
    attackJsonDialog.text = formatAttackPanelJsonExample()
  }
  attackJsonDialog.visible = true
}

function applyPersonalJsonImport() {
  try {
    Object.assign(personalPanelDraft, parseAttackPanelJson(attackJsonDialog.text, { requireMetadata: false }))
    attackJsonDialog.visible = false
    ElMessage.success('JSON 校验通过，请点击“保存并使用”')
  } catch (error) {
    ElMessage.error(error.message || 'JSON 导入失败')
  }
}

function copyAttackJsonSuccess() {
  ElMessage.success('JSON 已复制')
}

async function addPersonalPanel() {
  templateSaving.value = true
  try {
    const response = await addPersonalDefenseAttackPanel(attackPanelPayload(DEFAULT_ATTACK_PANEL))
    const panel = response.data || response
    personalAttackPanels.value.push(panel)
    selectPersonalPanel(panel.panelId)
    selectedPanelKey.value = panelKey('personal', panel.panelId)
  } finally {
    templateSaving.value = false
  }
}

function selectPersonalPanel(panelId) {
  const panel = personalAttackPanels.value.find(item => item.panelId === panelId)
  if (!panel) {
    editingPersonalPanelId.value = 0
    Object.assign(personalPanelDraft, createPersonalPanelDraft())
    return
  }
  editingPersonalPanelId.value = panel.panelId
  Object.assign(personalPanelDraft, createPersonalPanelDraft(panel))
}

async function savePersonalPanel() {
  if (!editingPersonalPanelId.value) return
  templateSaving.value = true
  try {
    await updatePersonalDefenseAttackPanel(editingPersonalPanelId.value, attackPanelPayload(personalPanelDraft))
    const index = personalAttackPanels.value.findIndex(item => item.panelId === editingPersonalPanelId.value)
    if (index >= 0) Object.assign(personalAttackPanels.value[index], personalPanelDraft)
    selectedPanelKey.value = panelKey('personal', editingPersonalPanelId.value)
    customAttackPanelDialogVisible.value = false
    await saveCurrentSetting()
    ElMessage.success('攻击方面板已保存并应用')
  } finally {
    templateSaving.value = false
  }
}

async function removePersonalPanel() {
  const panel = personalAttackPanels.value.find(item => item.panelId === editingPersonalPanelId.value)
  if (!panel) return
  try {
    await ElMessageBox.confirm(`确定删除“${panel.panelName}”吗？`, '删除攻击方面板', { type: 'warning' })
  } catch {
    return
  }
  templateSaving.value = true
  try {
    await deletePersonalDefenseAttackPanel(panel.panelId)
    personalAttackPanels.value = personalAttackPanels.value.filter(item => item.panelId !== panel.panelId)
    const next = personalAttackPanels.value[0]
    if (next) selectPersonalPanel(next.panelId)
    else selectPersonalPanel(0)
    ensureSelectedPanel()
    await saveCurrentSetting()
    ElMessage.success('攻击方面板已删除')
  } finally {
    templateSaving.value = false
  }
}

async function migrateLegacyCustomPanel(legacySetting) {
  if (personalAttackPanels.value.length || Number(legacySetting.selectedPanelId) !== -1) return
  const response = await addPersonalDefenseAttackPanel(attackPanelPayload(legacySetting.customAttackPanel || DEFAULT_ATTACK_PANEL))
  const panel = response.data || response
  personalAttackPanels.value.push(panel)
  selectedPanelKey.value = panelKey('personal', panel.panelId)
  saveDefenseCalculatorPanelSetting({
    defender: legacySetting.defender,
    selectedPanelId: 0,
    customAttackPanel: legacySetting.customAttackPanel
  })
  await saveCurrentSetting()
}

function ensureSelectedPanel() {
  const selected = parsePanelKey(selectedPanelKey.value)
  const panels = selected.source === 'personal' ? personalAttackPanels.value : systemAttackPanels.value
  if (panels.some(item => item.panelId === selected.panelId)) return
  const fallback = personalAttackPanels.value[0] || systemAttackPanels.value[0] || DEFAULT_ATTACK_PANEL
  const source = personalAttackPanels.value.some(item => item.panelId === fallback.panelId) ? 'personal' : 'system'
  selectedPanelKey.value = panelKey(source, fallback.panelId)
}

function scheduleSettingSave() {
  if (!settingLoaded.value) return
  window.clearTimeout(settingSaveTimer)
  settingSaveTimer = window.setTimeout(() => { saveCurrentSetting() }, 500)
}

async function saveCurrentSetting() {
  if (!settingLoaded.value) return
  const selected = parsePanelKey(selectedPanelKey.value)
  try {
    await saveDefenseCalculatorSetting({
      defender,
      selectedPanelSource: selected.source,
      selectedPanelId: selected.panelId,
      professionId: professionId.value,
      professionName: selectedProfession.value?.professionName || professionName.value,
      professionOverrides,
      selectedInternalPowerIds: selectedInternalPowerIds.value,
      recommendationInputs,
      afterDefenderOverride: afterDefenderOverrideActive.value ? afterDefenderDraft : null,
      afterDefenderAutoBaseline: afterDefenderOverrideActive.value ? afterDefenderAutoBaseline.value : null
    })
  } catch {
    ElMessage.warning('坦度计算器设置暂未同步到账号')
  }
}

function updateAfterDefenderField(key, value) {
  if (!afterDefenderOverrideActive.value) {
    Object.assign(afterDefenderDraft, normalizeDefenderPanel(autoAfterDefender.value))
    afterDefenderAutoBaseline.value = normalizeDefenderPanel(autoAfterDefender.value)
    afterDefenderOverrideActive.value = true
  }
  afterDefenderDraft[key] = Math.max(Number(value) || 0, 0)
  scheduleSettingSave()
}

function resetAfterDefenderToAuto(showMessage = true) {
  Object.assign(afterDefenderDraft, normalizeDefenderPanel(autoAfterDefender.value))
  afterDefenderOverrideActive.value = false
  afterDefenderAutoBaseline.value = null
  scheduleSettingSave()
  if (showMessage) ElMessage.success('已恢复职业与内功自动计算')
}

function createRecommendationInputs() {
  return Object.fromEntries(RECOMMENDATION_FIELDS.map(field => [field.key, field.key === 'defense' ? 33 : (field.key === 'critResist' ? 66 : 0)]))
}

function normalizeInternalPower(power = {}) {
  return {
    ...power,
    powerId: Number(power.powerId || power.id || 0),
    name: String(power.name || '未命名内功'),
    entries: Array.isArray(power.entries) ? power.entries : []
  }
}

function isInternalPowerSelected(powerId) {
  return selectedInternalPowerIds.value.includes(Number(powerId))
}

function toggleInternalPower(powerId) {
  const normalizedId = Number(powerId)
  if (isInternalPowerSelected(normalizedId)) {
    selectedInternalPowerIds.value = selectedInternalPowerIds.value.filter(id => id !== normalizedId)
    return
  }
  if (selectedInternalPowerIds.value.length >= 6) {
    ElMessage.warning('最多选择 6 本内功')
    return
  }
  selectedInternalPowerIds.value = [...selectedInternalPowerIds.value, normalizedId]
}

function clearInternalPowerSelection() {
  selectedInternalPowerIds.value = []
}

function getInternalPowerUpgrade(powerId) {
  return availableInternalPowerUpgradeMap.value.get(Number(powerId)) || {
    defense: 0,
    hp: 0,
    critResist: 0,
    resistPct: 0,
    gainPct: 0,
    ignoredEntries: []
  }
}

function isIgnoredInternalPowerEntry(entry) {
  return Boolean(calculateInternalPowerDefenseBenefit(entry, defender, activePanel.value).note)
}

function getInternalPowerEntryTitle(entry) {
  const benefit = calculateInternalPowerDefenseBenefit(entry, defender, activePanel.value)
  if (benefit.note) return `${formatInternalPowerEntry(entry)}：${benefit.note}，坦度收益为 0`
  return `${formatInternalPowerEntry(entry)}：坦度 +${formatPercent(benefit.gain)}`
}

function formatInternalPowerEntry(entry = {}) {
  const name = String(entry.name || entry.entryName || entry.词条 || '').trim() || '未命名词条'
  const rawValue = entry.value ?? entry.entryValue ?? entry.数值
  if (rawValue === undefined || rawValue === null || rawValue === '') return name
  const value = String(rawValue).trim()
  return `${name} ${value}`
}

function formatInternalPowerEntryWithGain(entry = {}) {
  const benefit = calculateInternalPowerDefenseBenefit(entry, defender, activePanel.value)
  return `${formatInternalPowerEntry(entry)} · ${formatPercent(benefit.gain)}`
}

function formatInternalPowerElements(elements = {}) {
  const labels = [
    ['metal', '金'],
    ['wood', '木'],
    ['water', '水'],
    ['fire', '火'],
    ['earth', '土']
  ]
  const sequence = labels.flatMap(([key, label]) => Array.from({ length: Math.max(0, Number(elements?.[key] || 0)) }, () => label)).join('')
  return sequence || '未配置元素'
}

function resolveInternalPowerImage(power = {}) {
  if (!internalPowerImageVisible.value) return ''
  const category = String(power.category || '').trim()
  const preset = internalPowerPresets.value.find(item => [item.name, item.displayName, item.value].some(value => String(value || '').trim() === category))
  return resolveInternalPowerImagePath(power.imageUrl || preset?.imageUrl || '')
}

function resolveInternalPowerImagePath(value = '') {
  const path = String(value || '').trim()
  if (!path) return ''
  if (/^(https?:)?\/\//.test(path) || path.startsWith('data:') || path.startsWith('blob:')) return path
  if (path.startsWith('/profile/')) return `${import.meta.env.VITE_APP_BASE_API}${path}`
  return path
}

function normalizeSelectedPowerIds(values) {
  const available = new Set(internalPowers.value.map(item => item.powerId))
  return [...new Set((Array.isArray(values) ? values : []).map(Number).filter(id => id > 0 && available.has(id)))].slice(0, 6)
}

function cleanSelectedPowerIds() {
  selectedInternalPowerIds.value = normalizeSelectedPowerIds(selectedInternalPowerIds.value)
}

function loadProfessionDraft() {
  const defaults = selectedProfession.value || { defenseBonusPct: 0, hpBonusPct: 0 }
  const override = professionOverrides[String(professionId.value)]
  professionName.value = defaults.professionName || professionName.value
  professionDraft.defenseBonusPct = Number(override?.defenseBonusPct ?? defaults.defenseBonusPct ?? 0)
  professionDraft.hpBonusPct = Number(override?.hpBonusPct ?? defaults.hpBonusPct ?? 0)
}

function changeProfession() {
  professionName.value = selectedProfession.value?.professionName || ''
  loadProfessionDraft()
  scheduleSettingSave()
}

async function saveProfessionOverride() {
  if (!professionId.value) return
  professionOverrides[String(professionId.value)] = {
    defenseBonusPct: Number(professionDraft.defenseBonusPct || 0),
    hpBonusPct: Number(professionDraft.hpBonusPct || 0)
  }
  await saveCurrentSetting()
  ElMessage.success(`${professionName.value || '当前职业'}个人加成已保存`)
}

async function restoreProfessionDefault() {
  delete professionOverrides[String(professionId.value)]
  loadProfessionDraft()
  await saveCurrentSetting()
  ElMessage.success('已恢复管理员默认职业加成')
}

function openInternalPowerDialog() {
  internalPowerKeyword.value = ''
  internalPowerDialogVisible.value = true
}

function markCurveInputManual(type) {
  curveInputManual[type] = true
  if (type === 'defense') syncDefenseCurvePointers()
  else syncCritCurvePointers()
}

function syncCurveInputsFromResult() {
  curveInputManual.defense = false
  curveInputManual.crit = false
  curveInputs.defense = clampCurveInput(calculation.value.remainingDefense, 0, 10000)
  curveInputs.crit = clampCurveInput(calculation.value.netCrit, -1000, 2000)
}

function panelKey(source, panelId) {
  return `${source === 'personal' ? 'personal' : 'system'}:${Number(panelId) || 0}`
}

function parsePanelKey(value) {
  const [source, panelId] = String(value || '').split(':')
  return { source: source === 'personal' ? 'personal' : 'system', panelId: Number(panelId) || 0 }
}

function createPersonalPanelDraft(source = {}) {
  return { ...DEFAULT_ATTACK_PANEL, ...source }
}

function attackPanelPayload(panel = {}) {
  return Object.fromEntries(Object.keys(DEFAULT_ATTACK_PANEL)
    .filter(key => !['panelId', 'panelName'].includes(key))
    .map(key => [key, Number(panel[key]) || 0]))
}

const attackPanelCoreFields = [
  { key: 'attack', label: '攻击' },
  { key: 'breakDefense', label: '破防' },
  { key: 'restraintValue', label: '克制数值' },
  { key: 'crit', label: '会心' },
  { key: 'critDmg', label: '会伤增幅', precision: 3, step: 0.01 },
  { key: 'extraCritRate', label: '额外会心率', precision: 3, step: 0.01 },
  { key: 'restraintPct', label: '流派克制', precision: 3, step: 0.01 },
  { key: 'skillBonus', label: '技能增强' },
  { key: 'skillBonusPct', label: '技能增强%', precision: 3, step: 0.01 },
  { key: 'techniqueRestraint', label: '技巧克制' }
]
const attackPanelAdvancedFields = [
  { key: 'internalBonus', label: '内功增伤' },
  { key: 'gearBonus', label: '装备增伤' },
  { key: 'martialBonus', label: '武蕴增伤' },
  { key: 'otherBonus', label: '其他增伤' }
]

function openRecognitionDialog() {
  recognitionFile.value = null
  recognitionError.value = ''
  recognitionDialogVisible.value = true
}

function handleRecognitionFileChange(uploadFile) {
  recognitionFile.value = uploadFile.raw || null
  if (recognitionFile.value) recognizeDefensePanelFile(recognitionFile.value, true)
}

function clearRecognitionFile() {
  recognitionFile.value = null
  recognitionError.value = ''
  defenseRecognition.success = false
}

function handleRecognitionExceed() {
  ElMessage.warning('一次只能识别一张面板截图')
}

async function recognizeDefensePanelFile(file, showDialog = false) {
  if (!isImageFile(file)) {
    const message = '请上传 PNG、JPG 或 WebP 格式的图片'
    recognitionError.value = message
    defenseRecognition.error = message
    defenseRecognition.success = false
    return
  }
  recognizing.value = true
  recognitionError.value = ''
  defenseRecognition.loading = true
  defenseRecognition.error = ''
  defenseRecognition.success = false
  if (showDialog) recognitionDialogVisible.value = true
  try {
    const response = await recognizeDefensePanelImage(file)
    const result = response.data || response
    applyAiRecognitionQuota(userStore, result, Number(result?.consumedCount || 0))
    if (!result?.success || !result.parsed) {
      const message = result?.error || '图片识别失败'
      recognitionError.value = message
      defenseRecognition.error = message
      return
    }
    defenseRecognition.success = true
    applyRecognizedDefensePanel(result.parsed)
    ElMessage.success('识别完成，已回填防守方面板')
  } catch (error) {
    const message = error?.msg || error?.message || '图片识别请求失败'
    recognitionError.value = message
    defenseRecognition.error = message
  } finally {
    recognizing.value = false
    defenseRecognition.loading = false
  }
}

function handleDefensePanelDrop(event) {
  defenseDropActive.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) recognizeDefensePanelFile(file)
}

function applyRecognizedDefensePanel(parsed) {
  assignRecognizedNumber('hp', parsed['气血'])
  assignRecognizedNumber('defense', parsed['防御'])
  assignRecognizedNumber('critResist', parsed['会心抗性'])
  assignRecognizedNumber('resist', parsed['流派抵御'])
  const resistPct = Number(String(parsed['流派抵御百分比'] ?? '').replace('%', '').trim())
  if (Number.isFinite(resistPct) && resistPct >= 0) defender.resistPct = resistPct
}

function assignRecognizedNumber(field, value) {
  const number = Number(value)
  if (Number.isFinite(number) && number >= 0) defender[field] = number
}

function createRecognitionState() {
  return { loading: false, error: '', success: false }
}

function createComparisonPlan(index) {
  return {
    id: `plan-${index}`,
    name: `方案 ${planName(index)}`,
    entries: createEmptyInnerPowerEntries(),
    dropActive: false,
    recognition: createRecognitionState()
  }
}

function planName(index) {
  return index <= 26 ? String.fromCharCode(64 + index) : String(index)
}

function addComparisonPlan() {
  comparePlans.push(createComparisonPlan(nextPlanIndex++))
}

function removeComparisonPlan(planId) {
  if (comparePlans.length <= 1) return
  const index = comparePlans.findIndex(plan => plan.id === planId)
  if (index >= 0) comparePlans.splice(index, 1)
}

function handlePlanDrop(event, plan) {
  plan.dropActive = false
  const file = event.dataTransfer?.files?.[0]
  if (file) recognizePlanFile(file, plan)
}

function handlePlanFileChange(uploadFile, plan) {
  const file = uploadFile.raw || null
  if (file) recognizePlanFile(file, plan)
}

async function recognizePlanFile(file, plan) {
  if (!isImageFile(file)) {
    plan.recognition.error = '请上传 PNG、JPG 或 WebP 格式的图片'
    plan.recognition.success = false
    return
  }
  plan.recognition.loading = true
  plan.recognition.error = ''
  plan.recognition.success = false
  try {
    const response = await recognizeInternalPowerBenefitsImage(file)
    const result = response.data || response
    applyAiRecognitionQuota(userStore, result, Number(result?.consumedCount || 0))
    if (!result?.success || !result.parsed) {
      plan.recognition.error = result?.error || '图片识别失败'
      return
    }
    applyRecognizedBenefitEntries(plan.entries, result.parsed)
    plan.recognition.success = true
    ElMessage.success(`${plan.name}识别完成，已回填词条`)
  } catch (error) {
    plan.recognition.error = error?.msg || error?.message || '图片识别请求失败'
  } finally {
    plan.recognition.loading = false
  }
}

function applyRecognizedBenefitEntries(entries, parsed) {
  const fields = {
    '耐力': 'endurance',
    '根骨': 'rootBone',
    '身法': 'agility',
    '内功防御': 'internalDefense',
    '外功防御': 'externalDefense',
    '防御': 'defense',
    '气血上限': 'hp',
    '抗会心': 'critResist',
    '抗内功会心': 'internalCritResist',
    '抗外功会心': 'externalCritResist'
  }
  Object.entries(fields).forEach(([source, target]) => {
    const value = Number(parsed[source])
    if (Number.isFinite(value) && value >= 0) entries[target] = value
  })
  const resistPct = parsePercent(parsed['流派抵御'])
  if (resistPct !== null) entries.resistPct = resistPct
}

function parsePercent(value) {
  const number = Number(String(value ?? '').replace('%', '').trim())
  return Number.isFinite(number) && number >= 0 ? number : null
}

function isImageFile(file) {
  return Boolean(file?.type && ['image/png', 'image/jpeg', 'image/webp'].includes(file.type))
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
  defenseDerivativeChart.setOption(lineOption('剩余防御', '每 +33 点减免增量', calculation.value.defenseDerivativeCurve, '#427d45', { yMax: curveMaximum(calculation.value.defenseDerivativeCurve) }))
  critDerivativeChart.setOption(lineOption('净会心', '每 +66 点会心率增量', calculation.value.critDerivativeCurve, '#925189', { inverseX: true, yMax: curveMaximum(calculation.value.critDerivativeCurve) }))
}

function lineOption(xName, yName, data, color, options = {}) {
  const yMax = options.yMax || 1
  return {
    grid: { left: 52, right: 24, top: 22, bottom: 42 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', snap: true },
      formatter: params => {
        const [x, y] = params?.[0]?.data || []
        return `${xName}: ${formatNumber(x)}<br/>${yName}: ${(Number(y) * 100).toFixed(6)}%`
      }
    },
    xAxis: { type: 'value', name: xName, nameLocation: 'end', axisPointer: { snap: true }, inverse: Boolean(options.inverseX), splitLine: { lineStyle: { color: '#edf0f5' } } },
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
function syncDefenseCurvePointers() {
  nextTick(() => {
    showChartPointer(defenseChart, curveInputs.defense, 0, 10000)
    showChartPointer(defenseDerivativeChart, curveInputs.defense, 0, 10000)
  })
}
function syncCritCurvePointers() {
  nextTick(() => {
    showChartPointer(critChart, curveInputs.crit, -1000, 2000)
    showChartPointer(critDerivativeChart, curveInputs.crit, -1000, 2000)
  })
}
function showChartPointer(chart, value, min, max) {
  if (!chart) return
  const x = clampCurveInput(value, min, max)
  const dataIndex = Math.round((x - min) / 10)
  const xPixel = chart.convertToPixel({ xAxisIndex: 0 }, x)
  chart.dispatchAction({ type: 'updateAxisPointer', x: xPixel, y: chart.getHeight() / 2 })
  chart.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex })
}
function formatNumber(value) { return Number(value || 0).toLocaleString('zh-CN', { maximumFractionDigits: 2 }) }
function formatPercent(value) { return `${(Number(value || 0) * 100).toFixed(2)}%` }
function clampCurveInput(value, min, max) { return Math.min(Math.max(Number(value) || 0, min), max) }
</script>

<style scoped>
.defense-page { display: grid; gap: 18px; color: #233247; }
.page-header { display: flex; align-items: end; justify-content: space-between; gap: 20px; padding-bottom: 16px; border-bottom: 1px solid #dbe3ed; }
.page-header h1, h2, h3 { margin: 0; letter-spacing: 0; }
.page-header h1 { font-size: 26px; }
.page-header p, .section-title span { margin: 8px 0 0; color: #6c7b8d; font-size: 14px; }
.panel-select { width: 240px; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.profession-bar { display: grid; grid-template-columns: minmax(180px, 1fr) repeat(2, minmax(160px, .8fr)) auto; align-items: end; gap: 14px; padding: 16px 18px; border: 1px solid #dbe3ed; border-radius: 8px; background: #fff; }
.profession-field { display: grid; gap: 7px; color: #526176; font-size: 13px; }
.profession-field :deep(.el-select), .profession-field :deep(.el-input-number) { width: 100%; }
.profession-actions { display: flex; align-items: center; gap: 8px; }
.attack-panel-description { margin: 0 0 18px; color: #68788c; font-size: 13px; line-height: 1.7; }
.attack-panel-tabs :deep(.el-tabs__header) { margin-bottom: 16px; }
.template-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
.json-toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin: -6px 0 18px; }
.json-help { margin: 0 0 12px; color: #68788c; font-size: 13px; }
.template-select { flex: 1; min-width: 0; }
.attack-panel-form :deep(.el-form-item) { margin-bottom: 16px; }
.attack-panel-advanced { width: 100%; }
.defender-advanced { width: 100%; margin-top: 18px; }
.defender-reduction-grid { margin-top: 0; padding: 0 2px 2px; }
.upload-icon { margin-bottom: 8px; font-size: 34px; color: #3c7bb2; }
.recognition-progress { display: flex; align-items: center; gap: 8px; margin-top: 14px; color: #376b9a; font-size: 13px; }
.recognition-alert { margin-top: 14px; }
.curve-grid, .calculator-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.chart-section, .input-section, .result-section, .advice-section, .comparison-section { border: 1px solid #dbe3ed; border-radius: 8px; background: #fff; }
.chart-section { padding: 18px; }
.chart-section h2, .input-section h2, .result-section h2, .advice-section h2, .comparison-section h2 { font-size: 17px; }
.chart { height: 270px; margin-top: 12px; }
.curve-point-input { display: grid; grid-template-columns: auto minmax(120px, 1fr); align-items: center; gap: 10px; margin-top: 10px; color: #526176; font-size: 13px; }
.curve-point-input :deep(.el-input-number) { width: 100%; }
.input-section, .result-section { padding: 20px; }
.after-panel { background: #f9fbfd; }
.after-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 18px; padding-top: 16px; border-top: 1px solid #e4e9ef; color: #69788b; font-size: 13px; }
.after-summary b { margin-left: 6px; color: #16634e; }
.defender-drop-zone, .plan-drop-zone { transition: border-color .18s ease, background-color .18s ease; }
.defender-drop-zone.is-dragging, .plan-drop-zone.is-dragging { border-color: #3c7bb2; background: #f0f7fd; box-shadow: inset 0 0 0 1px #3c7bb2; }
.inline-recognition { grid-column: 1 / -1; }
.field-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }
.number-field, .entry-set label { display: grid; gap: 7px; color: #526176; font-size: 13px; }
.number-field :deep(.el-input-number), .entry-set :deep(.el-input-number) { width: 100%; }
.metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; margin-top: 18px; background: #e5eaf0; }
.metric-grid div { min-height: 94px; padding: 16px; background: #f8fafc; }
.metric-grid span, .detail-grid span, .recommendations span, .comparison-results span { display: block; color: #69788b; font-size: 13px; }
.metric-grid strong { display: block; margin-top: 10px; color: #173a62; font-size: 22px; font-variant-numeric: tabular-nums; }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 20px; }
.detail-grid b { margin-left: 8px; color: #26394f; font-variant-numeric: tabular-nums; }
.result-heading { align-items: center; }
.result-comparison { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 18px; }
.result-snapshot { padding: 16px; border: 1px solid #e1e7ef; background: #fbfcfe; }
.result-snapshot h3 { color: #526176; font-size: 15px; }
.result-snapshot .metric-grid { margin-top: 12px; }
.result-after { border-color: #a9cbb7; background: #f5faf7; }
.durability-gain { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-top: 16px; padding: 15px 18px; border-left: 4px solid #2f8467; background: #edf8f3; }
.durability-gain span { color: #45675b; }
.durability-gain strong { color: #16634e; font-size: 24px; }
.advice-section, .comparison-section { padding: 20px; }
.recommendations, .comparison-results { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 16px; }
.recommendations > div, .comparison-results > div { padding: 16px; border-left: 4px solid #3c7bb2; background: #f6f9fc; }
.comparison-results strong { display: block; margin-top: 8px; color: #16634e; font-size: 18px; }
.comparison-results small { display: block; margin-top: 7px; color: #69788b; }
.recommendation-editor { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.recommendation-card { display: grid; gap: 10px; min-width: 0; }
.recommendation-editor :deep(.el-input-number) { width: 100%; }
.recommendation-heading, .recommendation-result { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; min-width: 0; }
.recommendation-name { color: #314b67 !important; font-size: 17px !important; font-weight: 700; }
.recommendation-actual, .recommendation-result small { margin: 0; color: #69788b; font-size: 12px; white-space: nowrap; }
.recommendation-result strong { color: #16634e; font-size: 14px; font-weight: 700; white-space: nowrap; }
.power-dialog-toolbar { display: flex; align-items: end; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
.power-dialog-toolbar div { display: grid; gap: 6px; }
.power-dialog-toolbar span, .ignored-entry { color: #718096; font-size: 12px; }
.power-picker-actions { display: flex !important; grid-template-columns: minmax(220px, 340px) auto auto; align-items: center; gap: 10px !important; }
.power-search { width: min(340px, 100%); }
.internal-power-picker-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; max-height: min(58vh, 620px); overflow-y: auto; padding: 2px 4px 12px 2px; }
.internal-power-picker-card { position: relative; display: grid; grid-template-columns: 82px minmax(0, 1fr); gap: 10px 12px; min-width: 0; min-height: 250px; border: 2px solid #d8e3ee; border-radius: 8px; padding: 16px 12px 12px; background: #fff; color: #1f2f43; cursor: pointer; font: inherit; text-align: left; transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease; }
.internal-power-picker-card:hover { border-color: #72aef0; box-shadow: 0 10px 24px rgba(47, 123, 178, 0.12); transform: translateY(-1px); }
.internal-power-picker-card.selected { border-color: #6c46ff; background: linear-gradient(180deg, rgba(108, 70, 255, 0.07), #fff 42%); box-shadow: 0 10px 26px rgba(108, 70, 255, 0.16); }
.power-selected-mark { position: absolute; top: 8px; right: 8px; z-index: 1; border: 1px solid #cfd8e3; border-radius: 999px; padding: 3px 8px; background: rgba(255, 255, 255, 0.94); color: #7a8797; font-size: 11px; font-weight: 700; }
.internal-power-picker-card.selected .power-selected-mark { border-color: #6c46ff; background: #6c46ff; color: #fff; }
.picker-power-media { grid-row: 1 / span 2; width: 82px; aspect-ratio: 1; align-self: start; border: 1px solid #d7e4f2; border-radius: 8px; background: linear-gradient(135deg, #f4f7fb, #fff); display: grid; place-items: center; overflow: hidden; }
.picker-power-media img { width: 100%; height: 100%; object-fit: cover; }
.picker-power-media.empty span { color: #8a9aae; font-size: 11px; font-weight: 700; }
.picker-power-heading { align-self: end; min-width: 0; padding-right: 54px; }
.picker-power-heading strong { display: block; overflow: hidden; color: #14283f; font-size: 17px; text-overflow: ellipsis; white-space: nowrap; }
.picker-power-heading span { display: block; margin-top: 6px; overflow: hidden; color: #60748b; font-size: 12px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.picker-entry-list { grid-column: 1 / -1; display: flex; flex-wrap: wrap; align-content: flex-start; gap: 6px; min-height: 62px; }
.picker-entry-list span { border-radius: 4px; padding: 5px 7px; background: #edf4ff; color: #324b68; font-size: 12px; font-weight: 700; line-height: 1.25; }
.picker-entry-list span.ignored { background: #f2f3f5; color: #8a94a2; text-decoration: line-through; }
.picker-entry-list span.empty-entry { color: #97a4b4; text-decoration: none; }
.picker-power-benefit { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 5px 8px; padding-top: 10px; border-top: 1px solid #e5ebf1; color: #536b82; font-size: 11px; font-variant-numeric: tabular-nums; }
.picker-power-gain { grid-column: 1 / -1; color: #17664f; font-size: 14px; font-weight: 800; text-align: right; }
.power-total { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 20px; margin-top: 16px; padding: 16px; border-left: 4px solid #2f8467; background: #f2f8f5; color: #526176; }
.power-total b, .power-total strong { color: #16634e; }
.power-total strong { margin-left: auto; font-size: 18px; }
.section-title { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; }
.section-title > div { min-width: 0; }
.comparison-inputs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-top: 18px; }
.entry-set { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 16px; border: 1px solid #e1e7ef; }
.entry-heading { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.entry-set h3 { color: #305675; font-size: 15px; }
.entry-actions { display: flex; gap: 6px; }
.entry-actions :deep(.el-upload) { display: inline-flex; }
.plan-drop-hint { grid-column: 1 / -1; padding: 9px 10px; border: 1px dashed #cbd9e6; background: #f8fafc; color: #708196; font-size: 12px; }
.empty-calculator { display: grid; min-height: 360px; place-items: center; }
@media (max-width: 1180px) { .profession-bar { grid-template-columns: repeat(3, minmax(0, 1fr)); } .profession-actions { grid-column: 1 / -1; } .recommendation-editor, .internal-power-picker-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 980px) { .curve-grid, .calculator-grid, .comparison-inputs, .result-comparison { grid-template-columns: 1fr; } }
@media (max-width: 640px) { .page-header, .section-title, .template-toolbar, .power-dialog-toolbar { align-items: stretch; flex-direction: column; } .header-actions, .profession-actions { align-items: stretch; flex-direction: column; } .json-toolbar, .power-picker-actions { display: grid !important; grid-template-columns: 1fr; } .json-toolbar :deep(.el-button), .power-picker-actions :deep(.el-button) { margin-left: 0; } .panel-select, .power-search { width: 100%; } .profession-bar, .curve-point-input, .field-grid, .after-summary, .metric-grid, .detail-grid, .recommendations, .comparison-results, .entry-set, .internal-power-picker-grid { grid-template-columns: 1fr; } .profession-actions { grid-column: auto; } .power-total strong { margin-left: 0; } .recommendation-heading, .recommendation-result { align-items: flex-start; flex-direction: column; gap: 4px; } }
</style>
