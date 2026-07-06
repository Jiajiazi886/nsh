<template>
  <div class="app-container internal-power-page">
    <section class="power-hero">
      <div>
        <p class="eyebrow">Personal Codex · 内功册</p>
        <h1>内功管理</h1>
        <p>先把内功、词条和五行配比管理起来；随机数值与后端同步留给下一轮。</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="benefitMode" class="benefit-mode-select" placeholder="收益类型">
          <el-option
            v-for="item in benefitModeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-tag effect="plain" type="info">AI识图 {{ aiRecognitionQuotaLabel }}</el-tag>
        <el-tag v-if="backgroundRecognitionRunning" effect="plain" type="warning">后台识别中</el-tag>
        <el-badge :value="recognitionRecordBadge" :hidden="!recognitionItems.length" class="recognition-record-badge">
          <el-button plain @click="openRecognitionHistory">识别记录</el-button>
        </el-badge>
        <el-button plain @click="openRecognitionDialog">图片识别</el-button>
        <el-button v-if="canEditPowerValues" plain @click="openValueEditor">内功数值编辑</el-button>
        <el-button plain @click="resetSamples">重置示例</el-button>
        <el-button type="primary" :disabled="!canCreateMore" @click="createPower">新增内功</el-button>
      </div>
    </section>

    <section class="summary-grid">
      <article class="summary-card">
        <span>内功数量</span>
        <strong>{{ powers.length }}</strong>
        <small>{{ quotaSummaryText }}</small>
      </article>
      <article class="summary-card">
        <span>平均{{ benefitModeLabel }}</span>
        <strong>{{ averageBonus }}</strong>
        <small>{{ benefitModeHelpText }}</small>
      </article>
      <article class="summary-card">
        <span>词条总数</span>
        <strong>{{ totalEntries }}</strong>
        <small>可手动维护占位</small>
      </article>
      <article class="summary-card">
        <span>AI识图次数</span>
        <strong>{{ aiRecognitionQuotaValue }}</strong>
        <small>{{ aiRecognitionUnlimited ? '管理员不限次数' : '每张成功图片消耗 1 次' }}</small>
      </article>
      <article class="summary-card element-summary">
        <span>五行分布</span>
        <div class="element-strip">
          <i
            v-for="item in elementOptions"
            :key="item.key"
            :style="{ '--element-color': item.color, flexGrow: elementTotals[item.key] || 1 }"
          />
        </div>
        <small>{{ elementSummaryText }}</small>
      </article>
    </section>

    <section class="power-board" v-loading="pageLoading">
      <div class="board-header">
        <div class="panel-title">
          <div>
            <strong>内功库（{{ Math.max(filteredPowers.length, 20) }}个槽位）</strong>
        <span>{{ filteredPowers.length }} 个内功 · {{ limitText }}</span>
          </div>
        </div>

        <div class="filters">
          <el-input v-model.trim="filters.keyword" clearable placeholder="搜索内功名字" />
          <el-select v-model="filters.category" clearable placeholder="全部种类">
            <el-option
              v-for="item in categoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-select v-model="filters.element" clearable placeholder="包含元素">
            <el-option
              v-for="item in elementOptions"
              :key="item.key"
              :label="item.label"
              :value="item.key"
            />
          </el-select>
          <el-button v-if="canEditPowerValues" plain @click="openValueEditor">内功数值编辑</el-button>
          <el-button plain :disabled="!powers.length" @click="toggleBatchMode">
            {{ batchMode ? '退出批量' : '批量管理' }}
          </el-button>
          <el-button v-if="batchMode" plain :disabled="!filteredPowers.length" @click="toggleSelectAllFiltered">
            {{ isAllFilteredSelected ? '取消全选' : '全选当前' }}
          </el-button>
          <el-button v-if="batchMode" type="danger" plain :disabled="!selectedBatchPowers.length" @click="deleteBatchPowers">
            删除选中 {{ selectedBatchPowers.length }}
          </el-button>
          <el-button type="danger" plain :disabled="!powers.length" @click="clearAllPowers">清空内功</el-button>
          <el-button plain @click="resetSamples">重置示例</el-button>
          <el-button type="primary" :disabled="!canCreateMore" @click="createPower">新增内功</el-button>
        </div>
      </div>

      <div class="power-grid">
        <article
          v-for="item in filteredPowers"
          :key="item.id"
          class="power-card"
          :class="{ active: item.id === selectedId, 'batch-selected': isPowerSelected(item.id) }"
          @click="handleCardClick(item)"
        >
          <el-checkbox
            v-if="batchMode"
            class="batch-checkbox"
            :model-value="isPowerSelected(item.id)"
            @click.stop
            @change="togglePowerSelection(item.id)"
          />
          <button class="delete-card" type="button" @click.stop="deletePower(item)">×</button>
          <div class="score-badge" :title="getPowerBenefitTitle(item)">
            <strong>{{ formatBenefit(getPowerBenefit(item).totalGain) }}</strong>
            <span>基础：{{ formatBenefit(getPowerBenefit(item).baseGain) }}</span>
            <span>词条：{{ formatBenefit(getPowerBenefit(item).entryGain) }}</span>
          </div>

          <div class="card-center">
            <div class="power-card-media" :class="{ empty: !resolvePowerImage(item) }">
              <img v-if="resolvePowerImage(item)" :src="resolvePowerImage(item)" :alt="`${item.name || '内功'}图片`" />
              <span v-else>内功图片</span>
            </div>
            <h2>{{ item.name || '未命名内功' }}</h2>
            <p class="element-sequence" :title="formatElementCounts(item.elements)">
              {{ formatElementSequence(item.elements) }}
            </p>
            <div class="entry-pills">
              <span v-for="entry in item.entries" :key="entry.id" :title="getEntryBenefitTitle(entry)">{{ getEntryLabel(entry, item) }}</span>
              <span v-if="!item.entries?.length" class="muted">词条等待后期随机开发</span>
            </div>
          </div>
        </article>

        <button
          v-for="slot in emptySlots"
          :key="slot"
          type="button"
          class="empty-slot-card"
          :disabled="!canCreateMore"
          @click="createPower"
        >
          <span>+</span>
          <strong>空槽位</strong>
          <small>点击新增内功</small>
        </button>
      </div>

      <el-empty v-if="!filteredPowers.length && !emptySlots.length" description="没有匹配的内功" />
    </section>

    <el-dialog
      v-model="deleteConfirmVisible"
      :title="deleteConfirmTitle"
      width="420px"
      append-to-body
      destroy-on-close
      class="delete-confirm-dialog"
      @close="cancelDeleteConfirm"
    >
      <p class="delete-confirm-message">{{ deleteConfirmMessage }}</p>
      <el-checkbox v-model="deleteConfirmSkipForSession">本次登录不再提示删除确认</el-checkbox>
      <template #footer>
        <el-button @click="cancelDeleteConfirm">取消</el-button>
        <el-button type="danger" @click="acceptDeleteConfirm">确认删除</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="recognitionDialogVisible"
      title="内功图片识别"
      width="620px"
      append-to-body
      destroy-on-close
      class="recognition-dialog"
      @opened="focusRecognitionPasteTarget"
      @closed="resetRecognitionDialog"
    >
      <div class="recognition-panel" @paste="handleRecognitionDialogPaste">
        <el-alert
          title="识别结果只会生成草稿；确认导入并保存后，才会写入内功库。"
          type="info"
          show-icon
          :closable="false"
        />
        <div class="recognition-quota">
          <span>剩余次数</span>
          <strong>{{ aiRecognitionQuotaValue }}</strong>
          <small>{{ recognitionSelectionCostText }}</small>
        </div>
        <div class="recognition-background-toggle">
          <el-checkbox v-model="recognitionBackgroundMode">
            后台模式
          </el-checkbox>
          <span>{{ recognitionBackgroundMode ? backgroundRecognitionProgressText : '勾选后，拖入或选择图片会自动后台识别并新增内功。' }}</span>
        </div>
        <div
          ref="recognitionPasteTarget"
          class="recognition-paste-zone"
          tabindex="0"
          role="textbox"
          aria-label="粘贴内功截图"
          @click="focusRecognitionPasteTarget"
        >
          <strong>截图后直接 Ctrl+V</strong>
          <span>这里只接收剪贴板图片；后台模式开启时会自动识别并新增内功。</span>
        </div>
        <el-upload
          drag
          multiple
          accept="image/*"
          :auto-upload="false"
          :file-list="recognitionFileList"
          :on-change="handleRecognitionFileChange"
          :on-remove="handleRecognitionFileRemove"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">拖入内功截图，或 <em>点击选择图片</em></div>
          <template #tip>
            <div class="el-upload__tip">支持多张图片；每张图片消耗 1 次 AI 识图次数。</div>
          </template>
        </el-upload>
        <div v-if="recognitionItems.length" class="recognition-result-list">
          <article
            v-for="item in recognitionItems"
            :key="item.clientId"
            class="recognition-card"
            :class="{ failed: getRecognitionDisplayStatus(item) === 'failed', pending: isRecognitionPending(item) }"
          >
            <header>
              <div class="recognition-card-thumb" :class="{ empty: !internalPowerImageVisible || !item.imageUrl }">
                <img v-if="internalPowerImageVisible && item.imageUrl" :src="item.imageUrl" :alt="`${item.fileName}截图`" />
                <span v-else>无图</span>
              </div>
              <div>
                <strong>{{ item.fileName }}</strong>
                <span>{{ item.parsed?.内功名 || '未识别内功名' }}</span>
                <small v-if="getRecognizedElementLabel(item.parsed)" class="recognition-element-hint">
                  元素 {{ getRecognizedElementLabel(item.parsed) }}
                </small>
              </div>
              <el-tag :type="getRecognitionStatusType(item)" effect="plain">
                {{ getRecognitionStatusText(item) }}
              </el-tag>
            </header>
            <el-progress
              v-if="isRecognitionPending(item)"
              :percentage="getRecognitionProgressPercent(item)"
              :stroke-width="8"
              :show-text="false"
              striped
              striped-flow
            />
            <el-alert
              v-if="item.error"
              title="识别失败"
              :description="item.error"
              type="error"
              show-icon
              :closable="false"
            />
            <pre v-if="item.error" class="recognition-error-detail">{{ item.error }}</pre>
            <el-alert
              v-if="item.needsPresetSelection && !item.saved"
              title="需要选择元素"
              :description="item.presetSelectionMessage || '该内功存在多个元素，请选择元素后再新增'"
              type="warning"
              show-icon
              :closable="false"
            />
            <div v-if="item.success" class="recognition-candidate">
              <span>匹配预设</span>
              <el-select v-model="item.selectedPresetId" placeholder="请选择具体内功预设">
                <el-option
                  v-for="candidate in item.presetCandidates"
                  :key="candidate.presetId"
                  :label="candidate.displayName"
                  :value="candidate.presetId"
                />
              </el-select>
            </div>
            <div v-if="item.entries.length" class="recognition-entry-list">
              <div
                v-for="(entry, index) in item.entries"
                :key="`${item.clientId}-${index}`"
                class="recognition-entry-edit"
                :class="{ muted: entry.name === '灵韵' || !getEntryOption(entry.name) }"
              >
                <span class="recognition-entry-name">{{ entry.name || '未知词条' }}</span>
                <el-input-number
                  v-model="entry.value"
                  :min="0"
                  :max="getRecognitionEntryMax(entry)"
                  :precision="getRecognitionEntryPrecision(entry)"
                  controls-position="right"
                  :disabled="entry.name === '灵韵' || !getEntryOption(entry.name)"
                  size="small"
                />
                <span v-if="isPercentEntry(entry.name)" class="recognition-entry-suffix">%</span>
                <small>{{ getRecognitionEntryHint(entry) }}</small>
              </div>
            </div>
            <details v-if="item.rawText" class="recognition-raw">
              <summary>查看原始返回</summary>
              <pre>{{ item.rawText }}</pre>
            </details>
            <div v-if="item.success && (!item.background || item.needsPresetSelection)" class="recognition-card-actions">
              <el-button
                type="success"
                plain
                :loading="item.saving"
                :disabled="!item.selectedPresetId || item.saving || item.saved"
                @click="saveRecognizedPowerDirectly(item)"
              >
                {{ item.saved ? '已新增' : '直接新增内功' }}
              </el-button>
              <el-button
                type="primary"
                plain
                :disabled="!item.selectedPresetId || item.saving"
                @click="importRecognizedPower(item)"
              >
                导入为内功草稿
              </el-button>
            </div>
          </article>
        </div>
      </div>
      <template #footer>
        <el-button @click="recognitionDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="recognitionSubmitting"
          :disabled="recognitionBackgroundMode || !recognitionFileList.length || (!aiRecognitionUnlimited && recognitionFileList.length > aiRecognitionCount)"
          @click="submitRecognition"
        >
          {{ recognitionBackgroundMode ? '上传后自动识别' : '开始识别' }}
        </el-button>
      </template>
    </el-dialog>

    <el-drawer
      v-model="recognitionHistoryVisible"
      title="识别记录"
      size="min(720px, 96vw)"
      append-to-body
      class="recognition-history-drawer"
    >
      <div class="recognition-history" v-loading="recognitionHistoryInitialLoading">
        <div class="recognition-history-summary">
          <div>
            <span>总数</span>
            <strong>{{ recognitionRecordStats.total }}</strong>
          </div>
          <div>
            <span>进行中</span>
            <strong>{{ recognitionRecordStats.running }}</strong>
          </div>
          <div>
            <span>已新增</span>
            <strong>{{ recognitionRecordStats.saved }}</strong>
          </div>
          <div>
            <span>待入库</span>
            <strong>{{ recognitionRecordStats.needsPreset }}</strong>
          </div>
          <div>
            <span>失败</span>
            <strong>{{ recognitionRecordStats.failed }}</strong>
          </div>
        </div>
        <div class="recognition-history-actions">
          <span v-if="recognitionRecordStats.total" class="recognition-history-loaded">
            已加载 {{ recognitionRecordStats.loaded }} / {{ recognitionRecordStats.total }}
          </span>
          <el-button plain icon="Refresh" @click="openRecognitionDialog">继续识别</el-button>
          <el-button plain type="danger" :disabled="!recognitionRecordStats.total || recognitionHistoryLoading" @click="clearRecognitionHistory">清空记录</el-button>
        </div>
        <el-empty v-if="!recognitionItems.length" description="暂无识别记录" />
        <div v-else class="recognition-history-list">
          <article
            v-for="item in recognitionItems"
            :key="`history-${item.clientId}`"
            class="recognition-history-card"
            :class="{ failed: getRecognitionDisplayStatus(item) === 'failed', pending: isRecognitionPending(item) }"
          >
            <div class="recognition-history-thumb" :class="{ empty: !internalPowerImageVisible || !item.imageUrl }">
              <img v-if="internalPowerImageVisible && item.imageUrl" :src="item.imageUrl" :alt="`${item.fileName}截图`" />
              <span v-else>无图</span>
            </div>
            <div class="recognition-history-main">
              <header>
                <div>
                  <strong>{{ item.parsed?.内功名 || item.fileName }}</strong>
                  <span>{{ item.fileName }}</span>
                  <small v-if="getRecognizedElementLabel(item.parsed)" class="recognition-element-hint">
                    元素 {{ getRecognizedElementLabel(item.parsed) }}
                  </small>
                </div>
                <el-tag :type="getRecognitionStatusType(item)" effect="plain">
                  {{ getRecognitionStatusText(item) }}
                </el-tag>
              </header>
              <el-progress
                :percentage="getRecognitionProgressPercent(item)"
                :status="getRecognitionProgressStatus(item)"
                :stroke-width="8"
              />
              <div v-if="item.entries.length" class="recognition-history-entries">
                <span
                  v-for="entry in item.entries"
                  :key="`${item.clientId}-${entry.id}`"
                  :class="{ muted: entry.name === '灵韵' || !getEntryOption(entry.name) }"
                >
                  {{ entry.name || '未知词条' }} {{ formatRecognitionEntryValue(entry) }}
                </span>
              </div>
              <el-alert
                v-if="item.error"
                title="完整错误"
                :description="item.error"
                type="error"
                show-icon
                :closable="false"
              />
              <el-alert
                v-if="item.needsPresetSelection && !item.saved"
                title="待选择元素"
                :description="item.presetSelectionMessage || '该内功存在多个元素，请选择元素后再新增'"
                type="warning"
                show-icon
                :closable="false"
              />
              <pre v-if="item.error" class="recognition-error-detail">{{ item.error }}</pre>
              <details v-if="item.rawText" class="recognition-raw">
                <summary>查看原始返回</summary>
                <pre>{{ item.rawText }}</pre>
              </details>
            </div>
          </article>
          <div v-if="recognitionHistoryPager.hasNext" class="recognition-history-more">
            <el-button
              plain
              :loading="recognitionHistoryLoading"
              @click="loadMoreRecognitionHistory"
            >查看更多</el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="editingVisible"
      size="min(1080px, 96vw)"
      :with-header="false"
      append-to-body
      destroy-on-close
      class="power-editor-drawer"
    >
      <main class="editor-shell" v-if="draft">
        <header class="editor-topbar">
          <div>
            <span class="editor-kicker">{{ selectedPower ? '编辑内功' : '新增内功' }}</span>
            <h2>{{ draft.name || '未命名内功' }}</h2>
            <p>{{ editorStatusText }}</p>
          </div>
          <div class="editor-actions">
            <el-button plain @click="openJsonImportDialog">JSON导入</el-button>
            <el-button plain @click="duplicateSelected">复制</el-button>
            <el-button v-if="selectedPower" class="editor-delete-button" plain type="danger" @click="deleteSelected">删除内功</el-button>
            <button type="button" class="editor-close" @click="editingVisible = false">×</button>
          </div>
        </header>

        <div class="editor-layout">
          <el-form
            ref="formRef"
            :model="draft"
            :rules="rules"
            label-position="top"
            class="power-form"
          >
            <section class="editor-section">
              <div class="section-heading">
                <strong>基础信息</strong>
                <span>决定卡片标题、类型和主加成</span>
              </div>
              <div class="basic-grid">
                <el-form-item label="内功名字" prop="name">
                  <el-input v-model.trim="draft.name" maxlength="24" show-word-limit placeholder="例如：破晓" />
                </el-form-item>

                <el-form-item label="内功种类" prop="category">
                  <el-popover
                    v-model:visible="categoryPickerVisible"
                    trigger="click"
                    placement="bottom-start"
                    :width="380"
                    popper-class="power-category-popper"
                  >
                    <template #reference>
                      <button
                        type="button"
                        class="category-picker-trigger"
                        :class="{ empty: !selectedCategoryCatalog }"
                      >
                        <span class="category-picker-thumb" :class="{ empty: !resolveCatalogImage(selectedCategoryCatalog) }">
                          <img
                            v-if="resolveCatalogImage(selectedCategoryCatalog)"
                            :src="resolveCatalogImage(selectedCategoryCatalog)"
                            :alt="`${selectedCategoryCatalog?.name || '内功'}图片`"
                          />
                          <span v-else>图</span>
                        </span>
                        <span class="category-picker-main">
                          <strong>{{ selectedCategoryCatalog?.displayName || '请选择内功种类' }}</strong>
                          <small>{{ selectedCategoryCatalog ? formatCategoryMeta(selectedCategoryCatalog) : '按元素文件夹选择预设内功' }}</small>
                        </span>
                        <el-icon class="category-picker-caret"><ArrowDown /></el-icon>
                      </button>
                    </template>

                    <div class="power-category-tree">
                      <button
                        v-for="item in rootCategoryOptions"
                        :key="item.value"
                        type="button"
                        class="category-file-row root-file"
                        :class="{ active: draft.category === item.value }"
                        @click="selectCategoryPreset(item)"
                      >
                        <span class="category-file-thumb" :class="{ empty: !resolveCatalogImage(item) }">
                          <img v-if="resolveCatalogImage(item)" :src="resolveCatalogImage(item)" :alt="`${item.name}图片`" />
                          <span v-else>图</span>
                        </span>
                        <span class="category-file-main">
                          <strong>{{ item.displayName }}</strong>
                          <small>{{ formatCategoryMeta(item) }}</small>
                        </span>
                        <span class="category-file-bonus">{{ formatBonus(item.baseBonus) }}</span>
                      </button>

                      <section
                        v-for="folder in elementCategoryFolders"
                        :key="folder.key"
                        class="element-folder"
                        :class="{ collapsed: isElementFolderCollapsed(folder.key) }"
                      >
                        <button
                          type="button"
                          class="element-folder-header"
                          :aria-expanded="!isElementFolderCollapsed(folder.key)"
                          @click="toggleElementFolder(folder.key)"
                        >
                          <span class="element-folder-left">
                            <el-icon class="element-folder-caret"><ArrowRightBold /></el-icon>
                            <el-icon class="element-folder-icon" :style="{ color: folder.color }">
                              <Folder v-if="isElementFolderCollapsed(folder.key)" />
                              <FolderOpened v-else />
                            </el-icon>
                            <strong>{{ folder.label }}元素</strong>
                          </span>
                          <span class="element-folder-count">{{ folder.items.length }}</span>
                        </button>

                        <div v-show="!isElementFolderCollapsed(folder.key)" class="element-folder-body">
                          <button
                            v-for="item in folder.items"
                            :key="item.value"
                            type="button"
                            class="category-file-row"
                            :class="{ active: draft.category === item.value }"
                            @click="selectCategoryPreset(item)"
                          >
                            <span class="category-file-thumb" :class="{ empty: !resolveCatalogImage(item) }">
                              <img v-if="resolveCatalogImage(item)" :src="resolveCatalogImage(item)" :alt="`${item.name}图片`" />
                              <span v-else>图</span>
                            </span>
                            <span class="category-file-main">
                              <strong>{{ item.displayName }}</strong>
                              <small>{{ formatCategoryMeta(item) }}</small>
                            </span>
                            <span class="category-file-bonus">{{ formatBonus(item.baseBonus) }}</span>
                          </button>
                        </div>
                      </section>
                    </div>
                  </el-popover>
                </el-form-item>

                <el-form-item label="基础百分比增伤" prop="bonusPercent">
                  <div class="bonus-editor">
                    <el-slider v-model="draft.bonusPercent" :min="0" :max="100" :step="0.1" />
                    <el-input-number v-model="draft.bonusPercent" :min="0" :max="100" :precision="1" controls-position="right" />
                  </div>
                </el-form-item>
                <el-form-item label="灵韵">
                  <div class="lingyun-editor">
                    <el-checkbox v-model="draft.lingyunEnabled">启用灵韵</el-checkbox>
                    <span>灵韵增益 {{ formatBonus(draft.lingyunBonusPercent) }}</span>
                  </div>
                </el-form-item>
              </div>
            </section>

            <section class="editor-section">
              <div class="section-heading">
                <strong>五行元素</strong>
                <span>{{ formatElementCounts(draft.elements) }}</span>
              </div>
              <div class="elements-editor">
                <div class="element-total" :class="{ invalid: !isElementTotalValid }">
                  <span>当前 {{ elementTotal }} / {{ expectedElementTotal }}</span>
                  <strong>{{ isElementTotalValid ? '配比完整' : `必须符合 ${expectedElementTotal} 个元素` }}</strong>
                </div>
                <div class="element-controls">
                  <div
                    v-for="item in elementOptions"
                    :key="item.key"
                    class="element-control"
                    :style="{ '--element-color': item.color, '--element-bg': item.bg }"
                  >
                    <span>{{ item.label }}</span>
                    <div>
                      <el-button size="small" circle @click="changeElement(item.key, -1)">-</el-button>
                      <strong>{{ draft.elements[item.key] || 0 }}</strong>
                      <el-button size="small" circle @click="changeElement(item.key, 1)">+</el-button>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section class="editor-section">
              <div class="section-heading">
                <div>
                  <strong>内功词条</strong>
                  <span>{{ draft.entries.length || 0 }} 条 · 行内显示当前收益</span>
                </div>
                <el-button size="small" plain :disabled="!entryOptions.length" @click="addEntry">添加词条</el-button>
              </div>
              <div class="entries-editor">
                <div v-if="draft.entries.length" class="entry-table-head">
                  <span>词条</span>
                  <span>数值</span>
                  <span>收益</span>
                  <span>操作</span>
                </div>
                <div
                  v-for="(entry, index) in draft.entries"
                  :key="entry.id"
                  class="entry-row"
                >
                  <el-select v-model="entry.name" filterable placeholder="请选择词条">
                    <el-option
                      v-for="item in entryOptions"
                      :key="item.entryName"
                      :label="formatEntryOptionLabel(item)"
                      :value="item.entryName"
                    />
                  </el-select>
                  <div class="entry-value-control">
                    <el-input-number
                      v-model="entry.value"
                      :min="0"
                      :max="getEntryLimitValue(entry.name)"
                      :precision="getEntryPrecision(entry.name)"
                      controls-position="right"
                      placeholder="词条数值"
                    />
                    <span v-if="isPercentEntry(entry.name)" class="entry-value-suffix">%</span>
                  </div>
                  <span class="entry-row-benefit" :title="getEntryLimitHint(entry)">
                    {{ formatBenefit(getSingleEntryBenefit(entry)) }}
                  </span>
                  <el-button text type="danger" @click="removeEntry(index)">删除</el-button>
                </div>
                <p v-if="!draft.entries.length" class="placeholder-note">暂无词条，等待后期随机开发。</p>
                <p v-if="!entryOptions.length" class="placeholder-note">暂无启用词条，请联系管理员检查内置词条配置。</p>
              </div>
            </section>

            <section class="editor-section">
              <el-form-item label="备注">
                <el-input
                  v-model.trim="draft.remark"
                  type="textarea"
                  :rows="3"
                  maxlength="160"
                  show-word-limit
                  placeholder="记录这套内功适合什么玩法。"
                />
              </el-form-item>
            </section>
          </el-form>

          <aside class="preview-panel">
            <div class="preview-card game-detail-card">
              <div class="game-card-bg" />
              <header class="game-card-head">
                <div class="preview-image game-card-icon" :class="{ empty: !resolvePowerImage(draft) }">
                  <img v-if="resolvePowerImage(draft)" :src="resolvePowerImage(draft)" :alt="`${draft.name || '内功'}图片`" />
                  <span v-else>内功</span>
                </div>
                <div class="game-card-title">
                  <h2>{{ draft.name || '未命名内功' }}</h2>
                  <p>
                    <span>评分 +{{ getPreviewScore(draft) }}</span>
                    <b>+{{ Math.round(getBaseBonus(draft) * 5) }}</b>
                  </p>
                </div>
                <span class="game-card-equip">装配</span>
              </header>

              <div class="game-card-tags">
                <span>{{ selectedCategoryCatalog?.rarity === 'rare' ? '稀有' : '通用' }}</span>
                <span>{{ getPrimaryEntryTag(draft) }}</span>
                <div class="game-card-marks">
                  <i
                    v-for="item in previewElementMarks(draft.elements)"
                    :key="item.key"
                    :style="{ '--element-color': item.color }"
                  />
                </div>
              </div>

              <div class="game-card-divider" />

              <section class="game-benefit-row">
                <span>◆ {{ benefitModeLabel }}</span>
                <strong>{{ formatBenefit(getPowerBenefit(draft).totalGain) }}</strong>
              </section>

              <section class="game-collapse">
                <button type="button" class="game-collapse-head" @click="previewTraitExpanded = !previewTraitExpanded">
                  <span>
                    <el-icon :class="{ expanded: previewTraitExpanded }"><ArrowRightBold /></el-icon>
                    特性
                    <b>{{ selectedCategoryCatalog?.rarity === 'rare' ? '稀' : '普' }}</b>
                  </span>
                </button>
                <div v-show="previewTraitExpanded" class="game-trait-body">
                  {{ getPowerTraitText(draft) }}
                </div>
              </section>

              <section class="game-collapse">
                <button type="button" class="game-collapse-head" @click="previewEntriesExpanded = !previewEntriesExpanded">
                  <span>
                    <el-icon :class="{ expanded: previewEntriesExpanded }"><ArrowRightBold /></el-icon>
                    属性加成
                  </span>
                  <strong>{{ draft.entries.length || 0 }} 条</strong>
                </button>
                <div v-show="previewEntriesExpanded" class="game-entry-list">
                  <div
                    v-for="row in getEntryPreviewRows(draft)"
                    :key="row.key"
                    class="game-entry-row"
                    :class="{ base: row.type === 'base' }"
                    :title="row.note"
                  >
                    <span>{{ row.name }}</span>
                    <em>{{ row.value }}</em>
                    <strong>{{ row.benefit }}</strong>
                  </div>
                  <div v-if="!draft.entries.length" class="game-entry-empty">词条等待后期随机开发</div>
                </div>
              </section>

              <div class="game-element-strip">
                <span
                  v-for="item in elementOptions"
                  :key="item.key"
                  :style="{ '--element-color': item.color }"
                >
                  {{ item.label }}{{ draft.elements[item.key] || 0 }}
                </span>
              </div>
            </div>
            <div class="editor-note-card">
              <strong>卡片预览</strong>
              <span>点击特性或属性加成可展开/隐藏详情，保存后同步到内功库卡片墙。</span>
            </div>
          </aside>
        </div>

        <footer class="editor-footer">
          <span>{{ footerStatusText }}</span>
          <div>
            <el-button @click="restoreDraft">撤销改动</el-button>
            <el-button type="primary" :disabled="!canSave" @click="saveDraft">保存内功</el-button>
          </div>
        </footer>
      </main>
    </el-drawer>

    <el-dialog v-model="jsonImportDialog.open" title="JSON导入内功" width="620px" append-to-body>
      <el-input
        v-model="jsonImportDialog.text"
        type="textarea"
        :rows="12"
        placeholder='粘贴识别原始JSON，例如 {"内功名":"鲸落","元素":"水","属性加成":[{"词条":"气血上限","数值":991}]}'
      />
      <template #footer>
        <el-button @click="jsonImportDialog.open = false">取消</el-button>
        <el-button type="primary" @click="submitJsonImportDialog">导入为草稿</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="valueEditorVisible"
      title="内功数值编辑"
      width="min(1120px, 96vw)"
      append-to-body
      class="power-value-dialog"
    >
      <div class="value-editor-intro">
        <div>
          <strong>新赛年内功种类与基础增伤</strong>
          <span>这些数值只表示内功本体固定基础增伤，不包含随机词条。当前保存在本机浏览器，后续可迁移到后端。</span>
        </div>
        <div class="value-editor-actions">
          <el-button plain @click="addCatalogRow">新增种类</el-button>
          <el-button plain @click="resetCatalogDraft">恢复默认</el-button>
        </div>
      </div>

      <div class="catalog-table">
        <div class="catalog-head">
          <span>内功种类</span>
          <span>赛年</span>
          <span>级别</span>
          <span>推荐元素</span>
          <span>基础增伤</span>
          <span>特性</span>
          <span>操作</span>
        </div>
        <div v-for="(item, index) in catalogDraft" :key="item.id" class="catalog-row">
          <el-input v-model.trim="item.name" placeholder="内功名" />
          <el-tag effect="plain" type="success">新赛年</el-tag>
          <el-select v-model="item.rarity" placeholder="级别">
            <el-option label="稀有" value="rare" />
            <el-option label="普通" value="common" />
          </el-select>
          <el-select v-model="item.primaryElement" placeholder="元素">
            <el-option label="不限定" value="mixed" />
            <el-option
              v-for="element in elementOptions"
              :key="element.key"
              :label="element.label"
              :value="element.key"
            />
          </el-select>
          <el-input-number v-model="item.baseBonus" :min="0" :max="100" :precision="1" controls-position="right" />
          <el-input v-model.trim="item.trait" placeholder="例如：偏爆发 / 通用增伤" />
          <el-button text type="danger" @click="removeCatalogRow(index)">删除</el-button>
        </div>
      </div>

      <template #footer>
        <div class="value-dialog-footer">
          <span>保存后，新建内功和切换种类会自动带出基础增伤。</span>
          <div>
            <el-button @click="valueEditorVisible = false">取消</el-button>
            <el-button type="primary" @click="saveCatalogDraft">保存配置</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { ArrowDown, ArrowRightBold, Folder, FolderOpened } from '@element-plus/icons-vue'
import useUserStore from '@/store/modules/user'
import internalPowerRecognitionPrompt from '@/assets/prompts/internal-power-recognition.md?raw'
import {
  addInternalPower,
  deleteInternalPower,
  clearInternalPowerRecognitionHistory,
  importLocalInternalPowers,
  listInternalPowerEntries,
  listInternalPowers,
  listInternalPowerRecognitionHistory,
  listInternalPowerPresets,
  markInternalPowerRecognitionHistorySaved,
  recognizeInternalPowerImage,
  updateInternalPower
} from '@/api/personal/internalPower'
import { getInternalPowerPanelSetting } from '@/api/personal/internalPowerPanel'
import { getActiveFormulaVersion } from '@/api/system/formulaDesign'
import { getInternalPowerImageDisplayStatus } from '@/api/system/internalPowerImageDisplay'
import {
  calculateEntryBenefit,
  calculatePowerBenefit,
  createDefaultPanelSetting,
  FORMULA_SCOPE_INTERNAL_POWER_PVP,
  formatBenefitPercent,
  normalizePanelSetting,
  setActiveFormulaPackage
} from '@/utils/internalPowerBenefit'
import { getInternalPowerTraitEffect } from '@/utils/internalPowerTraits'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const powers = ref([])
const quota = ref({ count: 0, maxCount: 20, unlimited: false, isVip: '0', vipExpireTime: null })
const pageLoading = ref(false)
const selectedId = ref('')
const batchMode = ref(false)
const selectedBatchIds = ref([])
const draft = ref(null)
const savedDraftSignature = ref('')
const editingVisible = ref(false)
const valueEditorVisible = ref(false)
const categoryPickerVisible = ref(false)
const previewTraitExpanded = ref(false)
const previewEntriesExpanded = ref(true)
const collapsedElementFolders = ref(new Set())
const powerCatalog = ref([])
const internalPowerImageVisible = ref(true)
const entryOptions = ref([])
const entryConversion = ref({ unitPercent: 0, entries: [] })
const panelSetting = ref(createDefaultPanelSetting())
const benefitMode = ref('defense')
const catalogDraft = ref([])
const baseApi = import.meta.env.VITE_APP_BASE_API
const deleteConfirmVisible = ref(false)
const deleteConfirmTitle = ref('删除内功')
const deleteConfirmMessage = ref('')
const deleteConfirmSkipForSession = ref(false)
const deleteConfirmResolve = ref(null)
const recognitionDialogVisible = ref(false)
const recognitionHistoryVisible = ref(false)
const recognitionHistoryLoading = ref(false)
const recognitionHistoryInitialLoading = ref(false)
const recognitionHistoryPager = reactive({
  pageNum: 1,
  pageSize: 10,
  total: 0,
  hasNext: false
})
const recognitionFileList = ref([])
const recognitionSubmitting = ref(false)
const recognitionItems = ref([])
const recognitionBackgroundMode = ref(true)
const backgroundRecognitionRunning = ref(false)
const backgroundRecognitionFileUids = ref(new Set())
const recognitionPasteTarget = ref(null)
const recognitionObjectUrls = new Set()
let recognitionHistoryPollTimer = null
const jsonImportDialog = reactive({
  open: false,
  text: ''
})

const filters = reactive({
  keyword: '',
  category: '',
  element: ''
})

const benefitModeOptions = [
  { value: 'defense', label: '数值收益', help: '按当前面板动态计算' },
  { value: 'tower', label: '拆塔收益', help: '暂未接入拆塔计算逻辑' }
]

const elementOptions = [
  { key: 'metal', label: '金', color: '#c7922e', bg: 'rgba(199, 146, 46, 0.14)' },
  { key: 'wood', label: '木', color: '#2f8f55', bg: 'rgba(47, 143, 85, 0.14)' },
  { key: 'water', label: '水', color: '#2776c7', bg: 'rgba(39, 118, 199, 0.14)' },
  { key: 'fire', label: '火', color: '#d74b37', bg: 'rgba(215, 75, 55, 0.14)' },
  { key: 'earth', label: '土', color: '#8c6a3e', bg: 'rgba(140, 106, 62, 0.16)' }
]

const recognizedRarePowerNameMap = {
  日月两仪: '稀有-日月两仪',
  '稀有-日月两仪': '稀有-日月两仪',
  不动明王: '稀有-不动明王',
  '稀有-不动明王': '稀有-不动明王',
  绝电惊沙: '稀有-绝电惊沙',
  '稀有-绝电惊沙': '稀有-绝电惊沙',
  承影锋烁: '稀有-承影锋烁',
  '稀有-承影锋烁': '稀有-承影锋烁',
  灼星贯日: '稀有-灼星贯日',
  '稀有-灼星贯日': '稀有-灼星贯日'
}

const recognizedElementAliases = {
  metal: 'metal',
  gold: 'metal',
  jin: 'metal',
  金: 'metal',
  wood: 'wood',
  mu: 'wood',
  木: 'wood',
  water: 'water',
  shui: 'water',
  水: 'water',
  fire: 'fire',
  huo: 'fire',
  火: 'fire',
  earth: 'earth',
  soil: 'earth',
  tu: 'earth',
  土: 'earth',
  mixed: 'mixed',
  all: 'mixed',
  金木水火土: 'mixed',
  五行: 'mixed',
  全元素: 'mixed'
}

const rules = {
  name: [{ required: true, message: '内功名字不能为空', trigger: 'blur' }],
  category: [{ required: true, message: '请选择内功种类', trigger: 'change' }],
  bonusPercent: [{ required: true, message: '百分比加成不能为空', trigger: 'blur' }]
}

const storageKey = computed(() => {
  if (!userStore.id) return ''
  return `personal-skill:internal-powers:v1:${userStore.id}`
})
const migrationKey = computed(() => {
  if (!userStore.id) return ''
  return `personal-skill:migrated-to-backend:v1:${userStore.id}`
})
const deleteConfirmSkipKey = computed(() => {
  if (!userStore.id) return ''
  return `personal-skill:skip-delete-confirm:v1:${userStore.id}`
})
const canEditPowerValues = computed(() => false)
const aiRecognitionNormalCount = computed(() => Number(userStore.aiImageRecognitionCount || 0))
const aiRecognitionVipCount = computed(() => Number(userStore.vipAiImageRecognitionCount || 0))
const aiRecognitionCount = computed(() => aiRecognitionNormalCount.value + aiRecognitionVipCount.value)
const aiRecognitionUnlimited = computed(() => {
  return (userStore.roles || []).includes('admin') || (userStore.permissions || []).includes('*:*:*')
})
const aiRecognitionQuotaValue = computed(() => aiRecognitionUnlimited.value ? '不限' : aiRecognitionCount.value)
const aiRecognitionQuotaLabel = computed(() => {
  if (aiRecognitionUnlimited.value) return '管理员不限'
  if (aiRecognitionVipCount.value > 0) {
    return `剩余 ${aiRecognitionCount.value} 次（VIP ${aiRecognitionVipCount.value} / 普通 ${aiRecognitionNormalCount.value}）`
  }
  return `剩余 ${aiRecognitionNormalCount.value} 次`
})
const recognitionSelectionCostText = computed(() => {
  if (aiRecognitionUnlimited.value) return `已选择 ${recognitionFileList.value.length} 张，管理员识别不扣次数`
  return `已选择 ${recognitionFileList.value.length} 张，成功识别将消耗对应次数`
})
const recognitionRecordStats = computed(() => {
  const items = recognitionItems.value
  const saved = items.filter(item => getRecognitionDisplayStatus(item) === 'saved').length
  const needsPreset = items.filter(item => getRecognitionDisplayStatus(item) === 'needs_preset').length
  return {
    total: recognitionHistoryPager.total || items.length,
    loaded: items.length,
    running: items.filter(isRecognitionPending).length,
    saved,
    needsPreset,
    success: saved,
    failed: items.filter(item => getRecognitionDisplayStatus(item) === 'failed').length
  }
})
const recognitionRecordBadge = computed(() => {
  if (recognitionRecordStats.value.running) return recognitionRecordStats.value.running
  return recognitionRecordStats.value.total
})
const backgroundRecognitionProgressText = computed(() => {
  const items = recognitionItems.value.filter(item => item.background)
  if (!items.length) return '后台模式已开启：拖入或选择图片后会自动识别。'
  const running = items.filter(isRecognitionPending).length
  const saved = items.filter(item => getRecognitionDisplayStatus(item) === 'saved').length
  const selection = items.filter(item => getRecognitionDisplayStatus(item) === 'needs_preset').length
  const failed = items.filter(item => getRecognitionDisplayStatus(item) === 'failed').length
  return `后台进度：共 ${items.length} 张，进行中 ${running} 张，已新增 ${saved} 个，待选择 ${selection} 张，失败 ${failed} 张。`
})
const canCreateMore = computed(() => quota.value.unlimited || powers.value.length < Number(quota.value.maxCount || 20))
const limitText = computed(() => quota.value.unlimited ? `${powers.value.length} 个已保存 · 不限上限` : `${powers.value.length}/${quota.value.maxCount || 20} 个已保存`)
const quotaSummaryText = computed(() => {
  if (quota.value.unlimited) return quota.value.isVip === '1' ? 'VIP不限内功数' : '管理员不限内功数'
  return `后端保存 · 上限 ${quota.value.maxCount || 20}`
})

const categoryOptions = computed(() => {
  const options = powerCatalog.value.map(item => ({
    label: `${item.displayName || item.name} · ${formatBonus(item.baseBonus)}`,
    value: item.value
  }))
  const existingCategories = powers.value
    .map(item => item.category)
    .filter(Boolean)
    .filter(category => !powerCatalog.value.some(item => item.value === category))
    .map(category => ({ label: `${category} · 自定义`, value: category }))
  return [...options, ...existingCategories]
})
const selectedCategoryCatalog = computed(() => draft.value ? getCatalogByName(draft.value.category) : null)
const rootCategoryOptions = computed(() => powerCatalog.value.filter(item => item.elementKey === 'mixed'))
const elementCategoryFolders = computed(() => {
  return elementOptions
    .map(element => ({
      ...element,
      items: powerCatalog.value.filter(item => item.elementKey === element.key)
    }))
    .filter(folder => folder.items.length)
})

const filteredPowers = computed(() => {
  const keyword = filters.keyword.toLowerCase()
  return powers.value
    .filter(item => {
      const matchKeyword = !keyword || item.name.toLowerCase().includes(keyword) || item.categoryTrait.toLowerCase().includes(keyword)
      const matchCategory = !filters.category || item.category === filters.category
      const matchElement = !filters.element || Number(item.elements?.[filters.element] || 0) > 0
      return matchKeyword && matchCategory && matchElement
    })
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
})

const selectedPower = computed(() => powers.value.find(item => item.id === selectedId.value) || null)
const selectedBatchPowers = computed(() => powers.value.filter(item => selectedBatchIds.value.includes(item.id)))
const isAllFilteredSelected = computed(() => {
  return !!filteredPowers.value.length && filteredPowers.value.every(item => selectedBatchIds.value.includes(item.id))
})
const elementTotal = computed(() => sumElements(draft.value?.elements))
const expectedElementTotal = computed(() => {
  const catalog = draft.value ? getCatalogByName(draft.value.category) : null
  return catalog?.elementKey === 'mixed' ? 5 : 4
})
const isElementTotalValid = computed(() => {
  if (!draft.value) return false
  const catalog = getCatalogByName(draft.value.category)
  if (catalog?.elementKey === 'mixed') {
    return elementTotal.value === 5 && elementOptions.every(item => Number(draft.value.elements[item.key] || 0) === 1)
  }
  if (catalog?.elementKey) {
    return elementTotal.value === 4 && Number(draft.value.elements[catalog.elementKey] || 0) === 4
  }
  return elementTotal.value === 4 || elementTotal.value === 5
})
const canSave = computed(() => draft.value && isElementTotalValid.value)
const isDirty = computed(() => draft.value && savedDraftSignature.value !== JSON.stringify(draft.value))
const editorStatusText = computed(() => {
  if (!selectedPower.value) {
    return isDirty.value ? '新建内功有未保存内容' : '新建内功，保存后进入卡片墙'
  }
  return isDirty.value ? '有未保存改动，保存后同步到卡片墙' : '已保存到后端内功库'
})
const footerStatusText = computed(() => {
  if (!canSave.value) return `五行数量未满足 ${expectedElementTotal.value} 个`
  return selectedPower.value ? '可以保存当前改动' : '保存后新增到内功库'
})
const activeBenefitModeOption = computed(() => {
  return benefitModeOptions.find(item => item.value === benefitMode.value) || benefitModeOptions[0]
})
const benefitModeLabel = computed(() => activeBenefitModeOption.value.label)
const benefitModeHelpText = computed(() => activeBenefitModeOption.value.help)
const emptySlots = computed(() => {
  const visibleSlots = quota.value.unlimited ? Math.max(20, filteredPowers.value.length + 1) : Math.max(20, quota.value.maxCount || 20)
  const slotCount = Math.max(0, visibleSlots - filteredPowers.value.length)
  return Array.from({ length: slotCount }, (_, index) => `slot-${index}`)
})

const averageBonus = computed(() => {
  if (!powers.value.length) return '+0.00000%'
  const total = powers.value.reduce((sum, item) => sum + getPowerBenefit(item).totalGain, 0)
  return formatBenefit(total / powers.value.length)
})

const totalEntries = computed(() => powers.value.reduce((sum, item) => sum + (item.entries?.length || 0), 0))

const entryOptionMap = computed(() => {
  return entryOptions.value.reduce((map, item) => {
    map[item.entryName] = item
    return map
  }, {})
})

const entryConversionMap = computed(() => {
  return (entryConversion.value.entries || []).reduce((map, item) => {
    map[item.entryName] = item
    return map
  }, {})
})

const elementTotals = computed(() => {
  const totals = createEmptyElements()
  powers.value.forEach(item => {
    elementOptions.forEach(element => {
      totals[element.key] += Number(item.elements?.[element.key] || 0)
    })
  })
  return totals
})

const elementSummaryText = computed(() => {
  return elementOptions.map(item => `${item.label}${elementTotals.value[item.key] || 0}`).join(' / ')
})

onMounted(async () => {
  await loadImageDisplayStatus()
  await loadActiveFormulaPackage()
  await loadPowerCatalog()
  await loadEntryOptions()
  await loadPanelSetting()
  await loadPowers()
  consumeSkillRouteAction(route.query.action)
})

onBeforeUnmount(() => {
  stopRecognitionHistoryPolling()
  revokeRecognitionObjectUrls()
})

watch(recognitionBackgroundMode, enabled => {
  if (enabled) {
    enqueueBackgroundRecognitionFromUploadItems(recognitionFileList.value)
  }
})

watch(recognitionHistoryVisible, visible => {
  if (visible) {
    void refreshRecognitionHistory({ force: true, reset: true })
    startRecognitionHistoryPolling()
  } else {
    stopRecognitionHistoryPolling()
  }
})

watch(
  () => route.query.action,
  action => consumeSkillRouteAction(action)
)

async function loadImageDisplayStatus() {
  try {
    const response = await getInternalPowerImageDisplayStatus()
    internalPowerImageVisible.value = response.data?.enabled !== false
  } catch {
    internalPowerImageVisible.value = true
  }
}

async function loadActiveFormulaPackage() {
  try {
    const response = await getActiveFormulaVersion(FORMULA_SCOPE_INTERNAL_POWER_PVP)
    setActiveFormulaPackage(response.data?.formulaPackage || null)
  } catch (error) {
    setActiveFormulaPackage(null)
    ElMessage.warning('公式配置加载失败，已使用内置公式计算收益')
    console.warn('公式配置加载失败，已使用内置公式计算收益', error)
  }
}

async function loadPowerCatalog() {
  try {
    const response = await listInternalPowerPresets()
    powerCatalog.value = (response.presets || response.data || []).map(normalizeCatalogItem)
  } catch {
    powerCatalog.value = []
    ElMessage.error('内功预设加载失败，请联系管理员检查系统内功信息管理')
  }
}

async function loadEntryOptions() {
  try {
    const response = await listInternalPowerEntries()
    entryOptions.value = (response.entries || response.data || []).map(normalizeEntryOption).filter(item => item.entryName && item.entryName !== '灵韵')
  } catch {
    entryOptions.value = []
    ElMessage.error('内功词条加载失败，请联系管理员检查内置词条配置')
  }
}

async function loadEntryConversion() {
  // 旧接口保留给历史菜单缓存，当前收益由面板设置 + Excel 公式引擎计算。
  entryConversion.value = { unitPercent: 0, entries: [] }
}

async function loadPanelSetting() {
  try {
    const response = await getInternalPowerPanelSetting()
    panelSetting.value = normalizePanelSetting(response.data || response)
  } catch {
    panelSetting.value = createDefaultPanelSetting()
    console.warn('内功面板设置加载失败，已使用默认面板计算收益')
  }
}

function persistPowerCatalog() {
  // 内功预设已迁移到后端系统管理，此处保留空函数兼容旧入口。
}

async function loadPowers() {
  pageLoading.value = true
  try {
    const response = await listInternalPowers()
    applyPowerResponse(response)
    await migrateLocalPowersIfNeeded(response.powers || [])
  } catch (error) {
    ElMessage.error('内功列表加载失败，请稍后重试')
  } finally {
    pageLoading.value = false
  }
}

function isLegacySampleLibrary(items = []) {
  const legacyCategories = new Set(['攻击', '防御', '治疗', '通用'])
  const hasNewSeasonCategory = items.some(item => powerCatalog.value.some(catalog => catalog.value === item.category))
  const hasLegacyCategory = items.some(item => legacyCategories.has(item.category))
  return hasLegacyCategory && !hasNewSeasonCategory
}

function isGeneratedSampleLibrary(items = []) {
  return items.length > 0 && items.every(item => String(item.id || '').startsWith('sample-'))
}

async function migrateLocalPowersIfNeeded(serverPowers = []) {
  if (!userStore.id || !migrationKey.value || !storageKey.value) return
  if (localStorage.getItem(migrationKey.value) === '1') return
  if (serverPowers.length) {
    localStorage.setItem(migrationKey.value, '1')
    return
  }
  let localPowers = []
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey.value) || '[]')
    if (Array.isArray(stored) && stored.length) {
      const normalized = stored.map(normalizePower)
      localPowers = (isLegacySampleLibrary(normalized) || isGeneratedSampleLibrary(normalized)) ? [] : normalized
    }
  } catch {
    localPowers = []
  }
  if (!localPowers.length) {
    localStorage.setItem(migrationKey.value, '1')
    return
  }
  const response = await importLocalInternalPowers(localPowers.map(toPowerPayload))
  applyPowerResponse(response)
  localStorage.setItem(migrationKey.value, '1')
}

function applyPowerResponse(response = {}) {
  powers.value = (response.powers || []).map(normalizePower)
  quota.value = {
    count: response.quota?.count ?? powers.value.length,
    maxCount: response.quota?.maxCount ?? 20,
    unlimited: !!response.quota?.unlimited,
    isVip: response.quota?.isVip || '0',
    vipExpireTime: response.quota?.vipExpireTime || null
  }
}

function updateQuotaCount() {
  quota.value = {
    ...quota.value,
    count: powers.value.length
  }
}

function openRecognitionDialog() {
  recognitionDialogVisible.value = true
  recognitionBackgroundMode.value = true
  focusRecognitionPasteTarget()
}

function openRecognitionHistory() {
  const wasVisible = recognitionHistoryVisible.value
  recognitionHistoryVisible.value = true
  if (wasVisible) {
    void refreshRecognitionHistory({ force: true, reset: true })
  }
}

function consumeSkillRouteAction(action) {
  const actionName = Array.isArray(action) ? action[0] : action
  if (!actionName) return

  nextTick(() => {
    if (actionName === 'recognize') {
      openRecognitionDialog()
    } else if (actionName === 'history') {
      openRecognitionHistory()
    } else if (actionName === 'create') {
      createPower()
    }

    const nextQuery = { ...route.query }
    delete nextQuery.action
    router.replace({ path: route.path, query: nextQuery })
  })
}

function getRecognitionHistoryPayload(response = {}) {
  return response.data && Array.isArray(response.data.items) ? response.data : response
}

function updateRecognitionHistoryPager(payload = {}, requestedPage = 1) {
  recognitionHistoryPager.pageNum = Number(payload.pageNum || requestedPage || 1)
  recognitionHistoryPager.pageSize = Number(payload.pageSize || recognitionHistoryPager.pageSize || 10)
  recognitionHistoryPager.total = Number(payload.total ?? 0)
  recognitionHistoryPager.hasNext = !!payload.hasNext
}

function mergeRecognitionHistoryItems(currentItems = [], nextItems = []) {
  const merged = []
  const seen = new Set()
  ;[...currentItems, ...nextItems].forEach(item => {
    const key = item.recordId ? `record-${item.recordId}` : `client-${item.clientId}`
    if (seen.has(key)) return
    seen.add(key)
    merged.push(item)
  })
  return merged
}

async function refreshRecognitionHistory(options = {}) {
  if (recognitionHistoryLoading.value && !options.force) return
  const requestedPage = Number(options.pageNum || (options.append ? recognitionHistoryPager.pageNum + 1 : 1))
  const showLoading = !options.silent
  recognitionHistoryLoading.value = true
  if (showLoading) {
    recognitionHistoryInitialLoading.value = true
  }
  try {
    const response = await listInternalPowerRecognitionHistory({
      pageNum: requestedPage,
      pageSize: recognitionHistoryPager.pageSize
    })
    const payload = getRecognitionHistoryPayload(response)
    const serverItems = normalizeRecognitionHistoryItems(payload.items || [])
    const pendingLocalItems = recognitionItems.value.filter(item => isRecognitionPending(item) && !item.recordId)
    const existingServerItems = options.append
      ? recognitionItems.value.filter(item => item.recordId)
      : []
    recognitionItems.value = [
      ...pendingLocalItems,
      ...mergeRecognitionHistoryItems(existingServerItems, serverItems)
    ]
    updateRecognitionHistoryPager(payload, requestedPage)
  } catch (error) {
    if (!options.silent) {
      ElMessage.error(formatRecognitionError(error, '识别记录加载失败'))
    }
  } finally {
    recognitionHistoryLoading.value = false
    if (showLoading) {
      recognitionHistoryInitialLoading.value = false
    }
  }
}

function loadMoreRecognitionHistory() {
  if (!recognitionHistoryPager.hasNext || recognitionHistoryLoading.value) return
  void refreshRecognitionHistory({ append: true })
}

function startRecognitionHistoryPolling() {
  stopRecognitionHistoryPolling()
  recognitionHistoryPollTimer = window.setInterval(() => {
    if (!recognitionHistoryVisible.value) return
    if (!recognitionItems.value.some(item => isRecognitionPending(item))) return
    void refreshRecognitionHistory({ silent: true })
  }, 2500)
}

function stopRecognitionHistoryPolling() {
  if (recognitionHistoryPollTimer) {
    window.clearInterval(recognitionHistoryPollTimer)
    recognitionHistoryPollTimer = null
  }
}

function handleRecognitionFileChange(file, fileList) {
  syncRecognitionUploadItems(fileList, {
    emptyMessage: '只能选择图片文件'
  })
}

function handleRecognitionFileRemove(file, fileList) {
  syncRecognitionUploadItems(fileList, {
    processBackground: false,
    silentEmpty: true
  })
}

function focusRecognitionPasteTarget() {
  nextTick(() => {
    recognitionPasteTarget.value?.focus?.()
  })
}

function handleRecognitionDialogPaste(event) {
  const files = getClipboardImageFiles(event)
  if (!files.length) {
    if (shouldWarnEmptyClipboardPaste(event?.target)) {
      ElMessage.warning('剪贴板中没有可粘贴的图片')
    }
    return
  }
  event.preventDefault()
  const uploadItems = files.map(createRecognitionUploadItemFromFile)
  syncRecognitionUploadItems(uploadItems, {
    append: true,
    backgroundItems: uploadItems,
    silentEmpty: true
  })
  ElMessage.success(`已加入 ${files.length} 张截图${recognitionBackgroundMode.value ? '，后台识别已开始' : ''}`)
}

function syncRecognitionUploadItems(uploadItems = [], options = {}) {
  const sourceItems = Array.isArray(uploadItems) ? uploadItems : []
  const imageItems = sourceItems
    .filter(item => item?.raw?.type?.startsWith('image/'))
    .map(ensureRecognitionUploadPreviewUrl)
  if (!options.silentEmpty && imageItems.length !== sourceItems.length) {
    ElMessage.warning(options.emptyMessage || '只能粘贴图片文件')
  }
  if (options.append) {
    const existingUids = new Set(recognitionFileList.value.map(item => item.uid))
    recognitionFileList.value = [
      ...recognitionFileList.value,
      ...imageItems.filter(item => !existingUids.has(item.uid))
    ]
  } else {
    recognitionFileList.value = imageItems
  }
  if (recognitionBackgroundMode.value && options.processBackground !== false) {
    enqueueBackgroundRecognitionFromUploadItems(options.backgroundItems || imageItems)
    return
  }
}

function resetRecognitionDialog() {
  recognitionFileList.value = []
  recognitionSubmitting.value = false
  recognitionBackgroundMode.value = true
}

function getClipboardImageFiles(event) {
  const clipboardData = event?.clipboardData
  if (!clipboardData) return []
  const filesFromItems = Array.from(clipboardData.items || [])
    .filter(item => item.kind === 'file' && item.type?.startsWith('image/'))
    .map(item => item.getAsFile())
    .filter(Boolean)
  const files = filesFromItems.length ? filesFromItems : Array.from(clipboardData.files || [])
    .filter(file => file.type?.startsWith('image/'))
  const timestamp = Date.now()
  return files.map((file, index) => renameClipboardImageFile(file, timestamp, index))
}

function renameClipboardImageFile(file, timestamp, index) {
  const extension = getImageExtension(file.type)
  const filename = `clipboard-image-${timestamp}${index ? `-${index + 1}` : ''}.${extension}`
  return new File([file], filename, {
    type: file.type || 'image/png',
    lastModified: timestamp
  })
}

function getImageExtension(mimeType = '') {
  const normalizedType = String(mimeType).toLowerCase()
  if (normalizedType.includes('jpeg') || normalizedType.includes('jpg')) return 'jpg'
  if (normalizedType.includes('webp')) return 'webp'
  if (normalizedType.includes('gif')) return 'gif'
  if (normalizedType.includes('bmp')) return 'bmp'
  return 'png'
}

function createRecognitionUploadItemFromFile(file) {
  const uid = createId()
  return ensureRecognitionUploadPreviewUrl({
    name: file.name || `${uid}.png`,
    uid,
    raw: file,
    status: 'ready'
  })
}

function ensureRecognitionUploadPreviewUrl(uploadItem = {}) {
  if (!uploadItem || uploadItem.previewUrl) return uploadItem
  const raw = uploadItem.raw
  if (!raw?.type?.startsWith('image/')) return uploadItem
  const previewUrl = URL.createObjectURL(raw)
  recognitionObjectUrls.add(previewUrl)
  uploadItem.previewUrl = previewUrl
  uploadItem.url = uploadItem.url || previewUrl
  return uploadItem
}

function getRecognitionUploadPreviewUrl(uploadItem = {}) {
  return uploadItem.previewUrl || uploadItem.url || ''
}

function revokeRecognitionObjectUrls() {
  recognitionObjectUrls.forEach(url => URL.revokeObjectURL(url))
  recognitionObjectUrls.clear()
}

async function clearRecognitionHistory() {
  if (backgroundRecognitionRunning.value) {
    ElMessage.warning('后台识别仍在进行，完成后再清空记录')
    return
  }
  await clearInternalPowerRecognitionHistory()
  recognitionItems.value = []
  updateRecognitionHistoryPager({ total: 0, pageNum: 1, pageSize: recognitionHistoryPager.pageSize, hasNext: false }, 1)
  backgroundRecognitionFileUids.value = new Set()
  revokeRecognitionObjectUrls()
  ElMessage.success('识别记录已清空')
}

function shouldWarnEmptyClipboardPaste(target) {
  return isRecognitionPasteZoneTarget(target) || !isEditablePasteTarget(target)
}

function isRecognitionPasteZoneTarget(target) {
  return !!target?.closest?.('.recognition-paste-zone')
}

function isEditablePasteTarget(target) {
  return !!target?.closest?.('input, textarea, [contenteditable="true"]')
}

async function submitRecognition() {
  const uploadItems = recognitionFileList.value.filter(item => item?.raw)
  if (!uploadItems.length) {
    ElMessage.warning('请先选择图片')
    return
  }
  if (!aiRecognitionUnlimited.value && uploadItems.length > aiRecognitionCount.value) {
    ElMessage.warning(`AI识图次数不足，当前剩余 ${aiRecognitionCount.value} 次`)
    return
  }
  if (recognitionBackgroundMode.value) {
    enqueueBackgroundRecognitionFromUploadItems(recognitionFileList.value)
    return
  }
  recognitionSubmitting.value = true
  try {
    const result = await recognizeUploadItemsWithProgress(uploadItems, { background: false, autoSave: false })
    recognitionFileList.value = []
    if (result.successCount) {
      ElMessage.success('识别完成')
    } else {
      ElMessage.warning('识别完成，但没有可导入的结果')
    }
  } finally {
    recognitionSubmitting.value = false
  }
}

async function recognizeUploadItemsWithProgress(uploadItems = [], options = {}) {
  const progressItems = uploadItems.map(item => createRecognitionProgressItem(item, options))
  recognitionItems.value = [...progressItems, ...recognitionItems.value]
  const results = await Promise.allSettled(
    progressItems.map((progressItem, index) => processRecognitionUploadItem(uploadItems[index], progressItem, options))
  )
  results.forEach((result, index) => {
    if (result.status === 'rejected') {
      Object.assign(progressItems[index], createRecognitionFailureItem(uploadItems[index]?.raw, result.reason), {
        clientId: progressItems[index].clientId,
        imageUrl: progressItems[index].imageUrl,
        status: 'failed',
        background: !!options.background,
        updatedAt: new Date().toISOString()
      })
    }
  })
  return {
    successCount: progressItems.filter(item => item.success).length,
    savedCount: progressItems.filter(item => item.status === 'saved').length,
    failedCount: progressItems.filter(item => item.status === 'failed').length
  }
}

async function recognizeFiles(files = []) {
  const results = await Promise.allSettled(
    files.map(file => recognizeInternalPowerImage(file, internalPowerRecognitionPrompt))
  )
  const mergedItems = []
  let consumedCount = 0
  let remainingCount = null
  results.forEach((result, index) => {
    const file = files[index]
    if (result.status === 'fulfilled') {
      const response = result.value || {}
      consumedCount += Number(response.consumedCount || 0)
      const responseRemaining = Number(response.remainingAiImageRecognitionCount)
      if (Number.isFinite(responseRemaining)) {
        remainingCount = responseRemaining
      }
      const responseItems = Array.isArray(response.result?.items) ? response.result.items : []
      if (responseItems.length) {
        mergedItems.push(...responseItems)
      } else {
        mergedItems.push(createRecognitionFailureItem(file, '识别接口未返回图片结果'))
      }
      return
    }
    mergedItems.push(createRecognitionFailureItem(file, result.reason || '图片识别请求失败'))
  })
  return {
    items: normalizeRecognitionItems(mergedItems),
    consumedCount,
    remainingCount
  }
}

function applyRecognitionConsumption(initialRecognitionCount, consumedCount, response = {}) {
  if (!aiRecognitionUnlimited.value) {
    const remainingNormalCount = Number(response.remainingCount ?? response.remainingAiImageRecognitionCount)
    const remainingVipCount = Number(response.remainingVipAiImageRecognitionCount)
    if (Number.isFinite(remainingVipCount)) {
      userStore.vipAiImageRecognitionCount = Math.max(0, remainingVipCount)
    }
    if (Number.isFinite(remainingNormalCount)) {
      userStore.aiImageRecognitionCount = Math.max(0, remainingNormalCount)
      return
    }
    userStore.aiImageRecognitionCount = Math.max(0, Number(initialRecognitionCount || 0) - Number(consumedCount || 0))
  }
}

function createRecognitionFailureItem(file, error) {
  return {
    fileName: file?.name || 'image',
    success: false,
    parsed: {},
    rawText: '',
    error: formatRecognitionError(error, '图片识别请求失败'),
    presetCandidates: [],
    needsPresetSelection: false,
    presetSelectionMessage: ''
  }
}

function normalizeRecognitionItems(items = [], options = {}) {
  return (Array.isArray(items) ? items : []).map((item, index) => {
    const candidates = Array.isArray(item.presetCandidates) ? item.presetCandidates.map(normalizeCatalogItem) : []
    const parsed = normalizeRecognitionParsed(item.parsed || {}, candidates)
    const success = !!item.success
    const needsPresetSelection = !!item.needsPresetSelection || (success && candidates.length > 1)
    return {
      clientId: `${Date.now()}-${index}-${Math.random().toString(36).slice(2, 6)}`,
      recordId: item.recordId || item.record_id || null,
      fileName: item.fileName || `图片${index + 1}`,
      imageUrl: item.imageUrl || options.imageUrl || '',
      fileSize: item.fileSize || options.fileSize || 0,
      success,
      status: item.status || (needsPresetSelection ? 'needs_preset' : (success ? 'recognized' : 'failed')),
      background: !!options.background || !!item.background,
      parsed,
      entries: normalizeRecognitionEntriesForEdit(parsed?.属性加成),
      rawText: item.rawText || '',
      error: item.error || '',
      presetCandidates: candidates,
      selectedPresetId: needsPresetSelection ? '' : (candidates.length === 1 ? candidates[0].presetId : ''),
      needsPresetSelection,
      presetSelectionMessage: item.presetSelectionMessage || (needsPresetSelection ? '该内功存在多个元素，请选择元素后再新增' : ''),
      saving: false,
      saved: false,
      savedPowerId: item.savedPowerId || null
    }
  })
}

function normalizeRecognitionHistoryItems(items = []) {
  return (Array.isArray(items) ? items : []).map((item, index) => {
    const candidates = Array.isArray(item.presetCandidates) ? item.presetCandidates.map(normalizeCatalogItem) : []
    const parsed = normalizeRecognitionParsed(item.parsed || {}, candidates)
    const status = item.status || (item.error ? 'failed' : 'recognized')
    const saved = status === 'saved' || !!item.savedPowerId
    const needsPresetSelection = !!item.needsPresetSelection || (status === 'recognized' && !saved && candidates.length > 1)
    const imageUrl = internalPowerImageVisible.value && item.imageBase64
      ? `data:${item.mimeType || 'image/png'};base64,${item.imageBase64}`
      : ''
    return {
      clientId: `history-${item.recordId || index}`,
      recordId: item.recordId,
      fileName: item.fileName || `图片${index + 1}`,
      imageUrl,
      fileSize: item.fileSize || 0,
      success: ['recognized', 'saved'].includes(status) || (!item.error && !!Object.keys(parsed).length),
      status: saved ? 'saved' : (needsPresetSelection ? 'needs_preset' : status),
      background: false,
      parsed,
      entries: normalizeRecognitionEntriesForEdit(parsed?.属性加成),
      rawText: item.rawText || '',
      error: item.error || '',
      presetCandidates: candidates,
      selectedPresetId: needsPresetSelection ? '' : (candidates.length === 1 ? candidates[0].presetId : ''),
      needsPresetSelection,
      presetSelectionMessage: item.presetSelectionMessage || (needsPresetSelection ? '该内功存在多个元素，请选择元素后再新增' : ''),
      saving: false,
      saved,
      savedPowerId: item.savedPowerId || null,
      startedAt: item.createTime || '',
      updatedAt: item.updateTime || item.createTime || ''
    }
  })
}

function enqueueBackgroundRecognitionFromUploadItems(uploadItems = []) {
  if (!recognitionBackgroundMode.value) return
  const pendingUploadItems = (uploadItems || [])
    .filter(item => item?.raw?.type?.startsWith('image/'))
    .map(ensureRecognitionUploadPreviewUrl)
    .filter(item => !backgroundRecognitionFileUids.value.has(item.uid))
  if (!pendingUploadItems.length) return
  let allowedItems = pendingUploadItems
  if (!aiRecognitionUnlimited.value && pendingUploadItems.length > aiRecognitionCount.value) {
    allowedItems = pendingUploadItems.slice(0, Math.max(0, aiRecognitionCount.value))
    ElMessage.warning(`AI识图次数不足，本次只会后台识别 ${allowedItems.length} 张`)
  }
  if (!allowedItems.length) return
  const nextUids = new Set(backgroundRecognitionFileUids.value)
  const progressItems = allowedItems.map(item => {
    nextUids.add(item.uid)
    return createRecognitionProgressItem(item, { background: true })
  })
  backgroundRecognitionFileUids.value = nextUids
  recognitionItems.value = [...progressItems, ...recognitionItems.value]
  backgroundRecognitionRunning.value = true
  progressItems.forEach((progressItem, index) => {
    void recognizeAndSaveBackgroundUploadItem(allowedItems[index], progressItem)
  })
}

function createRecognitionProgressItem(uploadItem = {}, options = {}) {
  const imageUrl = getRecognitionUploadPreviewUrl(uploadItem)
  const prefix = options.background ? 'background' : 'manual'
  return {
    clientId: `${prefix}-${uploadItem.uid || createId()}`,
    fileName: uploadItem.name || uploadItem.raw?.name || 'image',
    imageUrl,
    fileSize: uploadItem.raw?.size || uploadItem.size || 0,
    success: false,
    status: 'queued',
    background: !!options.background,
    parsed: {},
    entries: [],
    rawText: '',
    error: '',
    presetCandidates: [],
    selectedPresetId: '',
    saving: false,
    saved: false,
    startedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
}

async function recognizeAndSaveBackgroundUploadItem(uploadItem, progressItem) {
  return processRecognitionUploadItem(uploadItem, progressItem, { background: true, autoSave: true })
}

async function processRecognitionUploadItem(uploadItem, progressItem, options = {}) {
  const file = uploadItem?.raw
  if (!file) {
    Object.assign(progressItem, createRecognitionFailureItem(uploadItem, '图片文件不存在'), {
      status: 'failed',
      background: !!options.background,
      updatedAt: new Date().toISOString()
    })
    updateBackgroundRecognitionRunning()
    return
  }
  progressItem.status = 'recognizing'
  progressItem.updatedAt = new Date().toISOString()
  try {
    const response = await recognizeInternalPowerImage(file, internalPowerRecognitionPrompt)
    applyRecognitionConsumption(aiRecognitionCount.value, Number(response?.consumedCount || 0), response)
    const responseItems = Array.isArray(response?.result?.items) ? response.result.items : []
    const previewUrl = progressItem.imageUrl
    const normalizedItem = normalizeRecognitionItems(
      responseItems.length ? responseItems : [createRecognitionFailureItem(file, '识别接口未返回图片结果')],
      {
        background: !!options.background,
        imageUrl: previewUrl,
        fileSize: progressItem.fileSize
      }
    )[0]
    Object.assign(progressItem, normalizedItem, {
      clientId: progressItem.clientId,
      imageUrl: normalizedItem.imageUrl || previewUrl,
      background: !!options.background,
      status: normalizedItem.success
        ? (normalizedItem.needsPresetSelection ? 'needs_preset' : (options.autoSave ? 'saving' : 'recognized'))
        : 'failed',
      updatedAt: new Date().toISOString()
    })
    if (!progressItem.success) {
      return
    }
    selectDefaultRecognitionCandidate(progressItem)
    if (progressItem.needsPresetSelection) {
      return
    }
    if (!options.autoSave) {
      return
    }
    try {
      const savedPower = await saveRecognizedPowerDirectly(progressItem, { silent: true, clampEntries: true })
      if (savedPower) {
        progressItem.status = 'saved'
        progressItem.saved = true
        progressItem.needsPresetSelection = false
        progressItem.error = ''
        progressItem.updatedAt = new Date().toISOString()
      } else {
        progressItem.status = 'failed'
        progressItem.error = progressItem.error || '识别成功，但自动新增失败，请检查词条上限、内功上限或预设匹配'
        progressItem.updatedAt = new Date().toISOString()
      }
    } catch (error) {
      progressItem.status = 'failed'
      progressItem.error = formatRecognitionError(error, '识别成功，但自动新增失败')
      progressItem.updatedAt = new Date().toISOString()
    }
  } catch (error) {
    const previewUrl = progressItem.imageUrl
    Object.assign(progressItem, createRecognitionFailureItem(file, error), {
      clientId: progressItem.clientId,
      imageUrl: previewUrl,
      status: 'failed',
      background: !!options.background,
      updatedAt: new Date().toISOString()
    })
  } finally {
    updateBackgroundRecognitionRunning()
  }
}

function updateBackgroundRecognitionRunning() {
  const wasRunning = backgroundRecognitionRunning.value
  backgroundRecognitionRunning.value = recognitionItems.value.some(
    item => item.background && isRecognitionPending(item)
  )
  if (wasRunning && !backgroundRecognitionRunning.value) {
    const backgroundItems = recognitionItems.value.filter(item => item.background)
    const savedCount = backgroundItems.filter(item => getRecognitionDisplayStatus(item) === 'saved').length
    const failedCount = backgroundItems.filter(item => getRecognitionDisplayStatus(item) === 'failed').length
    const selectionCount = backgroundItems.filter(item => getRecognitionDisplayStatus(item) === 'needs_preset').length
    if (savedCount || failedCount || selectionCount) {
      ElNotification({
        title: '后台识别进度',
        message: `当前已新增 ${savedCount} 个内功，待选择 ${selectionCount} 张，失败 ${failedCount} 张`,
        type: failedCount ? 'warning' : 'success'
      })
    }
  }
}

function getRecognitionStatusText(item = {}) {
  const status = getRecognitionDisplayStatus(item)
  const statusTextMap = {
    queued: '等待识别',
    recognizing: '识别中',
    needs_preset: '待选择',
    saving: '保存中',
    saved: '已新增',
    failed: '失败',
    recognized: '识别成功'
  }
  return statusTextMap[status] || (item.success ? '识别成功' : '识别失败')
}

function getRecognitionDisplayStatus(item = {}) {
  const status = String(item.status || '').trim()
  if (item.error || status === 'failed') return 'failed'
  if (item.saved || status === 'saved') return 'saved'
  if (item.needsPresetSelection || status === 'needs_preset') return 'needs_preset'
  if (status === 'recognized' || (item.success && !item.saving)) return 'recognized'
  if (item.saving || status === 'saving') return 'saving'
  if (status === 'recognizing') return 'recognizing'
  if (status === 'queued') return 'queued'
  return item.success ? 'recognized' : (status || 'queued')
}

function isRecognitionPending(item = {}) {
  return ['queued', 'recognizing', 'saving'].includes(getRecognitionDisplayStatus(item))
}

function getRecognitionProgressPercent(item = {}) {
  const status = getRecognitionDisplayStatus(item)
  const percentMap = {
    queued: 8,
    recognizing: 45,
    needs_preset: 100,
    saving: 82,
    recognized: 100,
    saved: 100,
    failed: 100
  }
  return percentMap[status] ?? (item.success ? 100 : 0)
}

function getRecognitionProgressStatus(item = {}) {
  const status = getRecognitionDisplayStatus(item)
  if (status === 'failed') return 'exception'
  if (status === 'saved' || status === 'recognized') return 'success'
  if (status === 'needs_preset') return 'warning'
  return undefined
}

function getRecognitionStatusType(item = {}) {
  const status = getRecognitionDisplayStatus(item)
  if (status === 'saved' || status === 'recognized') return 'success'
  if (status === 'queued' || status === 'recognizing') return 'info'
  if (status === 'saving' || status === 'needs_preset') return 'warning'
  return item.success ? 'success' : 'danger'
}

function formatRecognitionEntryValue(entry = {}) {
  const suffix = isPercentEntry(entry.name) ? '%' : ''
  return `${entry.value ?? 0}${suffix}`
}

function formatRecognitionError(error, fallback = '图片识别请求失败') {
  if (!error) return fallback
  if (typeof error === 'string') return error
  const parts = []
  if (error.message) parts.push(`message: ${error.message}`)
  if (error.msg) parts.push(`msg: ${error.msg}`)
  if (error.name) parts.push(`name: ${error.name}`)
  const response = error.response
  if (response) {
    parts.push(`status: ${response.status || ''} ${response.statusText || ''}`.trim())
    if (response.config?.url) parts.push(`url: ${response.config.url}`)
    if (response.data !== undefined) {
      parts.push(`response: ${stringifyRecognitionErrorData(response.data)}`)
    }
  }
  if (error.code) parts.push(`code: ${error.code}`)
  if (error.data !== undefined) parts.push(`data: ${stringifyRecognitionErrorData(error.data)}`)
  if (error.config?.url && !response?.config?.url) parts.push(`url: ${error.config.url}`)
  if (error.stack) parts.push(`stack: ${error.stack}`)
  if (!parts.length) {
    parts.push(stringifyRecognitionErrorData(error))
  }
  return Array.from(new Set(parts.filter(Boolean))).join('\n') || fallback
}

function stringifyRecognitionErrorData(value) {
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function normalizeRecognitionParsed(parsed = {}, candidates = []) {
  const nextParsed = { ...(parsed || {}) }
  const powerName = normalizeRecognizedPowerName(nextParsed.内功名 || nextParsed.name)
  if (powerName) {
    nextParsed.内功名 = powerName
  }
  const elementKey = getRecognizedElementKey(nextParsed)
  if (!elementKey && candidates.length === 1) {
    const candidateElementKey = candidates[0]?.elementKey
    if (candidateElementKey) {
      nextParsed.元素 = getElementLabel(candidateElementKey)
    }
  }
  return nextParsed
}

function normalizeRecognizedPowerName(value) {
  const text = String(value || '').trim()
  if (!text) return ''
  const cleaned = text
    .replace(/·试用/g, '')
    .replace(/・试用/g, '')
    .replace(/试用/g, '')
    .trim()
  return recognizedRarePowerNameMap[cleaned] || cleaned
}

function getRecognizedElementKey(parsed = {}) {
  const values = [parsed?.元素, parsed?.五行, parsed?.element]
  for (const value of values) {
    const elementKey = normalizeRecognizedElementKey(value)
    if (elementKey) return elementKey
  }
  return ''
}

function normalizeRecognizedElementKey(value) {
  const text = String(value || '').trim().toLowerCase()
  if (!text) return ''
  return recognizedElementAliases[text.replace(/\s+/g, '')] || ''
}

function resolveRecognizedPresetCandidates(parsed = {}) {
  const normalizedParsed = normalizeRecognitionParsed(parsed)
  const powerName = normalizedParsed.内功名
  const namedCandidates = powerCatalog.value.filter(item => item.name === powerName)
  const elementKey = getRecognizedElementKey(normalizedParsed)
  if (elementKey && namedCandidates.length > 1) {
    const matchedCandidates = namedCandidates.filter(item => item.elementKey === elementKey)
    if (matchedCandidates.length === 1) {
      normalizedParsed.元素 = getElementLabel(elementKey)
      return {
        parsed: normalizedParsed,
        candidates: matchedCandidates,
        needsPresetSelection: false
      }
    }
  }
  const resolvedParsed = normalizeRecognitionParsed(normalizedParsed, namedCandidates)
  return {
    parsed: resolvedParsed,
    candidates: namedCandidates,
    needsPresetSelection: namedCandidates.length > 1
  }
}

function getRecognizedElementLabel(parsed = {}) {
  const elementKey = getRecognizedElementKey(parsed)
  if (elementKey) return getElementLabel(elementKey)
  const rawElement = String(parsed?.元素 || parsed?.五行 || parsed?.element || '').trim()
  return rawElement || ''
}

function selectDefaultRecognitionCandidate(item) {
  if (item?.needsPresetSelection) return
  if (!item?.selectedPresetId && item?.presetCandidates?.length) {
    item.selectedPresetId = item.presetCandidates[0].presetId
  }
}

function importRecognizedPower(item) {
  const nextPower = buildRecognizedPowerDraft(item)
  if (!nextPower) return
  selectedId.value = ''
  draft.value = nextPower
  savedDraftSignature.value = JSON.stringify(draft.value)
  recognitionDialogVisible.value = false
  editingVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
  const importedLingyun = nextPower.lingyunEnabled
  ElMessage.success(importedLingyun ? '已导入为内功草稿，已勾选灵韵' : '已导入为内功草稿')
}

function openJsonImportDialog() {
  jsonImportDialog.text = ''
  jsonImportDialog.open = true
}

function submitJsonImportDialog() {
  let parsed
  try {
    parsed = parseJsonImportText(jsonImportDialog.text)
  } catch (error) {
    ElMessage.error(formatRecognitionError(error, 'JSON格式不正确'))
    return
  }
  const powerName = normalizeRecognizedPowerName(parsed?.内功名 || parsed?.name)
  if (!powerName) {
    ElMessage.error('JSON缺少内功名')
    return
  }
  const resolved = resolveRecognizedPresetCandidates(parsed)
  const candidates = resolved.candidates
  if (!candidates.length) {
    ElMessage.error(`未匹配到启用内功预设：${powerName}`)
    return
  }
  const importItem = {
    fileName: 'JSON导入结果',
    success: true,
    parsed: resolved.parsed,
    entries: normalizeRecognitionEntriesForEdit(resolved.parsed?.属性加成),
    rawText: jsonImportDialog.text,
    presetCandidates: candidates,
    selectedPresetId: resolved.needsPresetSelection ? '' : candidates[0].presetId,
    needsPresetSelection: resolved.needsPresetSelection,
    presetSelectionMessage: resolved.needsPresetSelection ? '该内功存在多个元素，请选择元素后再新增' : ''
  }
  if (resolved.needsPresetSelection) {
    const [recognitionItem] = normalizeRecognitionItems([importItem])
    recognitionItems.value = [recognitionItem, ...recognitionItems.value]
    recognitionDialogVisible.value = true
    jsonImportDialog.open = false
    ElMessage.warning('JSON已导入识别列表，请先选择元素/预设')
    return
  }
  const nextPower = buildRecognizedPowerDraft(importItem)
  if (!nextPower) return
  selectedId.value = ''
  draft.value = nextPower
  savedDraftSignature.value = JSON.stringify(draft.value)
  editingVisible.value = true
  jsonImportDialog.open = false
  nextTick(() => formRef.value?.clearValidate())
  ElMessage.success('JSON已导入为内功草稿')
}

function parseJsonImportText(text = '') {
  const trimmed = String(text || '').trim()
  if (!trimmed) {
    throw new Error('请先粘贴JSON')
  }
  const unfenced = trimmed
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim()
  return JSON.parse(unfenced)
}

async function saveRecognizedPowerDirectly(item, options = {}) {
  const nextPower = buildRecognizedPowerDraft(item, options)
  if (!nextPower) return null
  item.saving = true
  try {
    const savedPower = normalizePower(await addInternalPower(toPowerPayload(nextPower)))
    powers.value.unshift(savedPower)
    updateQuotaCount()
    item.saved = true
    item.savedPowerId = savedPower.powerId || savedPower.id || null
    item.needsPresetSelection = false
    item.presetSelectionMessage = ''
    if (item.recordId && item.savedPowerId) {
      await markInternalPowerRecognitionHistorySaved(item.recordId, item.savedPowerId)
    }
    if (!options.silent) {
      ElMessage.success(`已新增内功「${savedPower.name || '未命名'}」`)
    }
    return savedPower
  } finally {
    item.saving = false
  }
}

function buildRecognizedPowerDraft(item, options = {}) {
  const candidate = item.presetCandidates.find(candidate => candidate.presetId === item.selectedPresetId)
  if (!candidate) {
    warnRecognitionBuild('请先选择具体内功预设', options)
    return null
  }
  if (!canCreateMore.value) {
    warnRecognitionBuild('已超过当前内功上限，请删除后再新增或联系管理员调整上限', options)
    return null
  }
  const entries = normalizeRecognizedEntries(item.entries, options)
  if (!validateEntryValues(entries, options)) return null
  const lingyunDetected = item.entries.some(entry => String(entry?.name || entry?.词条 || '').trim() === '灵韵')
  return normalizePower({
    id: createId(),
    name: item.parsed?.内功名 || candidate.name,
    category: candidate.value,
    categoryTrait: getCatalogTrait(candidate),
    bonusPercent: candidate.baseBonus,
    lingyunEnabled: lingyunDetected,
    lingyunBonusPercent: candidate.lingyunBonusPercent,
    imageUrl: candidate.imageUrl,
    entries,
    elements: candidate.elements,
    remark: 'AI识图导入',
    updatedAt: new Date().toISOString()
  })
}

function warnRecognitionBuild(message, options = {}) {
  if (!options.silent) {
    ElMessage.warning(message)
  }
}

function normalizeRecognitionEntriesForEdit(entries = []) {
  return (Array.isArray(entries) ? entries : []).map(entry => {
    const name = String(entry?.词条 || entry?.name || '').trim()
    return {
      id: createId(),
      name,
      value: parseRecognitionEntryNumber(entry?.数值 ?? entry?.value),
      rawValue: entry?.数值 ?? entry?.value ?? ''
    }
  })
}

function normalizeRecognizedEntries(entries = [], options = {}) {
  return (Array.isArray(entries) ? entries : [])
    .map(entry => {
      const name = String(entry?.name || entry?.词条 || '').trim()
      return {
        id: String(entry?.id || createId()),
        name,
        value: normalizeRecognizedEntryValue(entry?.value ?? entry?.数值, name, options)
      }
    })
    .filter(entry => entry.name && entry.name !== '灵韵' && getEntryOption(entry.name))
}

function normalizeRecognizedEntryValue(value, entryName = '', options = {}) {
  const normalizedValue = String(value ?? '').trim().replace(/^\+/, '').replace('%', '')
  if (!options.clampEntries) return normalizedValue
  const option = getEntryOption(entryName)
  const parsedValue = parseEntryValue(normalizedValue)
  if (!option || parsedValue === null) return normalizedValue
  const limitValue = Number(option.limitValue || 0)
  return String(Math.max(0, Math.min(limitValue, parsedValue)))
}

function parseRecognitionEntryNumber(value) {
  const parsed = parseEntryValue(String(value ?? '').replace(/^\+/, ''))
  return parsed === null ? 0 : parsed
}

function getRecognitionEntryMax(entry = {}) {
  const limit = getEntryLimitValue(entry.name)
  return limit > 0 ? limit : undefined
}

function getRecognitionEntryPrecision(entry = {}) {
  return getEntryPrecision(entry.name)
}

function getRecognitionEntryHint(entry = {}) {
  if (entry.name === '灵韵') return '灵韵暂不导入'
  const option = getEntryOption(entry.name)
  if (!option) return '暂不支持该词条'
  return `最大数值 ${formatEntryLimitValue(option)}`
}

function selectPower(id) {
  selectedId.value = id
  draft.value = clonePower(selectedPower.value)
  savedDraftSignature.value = JSON.stringify(draft.value)
  editingVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

function handleCardClick(item) {
  if (batchMode.value) {
    togglePowerSelection(item.id)
    return
  }
  selectPower(item.id)
}

function toggleBatchMode() {
  batchMode.value = !batchMode.value
  selectedBatchIds.value = []
}

function isPowerSelected(id) {
  return selectedBatchIds.value.includes(id)
}

function togglePowerSelection(id) {
  if (selectedBatchIds.value.includes(id)) {
    selectedBatchIds.value = selectedBatchIds.value.filter(item => item !== id)
    return
  }
  selectedBatchIds.value = [...selectedBatchIds.value, id]
}

function toggleSelectAllFiltered() {
  if (isAllFilteredSelected.value) {
    const filteredIds = new Set(filteredPowers.value.map(item => item.id))
    selectedBatchIds.value = selectedBatchIds.value.filter(id => !filteredIds.has(id))
    return
  }
  const nextIds = new Set(selectedBatchIds.value)
  filteredPowers.value.forEach(item => nextIds.add(item.id))
  selectedBatchIds.value = Array.from(nextIds)
}

function createPower() {
  if (!canCreateMore.value) {
    ElMessage.warning('已超过当前内功上限，请删除后再新增或联系管理员调整上限')
    return
  }
  if (!powerCatalog.value.length) {
    ElMessage.warning('暂无可用内功预设，请联系管理员在系统管理中维护')
    return
  }
  const firstCatalog = powerCatalog.value[0] || null
  selectedId.value = ''
  draft.value = normalizePower({
    id: createId(),
    name: firstCatalog?.name || '新内功',
    category: firstCatalog?.value || '通用',
    categoryTrait: firstCatalog ? getCatalogTrait(firstCatalog) : '等待定位',
    bonusPercent: firstCatalog?.baseBonus || 0,
    lingyunEnabled: false,
    lingyunBonusPercent: firstCatalog?.lingyunBonusPercent || 0,
    imageUrl: firstCatalog?.imageUrl || '',
    entries: cloneEntries(firstCatalog?.entries || []),
    elements: firstCatalog?.elements || createEmptyElements(),
    remark: '',
    updatedAt: new Date().toISOString()
  })
  savedDraftSignature.value = JSON.stringify(draft.value)
  editingVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

async function saveDraft() {
  if (!draft.value) return
  if (!isElementTotalValid.value) {
    ElMessage.warning(`五行元素总数必须符合预设：${expectedElementTotal.value} 个`)
    return
  }
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  if (!validateEntryValues(draft.value.entries)) return
  const nextPower = normalizePower({
    ...draft.value,
    updatedAt: new Date().toISOString()
  })
  const response = nextPower.powerId
    ? await updateInternalPower(nextPower.powerId, toPowerPayload(nextPower))
    : await addInternalPower(toPowerPayload(nextPower))
  const savedPower = normalizePower(response)
  const index = powers.value.findIndex(item => item.id === savedPower.id)
  if (index >= 0) {
    powers.value.splice(index, 1, savedPower)
  } else {
    powers.value.unshift(savedPower)
  }
  updateQuotaCount()
  selectedId.value = savedPower.id
  draft.value = clonePower(savedPower)
  savedDraftSignature.value = JSON.stringify(draft.value)
  editingVisible.value = false
  ElMessage.success('内功已保存到后端')
}

function restoreDraft() {
  if (!draft.value) return
  const initialDraft = savedDraftSignature.value ? JSON.parse(savedDraftSignature.value) : null
  const source = selectedPower.value || initialDraft
  if (!source) return
  draft.value = normalizePower(source)
  savedDraftSignature.value = JSON.stringify(draft.value)
  nextTick(() => formRef.value?.clearValidate())
}

async function duplicateSelected() {
  if (!draft.value) return
  if (!canCreateMore.value) {
    ElMessage.warning('已超过当前内功上限，请删除后再复制')
    return
  }
  const copy = normalizePower({
    ...clonePower(draft.value),
    id: createId(),
    powerId: undefined,
    name: `${draft.value.name || '未命名'} 副本`,
    updatedAt: new Date().toISOString()
  })
  const savedPower = normalizePower(await addInternalPower(toPowerPayload(copy)))
  powers.value.unshift(savedPower)
  updateQuotaCount()
  selectPower(savedPower.id)
  ElMessage.success('已复制内功')
}

async function deletePower(power) {
  if (!power) return
  const confirmed = await confirmDeleteAction({
    title: '删除内功',
    message: `确认删除「${power.name || '未命名内功'}」吗？`
  })
  if (!confirmed) {
    return
  }
  await removePowers([power])
  ElMessage.success('已删除')
}

async function deleteSelected() {
  if (!selectedPower.value) return
  const power = selectedPower.value
  const confirmed = await confirmDeleteAction({
    title: '删除内功',
    message: `确认删除「${power.name || '未命名内功'}」吗？`
  })
  if (!confirmed) {
    return
  }
  await removePowers([power])
  ElMessage.success('已删除')
}

async function deleteBatchPowers() {
  if (!selectedBatchPowers.value.length) return
  const count = selectedBatchPowers.value.length
  const confirmed = await confirmDeleteAction({
    title: '批量删除内功',
    message: `确认删除已选中的 ${count} 个内功吗？`
  })
  if (!confirmed) return
  await removePowers(selectedBatchPowers.value)
  selectedBatchIds.value = []
  batchMode.value = false
  ElMessage.success(`已删除 ${count} 个内功`)
}

async function clearAllPowers() {
  if (!powers.value.length) return
  const count = powers.value.length
  const confirmed = await confirmDeleteAction({
    title: '清空内功',
    message: `确认清空当前账号的全部 ${count} 个内功吗？此操作不可恢复。`
  })
  if (!confirmed) return
  await removePowers([...powers.value])
  selectedBatchIds.value = []
  batchMode.value = false
  ElMessage.success('内功已清空')
}

async function removePowers(targetPowers = []) {
  const targets = targetPowers.filter(Boolean)
  for (const power of targets) {
    if (power.powerId) {
      await deleteInternalPower(power.powerId)
    }
  }
  const removeIds = new Set(targets.map(item => item.id))
  powers.value = powers.value.filter(item => !removeIds.has(item.id))
  selectedBatchIds.value = selectedBatchIds.value.filter(id => !removeIds.has(id))
  if (removeIds.has(selectedId.value)) {
    selectedId.value = ''
    draft.value = null
    savedDraftSignature.value = ''
    editingVisible.value = false
  }
  updateQuotaCount()
}

function confirmDeleteAction({ title, message }) {
  if (deleteConfirmSkipKey.value && sessionStorage.getItem(deleteConfirmSkipKey.value) === '1') {
    return Promise.resolve(true)
  }
  deleteConfirmTitle.value = title
  deleteConfirmMessage.value = message
  deleteConfirmSkipForSession.value = false
  deleteConfirmVisible.value = true
  return new Promise(resolve => {
    deleteConfirmResolve.value = resolve
  })
}

function acceptDeleteConfirm() {
  if (deleteConfirmSkipForSession.value && deleteConfirmSkipKey.value) {
    sessionStorage.setItem(deleteConfirmSkipKey.value, '1')
  }
  deleteConfirmResolve.value?.(true)
  deleteConfirmResolve.value = null
  deleteConfirmVisible.value = false
}

function cancelDeleteConfirm() {
  deleteConfirmResolve.value?.(false)
  deleteConfirmResolve.value = null
  deleteConfirmVisible.value = false
}

async function resetSamples() {
  if (!powerCatalog.value.length) {
    ElMessage.warning('暂无可用内功预设，不能重置示例')
    return
  }
  try {
    await ElMessageBox.confirm('这会覆盖当前账号后端保存的内功示例，是否继续？', '重置示例', {
      type: 'warning',
      confirmButtonText: '重置',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  for (const power of powers.value) {
    if (power.powerId) {
      await deleteInternalPower(power.powerId)
    }
  }
  const response = await importLocalInternalPowers(getSamplePowersForQuota().map(toPowerPayload))
  applyPowerResponse(response)
  selectedId.value = ''
  draft.value = null
  savedDraftSignature.value = ''
  editingVisible.value = false
  ElMessage.success('示例内功已重置')
}

function addEntry() {
  if (!entryOptions.value.length) {
    ElMessage.warning('暂无启用内功词条，请联系管理员检查内置词条配置')
    return
  }
  draft.value.entries.push({
    id: createId(),
    name: entryOptions.value[0].entryName,
    value: 0
  })
}

function selectCategoryPreset(catalog) {
  if (!draft.value || !catalog) return
  draft.value.category = catalog.value
  handleCategoryChange(catalog.value)
  categoryPickerVisible.value = false
  nextTick(() => formRef.value?.clearValidate('category'))
}

function isElementFolderCollapsed(key) {
  return collapsedElementFolders.value.has(key)
}

function toggleElementFolder(key) {
  const next = new Set(collapsedElementFolders.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  collapsedElementFolders.value = next
}

function handleCategoryChange(value) {
  if (!draft.value) return
  const catalog = getCatalogByName(value)
  if (!catalog) return
  if (!draft.value.name || draft.value.name === '新内功' || powerCatalog.value.some(item => item.name === draft.value.name)) {
    draft.value.name = catalog.name
  }
  draft.value.categoryTrait = getCatalogTrait(catalog)
  draft.value.bonusPercent = catalog.baseBonus
  draft.value.lingyunBonusPercent = catalog.lingyunBonusPercent || 0
  draft.value.imageUrl = catalog.imageUrl || ''
  draft.value.entries = cloneEntries(catalog.entries || [])
  draft.value.elements = { ...catalog.elements }
}

function openValueEditor() {
  catalogDraft.value = powerCatalog.value.map(item => ({ ...item }))
  valueEditorVisible.value = true
}

function addCatalogRow() {
  catalogDraft.value.push(normalizeCatalogItem({
    id: createId(),
    name: '新内功种类',
    rarity: 'common',
    primaryElement: 'mixed',
    baseBonus: 4,
    trait: '待配置'
  }))
}

function removeCatalogRow(index) {
  catalogDraft.value.splice(index, 1)
}

function resetCatalogDraft() {
  catalogDraft.value = createDefaultPowerCatalog().map(item => ({ ...item }))
}

function saveCatalogDraft() {
  const seen = new Set()
  const nextCatalog = []
  for (const item of catalogDraft.value) {
    const normalized = normalizeCatalogItem(item)
    if (!normalized.name) {
      ElMessage.warning('内功种类名称不能为空')
      return
    }
    if (seen.has(normalized.name)) {
      ElMessage.warning(`内功种类「${normalized.name}」重复`)
      return
    }
    seen.add(normalized.name)
    nextCatalog.push(normalized)
  }
  if (!nextCatalog.length) {
    ElMessage.warning('至少保留一个内功种类')
    return
  }
  powerCatalog.value = nextCatalog
  powers.value = powers.value.map(power => {
    const catalog = nextCatalog.find(item => item.name === power.category)
    if (!catalog) return power
    return normalizePower({
      ...power,
      name: power.name || catalog.name,
      categoryTrait: getCatalogTrait(catalog),
      bonusPercent: catalog.baseBonus,
      lingyunBonusPercent: catalog.lingyunBonusPercent
    })
  })
  persistPowerCatalog()
  valueEditorVisible.value = false
  ElMessage.success('内功数值配置已保存')
}

function removeEntry(index) {
  draft.value.entries.splice(index, 1)
}

function formatBonus(value) {
  return `+${Number(value || 0).toFixed(5)}%`
}

function formatBenefit(value) {
  return formatBenefitPercent(value, 5)
}

function getEntryLabel(entry = {}, power = null) {
  const name = String(entry.name || '').trim() || '随机词条'
  const option = getEntryOption(name)
  const valueText = entry.value !== undefined && entry.value !== null && entry.value !== ''
    ? ` ${formatEntryValue(entry.value, option || {})}`
    : ''
  const benefitText = power ? ` · ${formatBenefit(getSingleEntryBenefit(entry))}` : ''
  return `${name}${valueText}${benefitText}`
}

function formatEntryOptionLabel(entry = {}) {
  return entry.entryName
}

function getBaseBonus(power = {}) {
  const catalog = getCatalogByName(power.category)
  return Number(power.bonusPercent ?? catalog?.baseBonus ?? 0)
}

function getEntryAttackPercent(power = {}) {
  return roundTo(getPowerBenefit(power).entryGain * 100, 5)
}

function getLingyunBonus(power = {}) {
  if (!power.lingyunEnabled) return 0
  const catalog = getCatalogByName(power.category)
  return Number(power.lingyunBonusPercent ?? catalog?.lingyunBonusPercent ?? 0)
}

function calculatePowerEntryStats(power = {}) {
  return {
    entryAttackPower: 0,
    entryAttackPercent: getEntryAttackPercent(power)
  }
}

function calculateEntryAttackPower(entry = {}) {
  return roundTo(getSingleEntryBenefit(entry) * 100, 5)
}

function calculateEntryAttackPercent(entry = {}) {
  return roundTo(getSingleEntryBenefit(entry) * 100, 5)
}

function getPowerBenefit(power = {}) {
  if (benefitMode.value === 'tower') {
    return {
      totalGain: 0,
      baseGain: 0,
      entryGain: 0,
      note: '拆塔收益暂未接入计算逻辑'
    }
  }
  return calculatePowerBenefit(power, panelSetting.value)
}

function getPowerBenefitTitle(power = {}) {
  const benefit = getPowerBenefit(power)
  const note = benefit.note ? ` · ${benefit.note}` : ''
  return `${benefitModeLabel.value} ${formatBenefit(benefit.totalGain)}${note}`
}

function getSingleEntryBenefit(entry = {}) {
  return getEntryBenefitResult(entry).gain
}

function getEntryBenefitResult(entry = {}) {
  if (benefitMode.value === 'tower') {
    return {
      gain: 0,
      note: '拆塔收益暂未接入计算逻辑'
    }
  }
  return calculateEntryBenefit(entry, panelSetting.value)
}

function getEntryBenefitTitle(entry = {}) {
  const benefit = getEntryBenefitResult(entry)
  const note = benefit.note ? ` · ${benefit.note}` : ''
  return `${benefitModeLabel.value} ${formatBenefit(benefit.gain)}${note}`
}

function getEntryLimitHint(entry = {}) {
  if (!entry?.name) return '请选择词条'
  return `最大数值 ${getEntryMaxValueText(entry.name)} · ${getEntryBenefitTitle(entry)}`
}

function getEntryPreviewRows(power = {}) {
  const rows = [{
    key: 'base-benefit',
    type: 'base',
    name: `基础${benefitModeLabel.value}`,
    value: formatBonus(getBaseBonus(power)),
    benefit: formatBenefit(getPowerBenefit(power).baseGain),
    note: `基础百分比增伤 ${formatBonus(getBaseBonus(power))}`
  }]

  for (const entry of power.entries || []) {
    const name = String(entry.name || '').trim() || '未选择词条'
    const benefit = getEntryBenefitResult(entry)
    rows.push({
      key: entry.id || `${name}-${rows.length}`,
      type: 'entry',
      name,
      value: formatEntryValue(entry.value, getEntryOption(name) || {}),
      benefit: formatBenefit(benefit.gain),
      note: `${name} ${formatEntryValue(entry.value, getEntryOption(name) || {})} · ${benefitModeLabel.value} ${formatBenefit(benefit.gain)}${benefit.note ? ` · ${benefit.note}` : ''}`
    })
  }

  return rows
}

function getEntryOption(name) {
  return entryOptionMap.value[String(name || '').trim()] || null
}

function getEntryConversion(name) {
  return entryConversionMap.value[String(name || '').trim()] || null
}

function getEntryLimitValue(name) {
  return Number(getEntryOption(name)?.limitValue || 0)
}

function getEntryLimitText(name) {
  const option = getEntryOption(name)
  return option ? formatEntryLimitValue(option) : '-'
}

function getEntryMaxValueText(name) {
  const option = getEntryOption(name)
  return option ? formatEntryLimitValue(option) : '-'
}

function getEntryPrecision(name) {
  return isPercentEntry(name) ? 5 : 0
}

function isPercentEntry(name) {
  return getEntryOption(name)?.valueType === 'percent'
}

function formatEntryValue(value, option = {}) {
  const numberValue = Number(value || 0)
  return option.valueType === 'percent' ? `${numberValue.toFixed(5)}%` : `${numberValue}`
}

function formatEntryLimitValue(option = {}) {
  const limitValue = Number(option.limitValue)
  if (!Number.isFinite(limitValue)) return option.limitText || '-'
  return `${limitValue.toString()}${option.valueType === 'percent' ? '%' : ''}`
}

function parseEntryValue(value) {
  const text = String(value ?? '').trim().replace('%', '')
  if (!text) return null
  const numberValue = Number(text)
  return Number.isFinite(numberValue) ? numberValue : null
}

function validateEntryValues(entries = [], options = {}) {
  const warn = message => {
    if (!options.silent) {
      ElMessage.warning(message)
    }
  }
  for (const entry of entries || []) {
    const name = String(entry.name || '').trim()
    const option = getEntryOption(name)
    if (!option) {
      warn(`词条「${name || '未选择'}」不在当前可用词条中`)
      return false
    }
    const value = parseEntryValue(entry.value)
    if (value === null || value < 0) {
      warn(`请填写「${name}」的词条数值`)
      return false
    }
    if (value > Number(option.limitValue || 0)) {
      warn(`「${name}」不能超过最大数值 ${formatEntryLimitValue(option)}`)
      return false
    }
  }
  return true
}

function resolvePowerImage(power = {}) {
  if (!internalPowerImageVisible.value) return ''
  const catalog = getCatalogByName(power.category)
  return resolveImagePath(power.imageUrl || catalog?.imageUrl || '')
}

function resolveCatalogImage(catalog = {}) {
  if (!internalPowerImageVisible.value) return ''
  return resolveImagePath(catalog?.imageUrl || '')
}

function resolveImagePath(value = '') {
  value = String(value || '').trim()
  if (!value) return ''
  if (/^(https?:)?\/\//.test(value) || value.startsWith('data:') || value.startsWith('blob:')) return value
  if (value.startsWith('/profile/')) return `${baseApi}${value}`
  return value
}

function formatCategoryMeta(catalog = {}) {
  const elementText = catalog.elementKey === 'mixed'
    ? '五行各 1'
    : `${getElementLabel(catalog.elementKey)} × ${Number(catalog.elements?.[catalog.elementKey] || 0)}`
  return `${elementText} · ${formatTraitSummary(getCatalogTrait(catalog))}`
}

function getCatalogTrait(catalog = {}) {
  const name = catalog.name || catalog.displayName || catalog.value
  return getInternalPowerTraitEffect(name) || String(catalog.trait || '').trim() || '待配置'
}

function getPowerTraitText(power = {}) {
  const currentTrait = String(power.categoryTrait || '').trim()
  if (currentTrait && currentTrait !== '待配置') return currentTrait
  return String(
    getInternalPowerTraitEffect(power.name) ||
    getInternalPowerTraitEffect(power.category) ||
    '未配置满级强化效果'
  ).trim()
}

function formatTraitSummary(value = '') {
  const text = String(value || '待配置').trim()
  return text.length > 28 ? `${text.slice(0, 28)}...` : text
}

function formatElementSequence(elements = {}) {
  const sequence = elementOptions
    .flatMap(item => Array.from({ length: Number(elements[item.key] || 0) }, () => item.label))
    .join('')
  return sequence || '未配置元素'
}

function formatElementCounts(elements = {}) {
  return elementOptions.map(item => `${item.label}${Number(elements[item.key] || 0)}`).join(' ')
}

function getPowerScore(power = {}) {
  return roundTo(getPowerBenefit(power).totalGain * 100, 5)
}

function getPreviewScore(power = {}) {
  const base = Number(getBaseBonus(power) || 0) * 100
  const entryScore = Number(getPowerBenefit(power).entryGain || 0) * 100000
  return Math.max(0, Math.round(base + entryScore))
}

function getPrimaryEntryTag(power = {}) {
  const firstEntry = (power.entries || []).find(entry => String(entry.name || '').trim())
  if (firstEntry?.name) return firstEntry.name
  const catalog = getCatalogByName(power.category)
  return getElementLabel(catalog?.elementKey) || '内功'
}

function previewElementMarks(elements = {}) {
  return elementOptions.flatMap(item => {
    const count = Math.min(4, Number(elements?.[item.key] || 0))
    return Array.from({ length: count }, (_, index) => ({
      key: `${item.key}-${index}`,
      color: item.color
    }))
  }).slice(0, 4)
}

function getCatalogByName(name) {
  return powerCatalog.value.find(item => item.value === name || item.name === name || item.displayName === name) || null
}

function getElementLabel(key) {
  return elementOptions.find(item => item.key === key)?.label || key || ''
}

function changeElement(key, delta) {
  const current = Number(draft.value.elements[key] || 0)
  const nextValue = Math.max(0, Math.min(5, current + delta))
  draft.value.elements[key] = nextValue
}

function isTruthyFlag(value) {
  return value === true || value === 1 || value === '1'
}

function normalizePower(value) {
  const catalog = getCatalogByName(value.category)
  const currentTrait = String(value.categoryTrait || '').trim()
  return {
    id: String(value.id || value.powerId || createId()),
    powerId: value.powerId || value.power_id || undefined,
    name: String(value.name || ''),
    category: String(value.category || '通用'),
    categoryTrait: currentTrait && currentTrait !== '待配置'
      ? currentTrait
      : getInternalPowerTraitEffect(value.name) || getInternalPowerTraitEffect(value.category) || getCatalogTrait(catalog || {}) || currentTrait,
    bonusPercent: clampBonus(value.bonusPercent),
    lingyunEnabled: isTruthyFlag(value.lingyunEnabled ?? value.lingyun_enabled),
    lingyunBonusPercent: clampBonus(value.lingyunBonusPercent ?? value.lingyun_bonus_percent ?? catalog?.lingyunBonusPercent ?? 0),
    entryAttackPower: Number(value.entryAttackPower || 0),
    entryAttackPercent: Number(value.entryAttackPercent || 0),
    totalBonusPercent: value.totalBonusPercent === undefined || value.totalBonusPercent === null
      ? undefined
      : Number(value.totalBonusPercent || 0),
    imageUrl: String(value.imageUrl || ''),
    entries: normalizeEntries(value.entries),
    elements: normalizeElements(value.elements),
    remark: String(value.remark || ''),
    updatedAt: value.updatedAt || new Date().toISOString()
  }
}

function toPowerPayload(power) {
  return {
    id: power.id,
    powerId: power.powerId,
    name: power.name,
    category: power.category,
    categoryTrait: power.categoryTrait,
    bonusPercent: power.bonusPercent,
    lingyunEnabled: Boolean(power.lingyunEnabled),
    lingyunBonusPercent: power.lingyunBonusPercent,
    entries: power.entries || [],
    elements: power.elements || createEmptyElements(),
    remark: power.remark || '',
    updatedAt: power.updatedAt
  }
}

function normalizeEntries(entries = []) {
  return Array.isArray(entries)
    ? entries.map(entry => ({
        id: String(entry.id || createId()),
        name: String(entry.name || ''),
        value: String(entry.value || '')
      }))
    : []
}

function normalizeEntryOption(value = {}) {
  const percent = value.conversionPercent
  return {
    entryId: value.entryId,
    entryName: String(value.entryName || '').trim(),
    conversionPercent: percent === null || percent === undefined || percent === '' ? null : Number(percent),
    conversionDesc: String(value.conversionDesc || ''),
    limitText: String(value.limitText || ''),
    limitValue: Number(value.limitValue || 0),
    valueType: value.valueType === 'percent' ? 'percent' : 'number',
    status: value.status || '0'
  }
}

function normalizeEntryConversion(value = {}) {
  return {
    entryName: String(value.entryName || '').trim(),
    limitText: String(value.limitText || ''),
    limitValue: Number(value.limitValue || 0),
    valueType: value.valueType === 'percent' ? 'percent' : 'number',
    attackPower: Number(value.attackPower || 0),
    attackPercent: Number(value.attackPercent || 0)
  }
}

function roundTo(value, precision = 5) {
  const ratio = 10 ** precision
  return Math.round(Number(value || 0) * ratio) / ratio
}

function cloneEntries(entries = []) {
  return normalizeEntries(entries).map(entry => ({ ...entry }))
}

function normalizeElements(value = {}) {
  const elements = createEmptyElements()
  elementOptions.forEach(item => {
    elements[item.key] = Math.max(0, Math.min(5, Number(value[item.key] || 0)))
  })
  return elements
}

function sumElements(elements = {}) {
  return elementOptions.reduce((sum, item) => sum + Number(elements[item.key] || 0), 0)
}

function createEmptyElements() {
  return { metal: 0, wood: 0, water: 0, fire: 0, earth: 0 }
}

function createElementsFromPrimary(primaryElement = 'mixed') {
  if (primaryElement && primaryElement !== 'mixed') {
    return {
      ...createEmptyElements(),
      [primaryElement]: 4
    }
  }
  return { metal: 1, wood: 1, water: 1, fire: 1, earth: 1 }
}

function clonePower(value) {
  return value ? JSON.parse(JSON.stringify(value)) : null
}

function clampBonus(value) {
  const numberValue = Number(value || 0)
  if (!Number.isFinite(numberValue)) return 0
  return Math.max(0, Math.min(100, Number(numberValue.toFixed(1))))
}

function createId() {
  return `skill-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

function normalizeCatalogItem(value = {}) {
  const elementKey = ['metal', 'wood', 'water', 'fire', 'earth', 'mixed'].includes(value.elementKey)
    ? value.elementKey
    : (['metal', 'wood', 'water', 'fire', 'earth', 'mixed'].includes(value.primaryElement) ? value.primaryElement : 'mixed')
  const elements = normalizeElements(Object.keys(value.elements || {}).length ? value.elements : createElementsFromPrimary(elementKey))
  const displayName = value.displayName || buildPresetDisplayName(value.name, elementKey)
  const trait = getInternalPowerTraitEffect(value.name || displayName || value.value) ||
    String(value.trait || value.bonusDesc || value.bonusType || '').trim() ||
    '待配置'
  return {
    id: String(value.id || value.presetId || createId()),
    presetId: value.presetId,
    name: String(value.name || '').trim(),
    displayName,
    value: displayName,
    season: 'new',
    rarity: value.rarity === 'rare' || String(value.name || '').startsWith('稀有-') ? 'rare' : 'common',
    primaryElement: elementKey,
    elementKey,
    elements,
    baseBonus: clampBonus(value.baseBonus ?? value.bonusPercent),
    lingyunBonusPercent: clampBonus(value.lingyunBonusPercent ?? value.lingyun_bonus_percent),
    imageUrl: String(value.imageUrl || '').trim(),
    entries: normalizeEntries(value.entries),
    trait
  }
}

function buildPresetDisplayName(name, elementKey) {
  const elementMap = {
    metal: '金',
    wood: '木',
    water: '水',
    fire: '火',
    earth: '土',
    mixed: '全元素'
  }
  return name ? `${name}（${elementMap[elementKey] || elementKey}）` : ''
}

function mergePowerCatalog(stored = []) {
  const storedMap = new Map(stored.map(item => [String(item.name || '').trim(), item]))
  const defaults = createDefaultPowerCatalog()
  const merged = defaults.map(item => normalizeCatalogItem({ ...item, ...(storedMap.get(item.name) || {}) }))
  stored.forEach(item => {
    const name = String(item.name || '').trim()
    if (name && !merged.some(defaultItem => defaultItem.name === name)) {
      merged.push(normalizeCatalogItem(item))
    }
  })
  return merged
}

function createDefaultPowerCatalog() {
  return []
}

function createSamplePowers() {
  const samples = powerCatalog.value.length ? powerCatalog.value : createDefaultPowerCatalog()
  return samples.map((item, index) => normalizePower({
    id: `sample-${item.id}`,
    name: item.name,
    category: item.value,
    categoryTrait: getCatalogTrait(item),
    bonusPercent: item.baseBonus,
    lingyunEnabled: false,
    lingyunBonusPercent: item.lingyunBonusPercent,
    entries: [],
    elements: item.elements,
    remark: item.rarity === 'rare' ? '新赛年稀有内功，基础数值可在权限面板调整。' : '新赛年普通内功，基础数值可在权限面板调整。',
    updatedAt: new Date(Date.UTC(2026, 5, 20, 8, 0, 0) - index * 60000).toISOString()
  }))
}

function getSamplePowersForQuota() {
  const samples = createSamplePowers()
  if (quota.value.unlimited) return samples
  return samples.slice(0, Math.max(20, Number(quota.value.maxCount || 20)))
}
</script>

<style scoped>
.internal-power-page {
  --ink: #18202d;
  --paper: #f8f3e9;
  --paper-deep: #efe2cf;
  --line: rgba(61, 43, 25, 0.14);
  --gold: #b9852c;
  color: var(--ink);
  background:
    radial-gradient(circle at 10% 8%, rgba(185, 133, 44, 0.16), transparent 32%),
    radial-gradient(circle at 86% 12%, rgba(32, 73, 86, 0.14), transparent 28%),
    linear-gradient(135deg, #fbf7ee, #edf3f2 48%, #f8f3e9);
  min-height: calc(100vh - 84px);
}

.power-hero,
.summary-card,
.power-board {
  border: 1px solid var(--line);
  box-shadow: 0 18px 38px rgba(55, 43, 28, 0.08);
}

.power-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  border-radius: 20px;
  padding: 26px 28px;
  background:
    linear-gradient(135deg, rgba(24, 32, 45, 0.96), rgba(55, 71, 75, 0.9)),
    var(--ink);
  color: #fff8e8;
  overflow: hidden;
  position: relative;
}

.power-hero::after {
  content: "";
  position: absolute;
  inset: auto -30px -52px auto;
  width: 230px;
  height: 230px;
  border-radius: 50%;
  border: 34px solid rgba(185, 133, 44, 0.16);
}

.eyebrow {
  margin: 0 0 8px;
  color: #e7bf73;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.power-hero h1 {
  margin: 0;
  font-size: 34px;
  letter-spacing: 0.08em;
}

.power-hero p:last-child {
  margin: 10px 0 0;
  max-width: 620px;
  color: rgba(255, 248, 232, 0.74);
  font-weight: 600;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
  position: relative;
  z-index: 1;
}

.benefit-mode-select {
  width: 136px;
}

.recognition-record-badge {
  display: inline-flex;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 14px;
  margin: 16px 0;
}

.summary-card {
  border-radius: 16px;
  padding: 16px;
  background: rgba(255, 252, 244, 0.78);
  backdrop-filter: blur(12px);
}

.summary-card span,
.summary-card small {
  display: block;
  color: #6b5b48;
  font-size: 12px;
  font-weight: 700;
}

.summary-card strong {
  display: block;
  margin: 6px 0 2px;
  font-size: 30px;
  color: var(--ink);
}

.element-strip {
  display: flex;
  gap: 3px;
  height: 18px;
  margin: 10px 0 8px;
}

.element-strip i {
  min-width: 12px;
  border-radius: 999px;
  background: var(--element-color);
}

.power-board {
  border-radius: 18px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
}

.board-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 16px;
  margin-bottom: 14px;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.panel-title div:first-child {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.panel-title strong {
  font-size: 16px;
}

.panel-title span {
  color: #786957;
  font-size: 12px;
  font-weight: 700;
}

.filters {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.filters :deep(.el-input),
.filters :deep(.el-select) {
  width: 170px;
}

.power-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(220px, 1fr));
  gap: 12px;
}

.power-card {
  position: relative;
  min-height: 320px;
  border: 2px solid #b8dcff;
  border-radius: 8px;
  padding: 14px;
  background: #ffffff;
  cursor: pointer;
  color: #111827;
  overflow: hidden;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}

.power-card:hover,
.power-card.active {
  transform: translateY(-1px);
  border-color: #4aa3ff;
  box-shadow: 0 12px 28px rgba(59, 130, 246, 0.14);
}

.power-card.batch-selected {
  border-color: #7c3aed;
  background: linear-gradient(180deg, rgba(124, 58, 237, 0.1), #ffffff 38%);
  box-shadow: 0 14px 30px rgba(124, 58, 237, 0.18);
}

.batch-checkbox {
  position: absolute;
  top: 10px;
  left: 102px;
  z-index: 2;
  border-radius: 999px;
  padding: 2px 7px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
}

.score-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  min-width: 74px;
  border: 1px solid #d8dfe8;
  border-radius: 4px;
  padding: 6px 9px;
  background: rgba(255, 255, 255, 0.92);
  display: grid;
  gap: 3px;
}

.score-badge strong {
  color: #2f89ff;
  font-size: 14px;
  line-height: 1;
}

.score-badge span {
  color: #16a34a;
  font-size: 11px;
  line-height: 1.15;
  white-space: nowrap;
}

.delete-card {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 999px;
  background: #ff4d5a;
  color: #ffffff;
  font-size: 25px;
  font-weight: 900;
  line-height: 30px;
  cursor: pointer;
  display: grid;
  place-items: center;
  box-shadow: 0 10px 24px rgba(255, 77, 90, 0.28);
  z-index: 2;
}

.delete-card:hover {
  transform: scale(1.06);
  box-shadow: 0 14px 30px rgba(255, 77, 90, 0.34);
}

.card-center {
  min-height: 286px;
  padding: 52px 8px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.power-card-media {
  width: min(118px, 58%);
  aspect-ratio: 1;
  margin-bottom: 16px;
  border: 1px solid #d7e4f2;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(245, 248, 252, 0.96), rgba(255, 255, 255, 0.9)),
    repeating-linear-gradient(45deg, rgba(148, 163, 184, 0.1) 0 8px, transparent 8px 16px);
  display: grid;
  place-items: center;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.82), 0 12px 24px rgba(15, 23, 42, 0.08);
}

.power-card-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.power-card-media.empty span {
  color: #8a9aae;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.card-center h2 {
  margin: 0 0 10px;
  color: #0f172a;
  font-size: 20px;
  font-weight: 900;
  word-break: break-word;
}

.element-sequence {
  margin: 0 0 12px;
  color: #334155;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.06em;
  word-break: break-word;
}

.entry-pills {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 7px;
}

.entry-pills span {
  border-radius: 5px;
  padding: 6px 9px;
  background: #eef4ff;
  color: #334155;
  font-size: 13px;
  font-weight: 800;
  line-height: 1.2;
  word-break: break-word;
}

.entry-pills .muted {
  color: #94a3b8;
}

.empty-slot-card {
  min-height: 320px;
  border: 2px solid #d8e1eb;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.48);
  color: #94a3b8;
  cursor: pointer;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
}

.empty-slot-card:hover {
  border-color: #93c5fd;
  color: #2563eb;
}

.empty-slot-card:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.empty-slot-card span {
  font-size: 28px;
  line-height: 1;
}

.empty-slot-card strong {
  color: inherit;
  font-size: 16px;
}

.empty-slot-card small {
  font-size: 12px;
}

.delete-confirm-message {
  margin: 0 0 14px;
  color: #334155;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.7;
}

.full-elements {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 6px;
  margin-top: 10px;
}

.full-elements > span {
  border: 1px solid color-mix(in srgb, var(--element-color), transparent 74%);
  border-radius: 12px;
  padding: 7px 6px;
  background: var(--element-bg);
  color: var(--element-color);
  display: grid;
  place-items: center;
  gap: 2px;
}

.full-elements b {
  font-size: 12px;
  font-weight: 900;
}

.full-elements strong {
  color: #151c26;
  font-size: 17px;
  line-height: 1;
}

.full-entries {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 10px;
}

.full-entries > span {
  border-radius: 999px;
  padding: 5px 8px;
  background: rgba(255, 247, 232, 0.92);
  border: 1px solid rgba(185, 133, 44, 0.2);
  color: #3f3326;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
  white-space: normal;
  word-break: break-word;
}

.full-entries .muted {
  color: #82705c;
}

.editor-shell {
  --editor-bg: #f6f0e6;
  --editor-card: rgba(255, 252, 246, 0.94);
  --editor-line: rgba(38, 50, 68, 0.1);
  min-height: 100%;
  padding: 18px;
  background:
    radial-gradient(circle at 92% 8%, rgba(185, 133, 44, 0.16), transparent 26%),
    linear-gradient(135deg, #fbf7ef, var(--editor-bg));
}

.editor-topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
  border: 1px solid var(--editor-line);
  border-radius: 20px;
  padding: 18px 20px;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 16px 38px rgba(38, 50, 68, 0.08);
}

.editor-kicker {
  color: #9a6b28;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.editor-topbar h2 {
  margin: 4px 0;
  color: #111827;
  font-size: clamp(24px, 3vw, 34px);
  line-height: 1.08;
}

.editor-topbar p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-delete-button {
  min-width: 96px;
  min-height: 38px;
  font-weight: 900;
}

.editor-close {
  width: 38px;
  height: 38px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: #fff;
  color: #1f2937;
  cursor: pointer;
  font-size: 25px;
  line-height: 1;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.editor-close:hover {
  transform: rotate(8deg) scale(1.04);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.12);
}

.editor-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 360px);
  gap: 16px;
  align-items: start;
  padding-bottom: 78px;
}

.power-form {
  display: grid;
  gap: 14px;
}

.editor-section,
.preview-card,
.editor-note-card,
.editor-footer {
  border: 1px solid var(--editor-line);
  border-radius: 20px;
  background: var(--editor-card);
  box-shadow: 0 14px 34px rgba(51, 65, 85, 0.07);
}

.editor-section {
  padding: 14px 16px;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.section-heading > div {
  min-width: 0;
  display: grid;
  gap: 3px;
}

.section-heading strong {
  color: #172033;
  font-size: 15px;
}

.section-heading span {
  color: #8a7862;
  font-size: 12px;
  font-weight: 800;
  text-align: right;
}

.basic-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
}

.power-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.power-form :deep(.el-form-item__label) {
  margin-bottom: 4px;
  color: #334155;
  font-weight: 900;
  line-height: 1.25;
}

.power-form :deep(.el-input__wrapper),
.power-form :deep(.el-select__wrapper),
.power-form :deep(.el-textarea__inner),
.power-form :deep(.el-input-number) {
  border-radius: 14px;
}

.category-picker-trigger {
  width: 100%;
  min-height: 48px;
  border: 1px solid #dcdfe6;
  border-radius: 14px;
  padding: 5px 10px 5px 6px;
  background: #ffffff;
  color: #172033;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) 18px;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

.category-picker-trigger:hover {
  border-color: #b9852c;
  background: #fffdfa;
}

.category-picker-trigger:focus-visible {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.16);
}

.category-picker-thumb,
.category-file-thumb {
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(248, 250, 252, 0.96), rgba(255, 247, 237, 0.9)),
    repeating-linear-gradient(45deg, rgba(148, 163, 184, 0.14) 0 6px, transparent 6px 12px);
  display: grid;
  place-items: center;
  overflow: hidden;
  flex: 0 0 auto;
}

.category-picker-thumb {
  width: 36px;
  height: 36px;
}

.category-file-thumb {
  width: 34px;
  height: 34px;
}

.category-picker-thumb img,
.category-file-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.category-picker-thumb.empty span,
.category-file-thumb.empty span {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 900;
}

.category-picker-main,
.category-file-main {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.category-picker-main strong,
.category-file-main strong {
  overflow: hidden;
  color: #172033;
  font-size: 13px;
  font-weight: 900;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-picker-main small,
.category-file-main small {
  overflow: hidden;
  color: #7b6b57;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.25;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-picker-caret {
  color: #94a3b8;
  font-size: 14px;
}

:global(.power-category-popper) {
  padding: 8px;
  border-radius: 14px;
}

.power-category-tree {
  max-height: min(430px, 58vh);
  overflow: auto;
  display: grid;
  gap: 6px;
}

.element-folder {
  position: relative;
}

.element-folder-header,
.category-file-row {
  width: 100%;
  border: 1px solid transparent;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.74);
  color: #172033;
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease, transform 0.16s ease, box-shadow 0.16s ease;
}

.element-folder-header {
  min-height: 36px;
  padding: 0 8px 0 6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.element-folder-header:hover,
.category-file-row:hover {
  border-color: rgba(185, 133, 44, 0.28);
  background: rgba(255, 252, 246, 0.98);
  box-shadow: 0 10px 20px rgba(51, 65, 85, 0.08);
  transform: translateY(-1px);
}

.element-folder-left {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.element-folder-left strong {
  overflow: hidden;
  font-size: 13px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.element-folder-caret {
  color: #94a3b8;
  font-size: 11px;
  transform: rotate(90deg);
  transition: transform 0.18s ease;
}

.element-folder.collapsed .element-folder-caret {
  transform: rotate(0deg);
}

.element-folder-icon {
  font-size: 17px;
  filter: drop-shadow(0 5px 8px rgba(15, 23, 42, 0.12));
}

.element-folder-count,
.category-file-bonus {
  flex: 0 0 auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 900;
}

.element-folder-count {
  min-width: 24px;
  border-radius: 999px;
  padding: 2px 7px;
  background: rgba(15, 23, 42, 0.06);
  color: #64748b;
  font-size: 11px;
  text-align: center;
}

.element-folder-body {
  display: grid;
  gap: 5px;
  padding: 5px 0 2px 22px;
}

.category-file-row {
  min-height: 46px;
  padding: 5px 8px 5px 6px;
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
}

.category-file-row.root-file {
  border-color: rgba(185, 133, 44, 0.2);
  background: rgba(255, 247, 237, 0.86);
}

.category-file-row.active {
  border-color: #7c3aed;
  background: rgba(124, 58, 237, 0.08);
  box-shadow: inset 0 0 0 1px rgba(124, 58, 237, 0.18);
}

.category-file-bonus {
  color: #7c3aed;
  font-size: 12px;
  white-space: nowrap;
}

.bonus-editor {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 124px;
  gap: 10px;
  align-items: center;
}

.lingyun-editor {
  width: 100%;
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 12px;
  padding: 6px 10px;
  background: rgba(124, 58, 237, 0.06);
}

.lingyun-editor span {
  color: #6d28d9;
  font-size: 12px;
  font-weight: 900;
}

.elements-editor,
.entries-editor {
  width: 100%;
}

.element-total {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  border-radius: 16px;
  padding: 10px 12px;
  background: rgba(34, 197, 94, 0.11);
  color: #14783d;
  font-weight: 900;
}

.element-total.invalid {
  background: rgba(239, 68, 68, 0.12);
  color: #b42318;
}

.element-controls {
  display: grid;
  grid-template-columns: repeat(5, minmax(86px, 1fr));
  gap: 10px;
}

.element-control {
  border: 1px solid color-mix(in srgb, var(--element-color), transparent 72%);
  border-radius: 18px;
  padding: 12px 10px;
  background: var(--element-bg);
}

.element-control > span {
  display: block;
  color: var(--element-color);
  font-size: 14px;
  font-weight: 1000;
  text-align: center;
}

.element-control > div {
  display: grid;
  grid-template-columns: 28px minmax(20px, 1fr) 28px;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
}

.element-control strong {
  color: #111827;
  font-size: 20px;
  text-align: center;
}

.entry-table-head,
.entry-row {
  display: grid;
  grid-template-columns: minmax(160px, 1.35fr) minmax(132px, 0.9fr) 96px 54px;
  align-items: center;
  gap: 8px;
}

.entry-table-head {
  min-height: 28px;
  padding: 0 8px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.04);
  color: #746654;
  font-size: 11px;
  font-weight: 900;
}

.entry-row {
  min-height: 46px;
  margin-bottom: 8px;
  padding: 5px 8px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.74);
}

.entry-row :deep(.el-select) {
  width: 100%;
}

.entry-value-control {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 4px;
  align-items: center;
}

.entry-value-control :deep(.el-input-number) {
  width: 100%;
}

.entry-value-suffix {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.entry-row-benefit {
  overflow: hidden;
  border-radius: 999px;
  padding: 5px 8px;
  background: rgba(22, 101, 52, 0.08);
  color: #166534;
  font-size: 12px;
  font-weight: 950;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.placeholder-note {
  margin: 8px 0 0;
  color: #8a7862;
  font-size: 12px;
  font-weight: 800;
}

.preview-panel {
  position: sticky;
  top: 14px;
  display: grid;
  gap: 12px;
}

.preview-card {
  padding: 24px;
  background:
    linear-gradient(145deg, rgba(25, 34, 48, 0.98), rgba(48, 62, 58, 0.96));
  color: #fff8e8;
}

.game-detail-card {
  position: relative;
  overflow: hidden;
  min-height: 520px;
  padding: 22px 20px 18px;
  border-color: rgba(139, 202, 255, 0.16);
  border-radius: 12px;
  background:
    radial-gradient(circle at 82% 6%, rgba(154, 207, 255, 0.16), transparent 26%),
    radial-gradient(circle at 18% 0%, rgba(246, 203, 112, 0.12), transparent 28%),
    linear-gradient(180deg, #0d1a22 0%, #182a33 48%, #24333a 100%);
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.22), inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

.game-card-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(115deg, transparent 0 22%, rgba(255, 255, 255, 0.06) 22% 22.4%, transparent 22.4% 100%),
    linear-gradient(180deg, rgba(114, 168, 205, 0.08), transparent 44%),
    radial-gradient(circle at 12% 18%, rgba(255, 255, 255, 0.34) 0 1px, transparent 1.5px),
    radial-gradient(circle at 68% 78%, rgba(255, 255, 255, 0.24) 0 1px, transparent 1.5px),
    radial-gradient(circle at 35% 92%, rgba(255, 255, 255, 0.2) 0 1px, transparent 1.5px);
  opacity: 0.9;
}

.game-card-head,
.game-card-tags,
.game-benefit-row,
.game-collapse,
.game-element-strip {
  position: relative;
  z-index: 1;
}

.game-card-head {
  position: relative;
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding-right: 62px;
}

.game-card-icon.preview-image {
  width: 76px;
  margin: 0;
  border-radius: 14px;
  border-color: rgba(246, 220, 148, 0.28);
  background:
    linear-gradient(135deg, rgba(239, 246, 255, 0.16), rgba(254, 243, 199, 0.16)),
    repeating-linear-gradient(45deg, rgba(255, 255, 255, 0.12) 0 8px, transparent 8px 16px);
}

.game-card-title {
  min-width: 0;
}

.game-card-title h2 {
  margin: 0 0 6px;
  color: #f9fbff;
  font-size: clamp(20px, 2.1vw, 26px);
  font-weight: 950;
  line-height: 1.18;
  word-break: break-word;
  writing-mode: horizontal-tb;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.45);
}

.game-card-title p {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: rgba(234, 242, 252, 0.72);
  font-size: 15px;
  font-weight: 900;
}

.game-card-title b {
  border: 1px solid rgba(244, 211, 119, 0.34);
  border-radius: 999px;
  padding: 2px 9px;
  background: rgba(22, 29, 38, 0.72);
  color: #f2d06d;
  font-size: 16px;
  font-weight: 950;
  line-height: 1.2;
  box-shadow: inset 0 0 14px rgba(242, 208, 109, 0.08);
}

.game-card-equip {
  position: absolute;
  top: 8px;
  right: 0;
  width: 54px;
  height: 54px;
  border: 2px solid rgba(190, 230, 255, 0.9);
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #dff5ff;
  font-size: 18px;
  font-weight: 950;
  text-shadow: 0 0 12px rgba(125, 211, 252, 0.65);
}

.game-card-tags {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  margin-top: 16px;
}

.game-card-tags span {
  border-radius: 4px;
  padding: 5px 8px 4px;
  background: #8cc29a;
  color: #193726;
  font-size: 15px;
  font-weight: 950;
  line-height: 1;
}

.game-card-tags span:nth-child(2) {
  background: #f2ca75;
  color: #593f12;
}

.game-card-marks {
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 9px;
}

.game-card-marks i {
  width: 17px;
  height: 22px;
  display: inline-block;
  background: linear-gradient(180deg, #fff7b7, var(--element-color));
  clip-path: polygon(50% 0, 100% 100%, 50% 76%, 0 100%);
  filter: drop-shadow(0 0 8px color-mix(in srgb, var(--element-color), transparent 24%));
}

.game-card-divider {
  position: relative;
  z-index: 1;
  height: 2px;
  margin: 15px 0 10px;
  background: linear-gradient(90deg, transparent, rgba(155, 205, 235, 0.72), transparent);
}

.game-benefit-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  min-height: 36px;
  padding: 0 12px;
  background: linear-gradient(90deg, rgba(23, 68, 105, 0.82), rgba(23, 68, 105, 0.48));
  color: #d7efff;
  font-size: 18px;
  font-weight: 950;
}

.game-benefit-row strong {
  color: #f4f7ff;
  font-size: 20px;
}

.game-collapse {
  margin-top: 8px;
}

.game-collapse-head {
  width: 100%;
  min-height: 36px;
  border: 0;
  padding: 0 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, rgba(20, 61, 95, 0.84), rgba(24, 70, 108, 0.54));
  color: #cdefff;
  cursor: pointer;
  font-size: 18px;
  font-weight: 950;
  text-align: left;
  transition: filter 0.16s ease, transform 0.16s ease;
}

.game-collapse-head:hover {
  filter: brightness(1.12);
  transform: translateX(2px);
}

.game-collapse-head span {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.game-collapse-head .el-icon {
  color: #e7f8ff;
  font-size: 16px;
  transition: transform 0.18s ease;
}

.game-collapse-head .el-icon.expanded {
  transform: rotate(90deg);
}

.game-collapse-head b {
  min-width: 24px;
  height: 24px;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  background: radial-gradient(circle, #ffe5a0, #8f5d1e);
  color: #fff8dc;
  font-size: 16px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.game-collapse-head strong {
  color: rgba(224, 242, 254, 0.78);
  font-size: 14px;
}

.game-trait-body {
  padding: 10px 13px 12px 33px;
  background: rgba(7, 17, 25, 0.34);
  color: rgba(232, 246, 255, 0.86);
  font-size: 14px;
  font-weight: 800;
  line-height: 1.65;
}

.game-entry-list {
  display: grid;
  gap: 2px;
  padding-top: 2px;
}

.game-entry-row {
  min-height: 34px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(74px, auto) minmax(92px, auto);
  align-items: center;
  gap: 10px;
  padding: 0 10px 0 18px;
  background: linear-gradient(90deg, rgba(15, 27, 36, 0.76), rgba(21, 35, 44, 0.46));
  color: rgba(238, 248, 255, 0.86);
  font-size: 16px;
  font-weight: 900;
}

.game-entry-row.base {
  background: linear-gradient(90deg, rgba(31, 70, 94, 0.82), rgba(31, 70, 94, 0.46));
}

.game-entry-row:nth-child(2n) {
  background: linear-gradient(90deg, rgba(31, 43, 51, 0.72), rgba(31, 43, 51, 0.42));
}

.game-entry-row span,
.game-entry-row em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.game-entry-row em {
  color: rgba(238, 248, 255, 0.9);
  font-style: normal;
  text-align: right;
}

.game-entry-row strong {
  color: #f3fbff;
  font-size: 15px;
  font-weight: 900;
  text-align: right;
  white-space: nowrap;
}

.game-entry-empty {
  padding: 12px 16px;
  background: rgba(7, 17, 25, 0.34);
  color: rgba(232, 246, 255, 0.68);
  font-size: 13px;
  font-weight: 900;
}

.game-element-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 14px;
}

.game-element-strip span {
  border: 1px solid color-mix(in srgb, var(--element-color), transparent 56%);
  border-radius: 4px;
  padding: 4px 7px;
  background: color-mix(in srgb, var(--element-color), transparent 84%);
  color: #f4fbff;
  font-size: 12px;
  font-weight: 950;
}

.preview-image {
  width: min(140px, 54%);
  aspect-ratio: 1;
  margin: 0 0 18px;
  border: 1px solid rgba(255, 248, 232, 0.18);
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(255, 248, 232, 0.08), rgba(185, 133, 44, 0.12)),
    repeating-linear-gradient(45deg, rgba(255, 248, 232, 0.09) 0 8px, transparent 8px 16px);
  display: grid;
  place-items: center;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(255, 248, 232, 0.06), 0 18px 32px rgba(0, 0, 0, 0.18);
}

.preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.preview-image.empty span {
  color: rgba(255, 248, 232, 0.58);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.seal {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--gold);
  color: #20170c;
  font-size: 24px;
  font-weight: 1000;
}

.preview-card h2 {
  margin: 18px 0 6px;
  font-size: 30px;
  word-break: break-word;
}

.preview-card p {
  margin: 0;
  color: rgba(255, 248, 232, 0.72);
  font-weight: 800;
}

.trait-description {
  width: 100%;
  color: rgba(255, 248, 232, 0.76);
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
  text-align: left;
}

.preview-card > strong {
  display: block;
  margin: 18px 0;
  color: #f3c875;
  font-size: 42px;
  line-height: 1;
}

.preview-bonus-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin: -6px 0 14px;
}

.preview-bonus-breakdown span {
  border: 1px solid rgba(255, 248, 232, 0.16);
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(255, 248, 232, 0.08);
  color: rgba(255, 248, 232, 0.78);
  font-size: 11px;
  font-weight: 900;
}

.preview-elements {
  margin-top: 0;
}

.preview-entries {
  margin-top: 14px;
}

.preview-entries > span {
  background: rgba(255, 248, 232, 0.1);
  border-color: rgba(255, 248, 232, 0.18);
  color: #fff8e8;
}

.preview-entries > span.lingyun-entry {
  background: rgba(124, 58, 237, 0.28);
  border-color: rgba(196, 181, 253, 0.4);
  color: #ede9fe;
}

.preview-entries .muted {
  color: rgba(255, 248, 232, 0.62);
}

.editor-note-card {
  padding: 14px;
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.editor-note-card strong,
.editor-note-card span {
  display: block;
}

.editor-note-card strong {
  margin-bottom: 5px;
  color: #172033;
}

.editor-footer {
  position: sticky;
  bottom: 0;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: -62px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(14px);
}

.editor-footer span {
  color: #64748b;
  font-size: 13px;
  font-weight: 900;
}

.editor-footer > div {
  display: flex;
  gap: 8px;
}

:deep(.power-editor-drawer.el-drawer) {
  max-width: 100vw;
}

:deep(.power-editor-drawer .el-drawer__body) {
  padding: 0;
  background: #f6f0e6;
  overflow: auto;
}

.value-editor-intro {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 14px;
  border: 1px solid rgba(59, 130, 246, 0.12);
  border-radius: 16px;
  background:
    radial-gradient(circle at 12% 16%, rgba(199, 146, 46, 0.13), transparent 28%),
    linear-gradient(135deg, rgba(248, 250, 252, 0.98), rgba(239, 246, 255, 0.92));
}

.value-editor-intro strong,
.value-editor-intro span {
  display: block;
}

.value-editor-intro strong {
  color: #172033;
  font-size: 16px;
}

.value-editor-intro span {
  margin-top: 5px;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

.value-editor-actions {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
}

.catalog-table {
  display: grid;
  gap: 8px;
  max-height: min(62vh, 620px);
  margin-top: 14px;
  overflow: auto;
  padding-right: 4px;
}

.catalog-head,
.catalog-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) 74px 96px 112px 126px minmax(180px, 1fr) 64px;
  gap: 8px;
  align-items: center;
}

.catalog-head {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 10px 12px;
  border-radius: 12px;
  background: #18202d;
  color: #fff8e8;
  font-size: 12px;
  font-weight: 900;
}

.catalog-row {
  padding: 10px 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
}

.value-dialog-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.value-dialog-footer span {
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.value-dialog-footer > div {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
}

:deep(.power-value-dialog .el-dialog) {
  border-radius: 18px;
}

:deep(.power-value-dialog .el-dialog__body) {
  padding-top: 10px;
}

.recognition-panel {
  display: grid;
  gap: 16px;
}

.recognition-quota {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(59, 130, 246, 0.16);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.9), rgba(255, 247, 237, 0.78));
}

.recognition-quota span,
.recognition-quota small {
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.recognition-quota strong {
  color: #2563eb;
  font-size: 28px;
  font-weight: 950;
}

.recognition-background-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid rgba(124, 58, 237, 0.14);
  border-radius: 14px;
  background: rgba(245, 243, 255, 0.72);
}

.recognition-background-toggle :deep(.el-checkbox) {
  height: auto;
  margin-right: 0;
  font-weight: 900;
}

.recognition-background-toggle span {
  min-width: 0;
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
}

.recognition-paste-zone {
  display: grid;
  gap: 6px;
  min-height: 86px;
  padding: 16px 18px;
  border: 1px dashed rgba(37, 99, 235, 0.34);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.86);
  color: #172033;
  cursor: text;
  outline: none;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
}

.recognition-paste-zone:focus {
  border-color: rgba(37, 99, 235, 0.72);
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.recognition-paste-zone strong {
  font-size: 15px;
  font-weight: 950;
}

.recognition-paste-zone span {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.6;
}

.recognition-result-list {
  display: grid;
  gap: 12px;
}

.recognition-card {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid rgba(34, 197, 94, 0.18);
  border-radius: 16px;
  background: rgba(240, 253, 244, 0.62);
}

.recognition-card.pending {
  border-color: rgba(59, 130, 246, 0.18);
  background: rgba(239, 246, 255, 0.72);
}

.recognition-card.failed {
  border-color: rgba(239, 68, 68, 0.18);
  background: rgba(254, 242, 242, 0.68);
}

.recognition-card header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.recognition-card header div {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.recognition-card header strong {
  overflow: hidden;
  color: #172033;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recognition-card header span {
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
}

.recognition-element-hint {
  color: #475569;
  font-size: 12px;
  font-weight: 850;
  line-height: 1.4;
}

.recognition-card header > .el-tag {
  margin-left: auto;
}

.recognition-card-thumb {
  width: 58px;
  height: 58px;
  flex: 0 0 58px;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.82);
  display: grid;
  place-items: center;
}

.recognition-card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recognition-card-thumb.empty span,
.recognition-history-thumb.empty span {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 900;
}

.recognition-candidate {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
}

.recognition-candidate > span {
  color: #334155;
  font-size: 13px;
  font-weight: 900;
}

.recognition-entry-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.recognition-entry-edit {
  min-width: 0;
  border-radius: 12px;
  padding: 8px;
  background: #ffffff;
  color: #172033;
  display: grid;
  grid-template-columns: minmax(72px, 1fr) minmax(98px, 128px) auto;
  gap: 6px;
  align-items: center;
}

.recognition-entry-edit.muted {
  background: rgba(255, 247, 237, 0.9);
  color: #9a6b28;
}

.recognition-entry-name {
  min-width: 0;
  overflow: hidden;
  color: #172033;
  font-size: 12px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recognition-entry-edit :deep(.el-input-number) {
  width: 100%;
}

.recognition-entry-suffix {
  color: #64748b;
  font-size: 12px;
  font-weight: 900;
}

.recognition-entry-edit small {
  grid-column: 1 / -1;
  color: #64748b;
  font-size: 11px;
  font-weight: 800;
}

.recognition-raw summary {
  color: #64748b;
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
}

.recognition-raw pre {
  max-height: 180px;
  overflow: auto;
  margin: 8px 0 0;
  border-radius: 12px;
  padding: 12px;
  background: #0f172a;
  color: #bfdbfe;
  font-size: 12px;
  white-space: pre-wrap;
}

.recognition-error-detail {
  max-height: 180px;
  overflow: auto;
  margin: 0;
  border-radius: 12px;
  padding: 12px;
  background: #2b1217;
  color: #fecdd3;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.recognition-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.recognition-history {
  display: grid;
  gap: 16px;
}

.recognition-history-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.recognition-history-summary > div {
  min-width: 0;
  border-radius: 14px;
  padding: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(248, 250, 252, 0.88);
  display: grid;
  gap: 4px;
}

.recognition-history-summary span {
  color: #64748b;
  font-size: 12px;
  font-weight: 900;
}

.recognition-history-summary strong {
  color: #172033;
  font-size: 24px;
  font-weight: 950;
}

.recognition-history-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.recognition-history-loaded {
  margin-right: auto;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.recognition-history-list {
  display: grid;
  gap: 12px;
}

.recognition-history-more {
  display: flex;
  justify-content: center;
  padding: 6px 0 2px;
}

.recognition-history-card {
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr);
  gap: 14px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(34, 197, 94, 0.16);
  background: rgba(240, 253, 244, 0.62);
}

.recognition-history-card.pending {
  border-color: rgba(59, 130, 246, 0.16);
  background: rgba(239, 246, 255, 0.72);
}

.recognition-history-card.failed {
  border-color: rgba(239, 68, 68, 0.18);
  background: rgba(254, 242, 242, 0.72);
}

.recognition-history-thumb {
  width: 132px;
  height: 132px;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.84);
  display: grid;
  place-items: center;
}

.recognition-history-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.recognition-history-main {
  min-width: 0;
  display: grid;
  gap: 10px;
  align-content: start;
}

.recognition-history-main header {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.recognition-history-main header div {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.recognition-history-main header strong,
.recognition-history-main header span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recognition-history-main header strong {
  color: #172033;
  font-size: 16px;
  font-weight: 950;
}

.recognition-history-main header span {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.recognition-history-entries {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recognition-history-entries span {
  border-radius: 999px;
  padding: 5px 9px;
  background: rgba(255, 255, 255, 0.9);
  color: #172033;
  font-size: 12px;
  font-weight: 900;
}

.recognition-history-entries span.muted {
  color: #9a6b28;
  background: rgba(255, 247, 237, 0.94);
}

@media (max-width: 1180px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .board-header {
    grid-template-columns: 1fr;
  }

  .filters {
    justify-content: flex-start;
  }

  .power-grid {
    grid-template-columns: repeat(2, minmax(220px, 1fr));
  }

  .editor-layout {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    position: static;
    grid-template-columns: minmax(0, 1fr) minmax(240px, 0.72fr);
    align-items: stretch;
  }

  .element-controls {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .catalog-head {
    display: none;
  }

  .catalog-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .internal-power-page {
    padding: 12px;
  }

  .power-hero {
    align-items: stretch;
    flex-direction: column;
    padding: 22px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .board-header {
    gap: 10px;
  }

  .filters,
  .hero-actions {
    width: 100%;
  }

  .benefit-mode-select {
    width: 100%;
  }

  .filters > .el-button,
  .hero-actions > .el-button {
    flex: 1;
  }

  .editor-shell {
    padding: 10px;
  }

  .editor-topbar {
    flex-direction: column;
    border-radius: 16px;
    padding: 14px;
  }

  .editor-actions {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .editor-actions :deep(.el-button) {
    flex: 1;
  }

  .editor-layout {
    padding-bottom: 0;
  }

  .editor-section,
  .preview-card,
  .editor-note-card,
  .editor-footer {
    border-radius: 16px;
  }

  .section-heading {
    flex-direction: column;
    gap: 4px;
  }

  .section-heading span {
    text-align: left;
  }

  .basic-grid,
  .bonus-editor {
    grid-template-columns: 1fr;
  }

  .entry-table-head {
    display: none;
  }

  .entry-row {
    grid-template-columns: minmax(0, 1fr) 118px;
    gap: 7px;
  }

  .entry-row-benefit {
    text-align: left;
  }

  .entry-row > .el-button {
    justify-self: end;
  }

  .element-controls {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    grid-template-columns: 1fr;
  }

  .preview-card {
    padding: 20px;
  }

  .game-card-head {
    grid-template-columns: 64px minmax(0, 1fr);
    padding-right: 54px;
  }

  .game-card-icon.preview-image {
    width: 64px;
  }

  .game-card-title h2 {
    font-size: 22px;
  }

  .game-card-equip {
    width: 48px;
    height: 48px;
    font-size: 15px;
  }

  .game-card-tags {
    grid-template-columns: auto auto;
  }

  .game-card-marks {
    grid-column: 1 / -1;
    justify-self: start;
  }

  .game-entry-row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .game-entry-row em {
    text-align: right;
  }

  .game-entry-row strong {
    grid-column: 1 / -1;
    text-align: left;
  }

  .preview-card > strong {
    font-size: 34px;
  }

  .editor-footer {
    position: static;
    align-items: stretch;
    flex-direction: column;
    margin-top: 12px;
  }

  .editor-footer > div {
    width: 100%;
  }

  .editor-footer > div :deep(.el-button) {
    flex: 1;
  }

  .full-elements {
    grid-template-columns: repeat(5, minmax(44px, 1fr));
  }

  .power-grid {
    grid-template-columns: 1fr;
  }

  .filters :deep(.el-input),
  .filters :deep(.el-select) {
    width: 100%;
  }

  .value-editor-intro,
  .value-dialog-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .value-editor-actions,
  .value-dialog-footer > div {
    width: 100%;
  }

  .value-editor-actions :deep(.el-button),
  .value-dialog-footer :deep(.el-button) {
    flex: 1;
  }

  .catalog-row {
    grid-template-columns: 1fr;
  }

  .recognition-entry-list,
  .recognition-entry-edit {
    grid-template-columns: 1fr;
  }

  .recognition-history-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .recognition-history-card {
    grid-template-columns: 1fr;
  }

  .recognition-history-thumb {
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 10;
  }
}
</style>
