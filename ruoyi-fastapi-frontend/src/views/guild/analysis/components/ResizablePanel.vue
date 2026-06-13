<template>
  <section
    class="resizable-panel"
    :class="[panelClass, { 'is-interacting': isInteracting }]"
    :style="panelStyle"
    @pointerdown.capture="focusPanel"
    @pointerdown="handlePanelPointerDown"
  >
    <slot />
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
      @pointerdown="startResize($event, 'corner')"
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
    default: 'guild-analysis:panel-sizes:v1'
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

const size = ref({
  width: props.defaultWidth,
  height: props.defaultHeight
})
const position = ref({
  x: 0,
  y: 0
})
const isInteracting = ref(false)

let activeResize = null
let activeMove = null

const panelStyle = computed(() => ({
  width: `${size.value.width}px`,
  minWidth: `${props.minWidth}px`,
  height: `${size.value.height}px`,
  minHeight: `${props.minHeight}px`,
  transform: `translate3d(${position.value.x}px, ${position.value.y}px, 0)`,
  zIndex: zIndex.value
}))

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
  const nextWidth = activeResize.axis !== 'bottom'
    ? Math.max(props.minWidth, activeResize.startWidth + deltaX)
    : size.value.width
  const nextHeight = activeResize.axis !== 'right'
    ? Math.max(props.minHeight, activeResize.startHeight + deltaY)
    : size.value.height
  size.value = {
    width: Math.round(nextWidth),
    height: Math.round(nextHeight)
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
    startHeight: size.value.height
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

function handlePanelPointerDown(event) {
  if (isInteractiveTarget(event.target)) return
  const rect = event.currentTarget.getBoundingClientRect()
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
  min-width: 0;
  overflow: auto;
  will-change: transform;
  transition: box-shadow 0.16s ease, transform 0.04s linear;
}

.resizable-panel.is-interacting {
  box-shadow: 0 22px 48px rgba(25, 31, 38, 0.22) !important;
}

.resize-handle {
  position: absolute;
  z-index: 4;
  border: 0;
  padding: 0;
  background: transparent;
}

.resize-handle-right {
  top: 14px;
  right: 0;
  bottom: 14px;
  width: 8px;
  cursor: ew-resize;
}

.resize-handle-bottom {
  right: 14px;
  bottom: 0;
  left: 14px;
  height: 8px;
  cursor: ns-resize;
}

.resize-handle-corner {
  right: 0;
  bottom: 0;
  width: 20px;
  height: 20px;
  cursor: nwse-resize;
}

.resize-handle-corner::before {
  content: "";
  position: absolute;
  right: 5px;
  bottom: 5px;
  width: 10px;
  height: 10px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  color: rgba(23, 33, 43, 0.42);
}

.resizable-panel :deep(.pool-head),
.resizable-panel :deep(.tray-head),
.resizable-panel :deep(.panel-title),
.resizable-panel :deep(.dense-side h3) {
  cursor: move;
  user-select: none;
}
</style>
