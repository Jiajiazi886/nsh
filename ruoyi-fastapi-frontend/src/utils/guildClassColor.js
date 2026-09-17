import { computed, ref } from 'vue'
import '@/utils/professionStylesCore.js'
import { activityApi } from '@/api/activities'
import { getToken } from '@/utils/auth'
import defaultGuildClassColorConfig from '@/assets/data/guild-class-colors-default.json'

export const DEFAULT_GUILD_CLASS_COLORS = defaultGuildClassColorConfig.colors || []

const defaultClassColorMap = buildClassColorMap(DEFAULT_GUILD_CLASS_COLORS, false)
const classColorMap = ref({ ...defaultClassColorMap })
let loaded = false
let loadingPromise = null
let actorToken = null
let epoch = 0
export function clearGuildClassColors() { actorToken = null; epoch++; loaded = false; loadingPromise = null; classColorMap.value = { ...defaultClassColorMap } }
function ensureActor() { const token = getToken() || ''; if (token !== actorToken) { clearGuildClassColors(); actorToken = token } return token }

function buildClassColorMap(list = [], includeDefaults = true) {
  const map = includeDefaults ? { ...defaultClassColorMap } : {}
  list.forEach(item => {
    if (!item?.class_name) return
    map[item.class_name] = item
  })
  return map
}

function normalizeColorItem(item = {}) {
  const className = item.profession || item.class_name || item.className
  if (!className) return null
  const fallback = defaultClassColorMap[className] || { bg_color:'#e5e7eb', text_color:'#374151' }
  const normalized = globalThis.NshProfessionStyles.normalize([item])[className] || {}
  const bg = normalized.backgroundColor
  const fg = normalized.color
  return {class_name:className, bg_color:/^#[0-9a-f]{6}$/i.test(bg||'')?bg:fallback.bg_color,
    text_color:/^#[0-9a-f]{6}$/i.test(fg||'')?fg:fallback.text_color}
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
  ensureActor()
  epoch++
  classColorMap.value = buildClassColorMap(normalizeClassColorList(list))
  loaded = true
  return classColorMap.value
}

export async function loadGuildClassColors(force = false) {
  const token = ensureActor()
  if (!token || loaded && !force) return classColorMap.value
  if (!loadingPromise || force) {
    const version = ++epoch
    const task = activityApi.professionStyles().then(rows => {
      if (ensureActor() === token && epoch === version) {
        classColorMap.value = buildClassColorMap(normalizeClassColorList(rows))
        loaded = true
      }
      return classColorMap.value
    }).catch(() => classColorMap.value).finally(() => { if (loadingPromise === task) loadingPromise = null })
    loadingPromise = task
  }
  return loadingPromise
}
export function getGuildClassStyle(className) {
  ensureActor()
  const item = classColorMap.value[className] || {bg_color:'#e5e7eb',text_color:'#374151'}
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
