import { computed, ref } from 'vue'
import { getClassColors } from '@/api/guild/classColor'

export const DEFAULT_GUILD_CLASS_COLORS = [
  { class_name: '九灵', bg_color: '#e100ff', text_color: '#000000' },
  { class_name: '沧澜', bg_color: '#009dff', text_color: '#000000' },
  { class_name: '潮光', bg_color: '#0073ff', text_color: '#000000' },
  { class_name: '玄机', bg_color: '#ddff00', text_color: '#000000' },
  { class_name: '碎梦', bg_color: '#00ffe5', text_color: '#000000' },
  { class_name: '神相', bg_color: '#002fff', text_color: '#000000' },
  { class_name: '素问', bg_color: '#ea00ff', text_color: '#000000' },
  { class_name: '血河', bg_color: '#ff0000', text_color: '#000000' },
  { class_name: '铁衣', bg_color: '#ff8c00', text_color: '#000000' },
  { class_name: '鸿音', bg_color: '#ff7b00', text_color: '#000000' },
  { class_name: '龙吟', bg_color: '#00f846', text_color: '#000000' },
  { class_name: '刺客', bg_color: '#FFFFFF', text_color: '#000000' }
]

const defaultClassColorMap = buildClassColorMap(DEFAULT_GUILD_CLASS_COLORS, false)
const classColorMap = ref({ ...defaultClassColorMap })
let loaded = false
let loadingPromise = null

function buildClassColorMap(list = [], includeDefaults = true) {
  const map = includeDefaults ? { ...defaultClassColorMap } : {}
  list.forEach(item => {
    if (!item?.class_name) return
    map[item.class_name] = item
  })
  return map
}

function normalizeColorItem(item = {}) {
  const className = item.class_name || item.className
  if (!className) return null
  const defaultItem = defaultClassColorMap[className] || {}
  const bgColor = item.bg_color || item.bgColor
  const textColor = item.text_color || item.textColor
  const isLegacyEmptyColor =
    bgColor?.toUpperCase?.() === '#FFFFFF' &&
    textColor?.toUpperCase?.() === '#000000' &&
    defaultItem.bg_color?.toUpperCase?.() !== '#FFFFFF'
  return {
    class_name: className,
    bg_color: isLegacyEmptyColor ? defaultItem.bg_color : bgColor || defaultItem.bg_color || '#FFFFFF',
    text_color: isLegacyEmptyColor ? defaultItem.text_color : textColor || defaultItem.text_color || '#000000'
  }
}

function hexToRgb(color) {
  if (!color || typeof color !== 'string') return null
  const normalized = color.trim().replace('#', '')
  if (!/^[0-9a-fA-F]{3}$|^[0-9a-fA-F]{6}$/.test(normalized)) return null
  const full = normalized.length === 3
    ? normalized.split('').map(char => `${char}${char}`).join('')
    : normalized
  return {
    r: parseInt(full.slice(0, 2), 16),
    g: parseInt(full.slice(2, 4), 16),
    b: parseInt(full.slice(4, 6), 16)
  }
}

function rgba(color, alpha) {
  const rgb = hexToRgb(color)
  if (!rgb) return `rgba(47, 111, 99, ${alpha})`
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`
}

export function normalizeClassColorList(list = []) {
  return list
    .map(normalizeColorItem)
    .filter(Boolean)
}

export function setGuildClassColors(list = []) {
  classColorMap.value = buildClassColorMap(normalizeClassColorList(list))
  loaded = true
  return classColorMap.value
}

export async function loadGuildClassColors(force = false) {
  if (loaded && !force) return classColorMap.value
  if (!loadingPromise || force) {
    loadingPromise = getClassColors()
      .then(res => setGuildClassColors(res.data || res || []))
      .catch(error => {
        loaded = true
        throw error
      })
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

export function getGuildClassTokenStyle(className) {
  if (!className) return {}
  const item = classColorMap.value[className]
  if (!item) return {}
  return {
    '--guild-class-accent': item.bg_color,
    '--guild-class-accent-soft': rgba(item.bg_color, 0.14),
    '--guild-class-accent-ring': rgba(item.bg_color, 0.24),
    '--guild-class-accent-bar': `linear-gradient(90deg, ${rgba(item.bg_color, 0.36)}, ${item.bg_color})`
  }
}

export function getGuildClassBarStyle(className) {
  const item = classColorMap.value[className]
  if (!item) return {}
  return {
    background: `linear-gradient(90deg, ${rgba(item.bg_color, 0.36)}, ${item.bg_color})`
  }
}

export function useGuildClassColors() {
  const classOptions = computed(() => Object.keys(classColorMap.value).sort())
  return {
    classColorMap,
    classOptions,
    getGuildClassBarStyle,
    getGuildClassStyle,
    getGuildClassTokenStyle,
    loadGuildClassColors,
    setGuildClassColors
  }
}
