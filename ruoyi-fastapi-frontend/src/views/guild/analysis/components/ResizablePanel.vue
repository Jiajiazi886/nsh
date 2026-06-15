<template>
  <section
    class="resizable-panel"
    :class="[panelClass, { 'is-interacting': isInteracting }]"
    :style="panelStyle"
    @pointerdown.capture="focusPanel"
    @pointerdown="handlePanelPointerDown"
    @pointermove="handlePanelPointerMove"
    @pointerleave="clearHoverResizeAxis"
  >
    <slot />
    <button
      type="button"
      class="resize-handle resize-handle-left"
      aria-label="左侧缩放"
      @pointerdown="startResize($event, 'left')"
    />
    <button
      type="button"
      class="resize-handle resize-handle-top"
      aria-label="顶部缩放"
      @pointerdown="startResize($event, 'top')"
    />
    <button
      type="button"
      class="resize-handle resize-handle-right"
      aria-label="横向缩放"
      @pointerdown="startResize($event, 'right')"
    />
    <button
      type="button"
      class="resize-handle resize-handle-bottom"
      aria-label="纵向缩放"
      @pointerdown="startResize($event, 'bottom')"
    />
    <button
      type="button"
      class="resize-handle resize-handle-corner"
      aria-label="缩放窗口"
      @pointerdown="startResize($event, 'right-bottom')"
    />
    <button
      type="button"
      class="resize-handle resize-handle-corner resize-handle-top-left"
      aria-label="左上缩放窗口"
      @pointerdown="startResize($event, 'left-top')"
    />
    <button
      type="button"
      class="resize-handle resize-handle-corner resize-handle-top-right"
      aria-label="右上缩放窗口"
      @pointerdown="startResize($event, 'right-top')"
    />
    <button
      type="button"
      class="resize-handle resize-handle-corner resize-handle-bottom-left"
      aria-label="左下缩放窗口"
      @pointerdown="startResize($event, 'left-bottom')"
    />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

let topPanelZIndex = 20

const props = defineProps({
  storageKey: {
    type: String,
    required: true
  },
  storageNamespace: {
    type: String,
    default: 'guild-analysis:panel-sizes:v2'
  },
  minWidth: {
    type: Number,
    default: 220
  },
  minHeight: {
    type: Number,
    default: 160
  },
  defaultWidth: {
    type: Number,
    default: 320
  },
  defaultHeight: {
    type: Number,
    default: 260
  },
  panelClass: {
    type: [String, Array, Object],
    default: ''
  }
})

const emit = defineEmits(['resize'])

const RESIZE_EDGE_SIZE = 14
const RESIZE_CORNER_SIZE = 28

const size = ref({
  width: props.defaultWidth,
  height: props.defaultHeight
})
const position = ref({
  x: 0,
  y: 0
})
const isInteracting = ref(false)
const hoverResizeAxis = ref('')

let activeResize = null
let activeMove = null

const panelStyle = computed(() => {
  const cursor = activeResize
    ? getResizeCursor(activeResize.axis)
    : (hoverResizeAxis.value ? getResizeCursor(hoverResizeAxis.value) : undefined)
  return {
    width: `${size.value.width}px`,
    minWidth: `${props.minWidth}px`,
    height: `${size.value.height}px`,
    minHeight: `${props.minHeight}px`,
    transform: `translate3d(${position.value.x}px, ${position.value.y}px, 0)`,
    zIndex: zIndex.value,
    ...(cursor ? { cursor } : {})
  }
})

const zIndex = ref(++topPanelZIndex)

function readStoredSizes() {
  try {
    return JSON.parse(localStorage.getItem(props.storageNamespace) || '{}')
  } catch {
    return {}
  }
}

function persistPanelState() {
  try {
    const stored = readStoredSizes()
    stored[props.storageKey] = {
      ...size.value,
      ...position.value
    }
    localStorage.setItem(props.storageNamespace, JSON.stringify(stored))
  } catch {
    // localStorage may be unavailable in restricted browser contexts.
  }
}

function loadSize() {
  const stored = readStoredSizes()
  const saved = stored[props.storageKey]
  size.value = {
    width: Math.max(props.minWidth, Number(saved?.width || props.defaultWidth)),
    height: Math.max(props.minHeight, Number(saved?.height || props.defaultHeight))
  }
  position.value = {
    x: Number(saved?.x || 0),
    y: Number(saved?.y || 0)
  }
}

function finishResize() {
  if (!activeResize) return
  activeResize = null
  isInteracting.value = false
  document.removeEventListener('pointermove', handleResize)
  document.removeEventListener('pointerup', finishResize)
  persistPanelState()
  emit('resize', size.value)
}

function handleResize(event) {
  if (!activeResize) return
  const deltaX = event.clientX - activeResize.startX
  const deltaY = event.clientY - activeResize.startY
  const movesLeft = activeResize.axis.includes('left')
  const movesRight = activeResize.axis.includes('right')
  const movesTop = activeResize.axis.includes('top')
  const movesBottom = activeResize.axis.includes('bottom')

  let nextWidth = activeResize.startWidth
  let nextHeight = activeResize.startHeight
  let nextX = activeResize.startXOffset
  let nextY = activeResize.startYOffset

  if (movesRight) {
    nextWidth = Math.max(props.minWidth, activeResize.startWidth + deltaX)
  }
  if (movesLeft) {
    nextWidth = Math.max(props.minWidth, activeResize.startWidth - deltaX)
    nextX = activeResize.startXOffset + activeResize.startWidth - nextWidth
  }
  if (movesBottom) {
    nextHeight = Math.max(props.minHeight, activeResize.startHeight + deltaY)
  }
  if (movesTop) {
    nextHeight = Math.max(props.minHeight, activeResize.startHeight - deltaY)
    nextY = activeResize.startYOffset + activeResize.startHeight - nextHeight
  }

  size.value = {
    width: Math.round(nextWidth),
    height: Math.round(nextHeight)
  }
  position.value = {
    x: Math.round(nextX),
    y: Math.round(nextY)
  }
  emit('resize', size.value)
}

function startResize(event, axis) {
  event.preventDefault()
  event.stopPropagation()
  focusPanel()
  isInteracting.value = true
  activeResize = {
    axis,
    startX: event.clientX,
    startY: event.clientY,
    startWidth: size.value.width,
    startHeight: size.value.height,
    startXOffset: position.value.x,
    startYOffset: position.value.y
  }
  document.addEventListener('pointermove', handleResize)
  document.addEventListener('pointerup', finishResize)
}

function finishMove() {
  if (!activeMove) return
  activeMove = null
  isInteracting.value = false
  document.removeEventListener('pointermove', handleMove)
  document.removeEventListener('pointerup', finishMove)
  persistPanelState()
}

function handleMove(event) {
  if (!activeMove) return
  position.value = {
    x: Math.round(activeMove.startXOffset + event.clientX - activeMove.startX),
    y: Math.round(activeMove.startYOffset + event.clientY - activeMove.startY)
  }
}

function startMove(event) {
  event.preventDefault()
  event.stopPropagation()
  focusPanel()
  isInteracting.value = true
  activeMove = {
    startX: event.clientX,
    startY: event.clientY,
    startXOffset: position.value.x,
    startYOffset: position.value.y
  }
  document.addEventListener('pointermove', handleMove)
  document.addEventListener('pointerup', finishMove)
}

function focusPanel() {
  zIndex.value = ++topPanelZIndex
}

function isInteractiveTarget(target) {
  return Boolean(target?.closest?.('button, a, input, textarea, select, [role="button"], .el-select, .el-input, .resize-handle'))
}

function getResizeCursor(axis) {
  if (axis === 'left' || axis === 'right') return 'ew-resize'
  if (axis === 'top' || axis === 'bottom') return 'ns-resize'
  if (axis === 'left-top' || axis === 'right-bottom') return 'nwse-resize'
  if (axis === 'right-top' || axis === 'left-bottom') return 'nesw-resize'
  return ''
}

function getResizeAxisFromPointer(event, rect) {
  const offsetX = event.clientX - rect.left
  const offsetY = event.clientY - rect.top
  const nearLeft = offsetX <= RESIZE_EDGE_SIZE
  const nearRight = rect.width - offsetX <= RESIZE_EDGE_SIZE
  const nearTop = offsetY <= RESIZE_EDGE_SIZE
  const nearBottom = rect.height - offsetY <= RESIZE_EDGE_SIZE
  const inLeftCorner = offsetX <= RESIZE_CORNER_SIZE
  const inRightCorner = rect.width - offsetX <= RESIZE_CORNER_SIZE
  const inTopCorner = offsetY <= RESIZE_CORNER_SIZE
  const inBottomCorner = rect.height - offsetY <= RESIZE_CORNER_SIZE

  if (inLeftCorner && inTopCorner) return 'left-top'
  if (inRightCorner && inTopCorner) return 'right-top'
  if (inLeftCorner && inBottomCorner) return 'left-bottom'
  if (inRightCorner && inBottomCorner) return 'right-bottom'
  if (nearLeft) return 'left'
  if (nearRight) return 'right'
  if (nearTop) return 'top'
  if (nearBottom) return 'bottom'
  return ''
}

function handlePanelPointerMove(event) {
  if (activeMove || activeResize) return
  const rect = event.currentTarget.getBoundingClientRect()
  hoverResizeAxis.value = getResizeAxisFromPointer(event, rect)
}

function clearHoverResizeAxis() {
  if (activeResize) return
  hoverResizeAxis.value = ''
}

function handlePanelPointerDown(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  const resizeAxis = getResizeAxisFromPointer(event, rect)
  if (resizeAxis && !isInteractiveTarget(event.target)) {
    startResize(event, resizeAxis)
    return
  }
  if (isInteractiveTarget(event.target)) return
  const isTopDragArea = event.clientY - rect.top <= 58
  if (!isTopDragArea) return
  startMove(event)
}

watch(
  () => [props.defaultWidth, props.defaultHeight, props.storageKey],
  loadSize,
  { immediate: true }
)

onBeforeUnmount(() => {
  finishResize()
  finishMove()
})
</script>

<style scoped>
.resizable-panel {
  position: relative;
  box-sizing: border-box;
  min-width: 0;
  overflow: auto;
  will-change: transform;
  transition: box-shadow 0.16s ease, transform 0.04s linear;
}

.resizable-panel.is-interacting {
  box-shadow: 0 22px 48px rgba(25, 31, 38, 0.22) !important;
  user-select: none;
}

.resize-handle {
  position: absolute;
  z-index: 30;
  border: 0;
  padding: 0;
  background: transparent;
  pointer-events: auto;
  touch-action: none;
}

.resize-handle-left {
  top: 18px;
  bottom: 18px;
  left: 0;
  width: 14px;
  cursor: ew-resize;
}

.resize-handle-right {
  top: 18px;
  right: 0;
  bottom: 18px;
  width: 14px;
  cursor: ew-resize;
}

.resize-handle-top {
  top: 0;
  right: 18px;
  left: 18px;
  height: 14px;
  cursor: ns-resize;
}

.resize-handle-bottom {
  right: 18px;
  bottom: 0;
  left: 18px;
  height: 14px;
  cursor: ns-resize;
}

.resize-handle-corner {
  right: 0;
  bottom: 0;
  width: 28px;
  height: 28px;
  cursor: nwse-resize;
}

.resize-handle-top-left {
  top: 0;
  right: auto;
  bottom: auto;
  left: 0;
  cursor: nwse-resize;
}

.resize-handle-top-right {
  top: 0;
  right: 0;
  bottom: auto;
  left: auto;
  cursor: nesw-resize;
}

.resize-handle-bottom-left {
  top: auto;
  right: auto;
  bottom: 0;
  left: 0;
  cursor: nesw-resize;
}

.resize-handle-corner::before {
  content: "";
  position: absolute;
  right: 7px;
  bottom: 7px;
  width: 13px;
  height: 13px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  color: rgba(228, 179, 93, 0.62);
}

.resize-handle-top-left::before {
  right: auto;
  bottom: auto;
  top: 7px;
  left: 7px;
  border: 0;
  border-top: 2px solid currentColor;
  border-left: 2px solid currentColor;
}

.resize-handle-top-right::before {
  bottom: auto;
  top: 7px;
  border: 0;
  border-top: 2px solid currentColor;
  border-right: 2px solid currentColor;
}

.resize-handle-bottom-left::before {
  right: auto;
  left: 7px;
  border: 0;
  border-bottom: 2px solid currentColor;
  border-left: 2px solid currentColor;
}

.resizable-panel :deep(.pool-head),
.resizable-panel :deep(.tray-head),
.resizable-panel :deep(.panel-title),
.resizable-panel :deep(.dense-side h3) {
  cursor: move;
  user-select: none;
}
</style>
