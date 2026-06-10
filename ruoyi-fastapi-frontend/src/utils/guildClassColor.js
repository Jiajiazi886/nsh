import { computed, ref } from 'vue'
import { getClassColors } from '@/api/guild/classColor'

const classColorMap = ref({})
let loaded = false
let loadingPromise = null

function normalizeColorItem(item = {}) {
  const className = item.class_name || item.className
  if (!className) return null
  return {
    class_name: className,
    bg_color: item.bg_color || item.bgColor || '#FFFFFF',
    text_color: item.text_color || item.textColor || '#263245'
  }
}

export function normalizeClassColorList(list = []) {
  return list
    .map(normalizeColorItem)
    .filter(Boolean)
}

export function setGuildClassColors(list = []) {
  const map = {}
  normalizeClassColorList(list).forEach(item => {
    map[item.class_name] = item
  })
  classColorMap.value = map
  loaded = true
  return map
}

export async function loadGuildClassColors(force = false) {
  if (loaded && !force) return classColorMap.value
  if (!loadingPromise || force) {
    loadingPromise = getClassColors()
      .then(res => setGuildClassColors(res.data || res || []))
      .finally(() => {
        loadingPromise = null
      })
  }
  return loadingPromise
}

export function getGuildClassStyle(className) {
  if (!className) return {}
  const item = classColorMap.value[className]
  if (!item) return {}
  return {
    backgroundColor: item.bg_color,
    borderColor: item.text_color,
    color: item.text_color
  }
}

export function getGuildClassBarStyle(className) {
  const item = classColorMap.value[className]
  if (!item) return {}
  return {
    background: `linear-gradient(90deg, ${item.text_color}, ${item.bg_color})`
  }
}

export function useGuildClassColors() {
  const classOptions = computed(() => Object.keys(classColorMap.value).sort())
  return {
    classColorMap,
    classOptions,
    getGuildClassBarStyle,
    getGuildClassStyle,
    loadGuildClassColors,
    setGuildClassColors
  }
}
