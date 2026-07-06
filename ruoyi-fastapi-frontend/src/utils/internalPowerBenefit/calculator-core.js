import { WORKBOOK_DATA, FORMULAS } from './workbook-data.js';
import { WorkbookEngine, asNumber } from './formula-engine.js';

const SHEET = '属性输入';
export const FORMULA_SCOPE_INTERNAL_POWER_PVP = 'internal_power_pvp_damage';

export const DEFAULT_TARGET = {
  defense: 2550,
  resist: 400,
  critResist: 0,
  resistPct: 0,
  hp: 100000,
  critDefense: 0,
  skillResist: 0,
  skillReductionPct: 0,
  techniqueResist: 0,
  damageReductionPct: 0,
};

export const DEFAULT_ATTACK = {
  attack: 1750,
  breakDefense: 1100,
  restraintValue: 285,
  crit: 1100,
  critDmg: 0.575,
  extraCritRate: 0,
  restraintPct: 0,
  skillBonusPct: 0,
  skillBonus: 0,
  gearBonus: 0.25,
  internalBonus: 0.15,
  elementBonus: 0,
  techniqueRestraint: 0,
};

export const EMPTY_DELTA = {
  attack: 0,
  breakDefense: 0,
  restraintValue: 0,
  crit: 0,
  critDmg: 0,
  extraCritRate: 0,
  restraintPct: 0,
  skillBonusPct: 0,
  skillBonus: 0,
  gearBonus: 0,
  internalBonus: 0,
  elementBonus: 0,
  techniqueRestraint: 0,
  finalBonus: 0,
};

export const FIXED_CELLS = [
  { sheet: SHEET, cell: 'C13', value: 0, label: '气盾' },
  { sheet: SHEET, cell: 'D13', value: 0, label: '元素抗性' },
  { sheet: SHEET, cell: 'F13', value: 0, label: '格挡' },
  { sheet: SHEET, cell: 'D27', value: 0, label: '破盾' },
  { sheet: SHEET, cell: 'E27', value: 0, label: '元素攻击' },
  { sheet: SHEET, cell: 'G27', value: 18200, label: '命中' },
  { sheet: SHEET, cell: 'A27', value: 0, label: '忽视元抗' },
];

export const OUTPUTS = {
  sheet: SHEET,
  damage: 'D29',
  noCritDamage: 'B29',
  critRate: 'P29',
  hitRate: 'O29',
  penetrateRateSource: 'P27',
  remainingDefense: 'O27',
};

export const TARGET_FIELDS = [
  { key: 'defense', label: '防御', type: 'number', cell: 'B13' },
  { key: 'resist', label: '抵御', type: 'number', cell: 'E13' },
  { key: 'critResist', label: '会心抵抗', type: 'number', cell: 'G13' },
  { key: 'resistPct', label: '抵御百分比', type: 'percent', cell: 'H13' },
  { key: 'hp', label: '血量', type: 'number', cell: 'I13' },
  { key: 'critDefense', label: '会心防御', type: 'percent', cell: 'J13' },
  { key: 'skillResist', label: '技能抵御', type: 'number', cell: 'K13' },
  { key: 'skillReductionPct', label: '技能减免百分比', type: 'percent', cell: 'L13' },
  { key: 'techniqueResist', label: '受击方技巧克制', type: 'number', cell: 'M13' },
  { key: 'damageReductionPct', label: '减伤百分比（日月区）', type: 'percent', cell: 'O13' },
];

export const ATTACK_FIELDS = [
  { key: 'attack', label: '攻击', type: 'number', cell: 'B27' },
  { key: 'breakDefense', label: '破防', type: 'number', cell: 'C27' },
  { key: 'restraintValue', label: '克制数值', type: 'number', cell: 'F27' },
  { key: 'crit', label: '会心', type: 'number', cell: 'H27' },
  { key: 'critDmg', label: '会伤-100%', type: 'percent', cell: 'I27' },
  { key: 'extraCritRate', label: '额外会心率', type: 'percent', cell: 'J27' },
  { key: 'restraintPct', label: '克制百分比', type: 'percent', cell: 'K27' },
  { key: 'skillBonusPct', label: '技能增强百分比', type: 'percent', cell: 'L27' },
  { key: 'skillBonus', label: '技能增强', type: 'number', cell: 'N27' },
  { key: 'gearBonus', label: '装备增伤比', type: 'percent', cell: 'K29' },
  { key: 'internalBonus', label: '内功增伤比', type: 'percent', cell: 'L29' },
  { key: 'elementBonus', label: '元素增伤百分比', type: 'percent', cell: 'M29' },
  { key: 'techniqueRestraint', label: '攻击方技巧克制', type: 'number', cell: 'N29' },
];

export const MANUAL_FIELDS = [
  { key: 'attack', label: '攻击变化', type: 'number' },
  { key: 'breakDefense', label: '破防变化', type: 'number' },
  { key: 'crit', label: '会心变化', type: 'number' },
  { key: 'critDmg', label: '会伤变化', type: 'percent' },
  { key: 'restraintValue', label: '克制数值变化', type: 'number' },
  { key: 'restraintPct', label: '克制百分比变化', type: 'percent' },
  { key: 'extraCritRate', label: '额外会心率变化', type: 'percent' },
  { key: 'skillBonus', label: '技能增强变化', type: 'number' },
  { key: 'skillBonusPct', label: '技能增强百分比变化', type: 'percent' },
  { key: 'internalBonus', label: '内功增伤比变化', type: 'percent' },
  { key: 'finalBonus', label: '最终增伤变化', type: 'percent' },
];

export const ENTRY_DEFS = [
  { name: '攻击', max: '33', type: 'number', role: 'offense' },
  { name: '力量/气海', max: '10', type: 'number', role: 'offense' },
  { name: '赛年伤害/治疗提高', max: '1.7%', type: 'percent', role: 'offense' },
  { name: '最小攻击', max: '36', type: 'number', role: 'offense' },
  { name: '最大攻击', max: '36', type: 'number', role: 'offense' },
  { name: '流派克制', max: '1.2%', type: 'percent', role: 'offense' },
  { name: '破防', max: '33', type: 'number', role: 'offense' },
  { name: '会心', max: '66', type: 'number', role: 'offense' },
  { name: '耐力', max: '10', type: 'number', role: 'mixed' },
  { name: '根骨', max: '10', type: 'number', role: 'mixed' },
  { name: '身法', max: '10', type: 'number', role: 'mixed' },
  { name: '内功防御', max: '36', type: 'number', role: 'defense' },
  { name: '首领抵御', max: '1.2%', type: 'percent', role: 'defense' },
  { name: '流派抵御', max: '1.2%', type: 'percent', role: 'defense' },
  { name: '抗会心', max: '66', type: 'number', role: 'defense' },
  { name: '防御', max: '33', type: 'number', role: 'defense' },
  { name: '气血上限', max: '991', type: 'number', role: 'defense' },
  { name: '首领克制', max: '1.2%', type: 'percent', role: 'pve' },
  { name: '抗内功会心', max: '72', type: 'number', role: 'defense' },
  { name: '抗外功会心', max: '72', type: 'number', role: 'defense' },
  { name: '外功防御', max: '36', type: 'number', role: 'defense' },
];

export const BENEFIT_PRESETS = [
  { label: '攻击 +33', delta: { attack: 33 }, explain: '内功词条上限：+33 攻击' },
  { label: '力量/气海 +10', delta: { attack: 25, breakDefense: 10 }, explain: '上限换算：+25 攻击，+10 破防' },
  { label: '赛年伤害/治疗提高 +1.7%', delta: { finalBonus: 0.017 }, explain: '上限换算：最终伤害期望 ×1.017' },
  { label: '最小攻击 +36', delta: { attack: 18 }, explain: '上限换算：折算 +18 攻击' },
  { label: '最大攻击 +36', delta: { attack: 18 }, explain: '上限换算：折算 +18 攻击' },
  { label: '流派克制 +1.2%', delta: { restraintPct: 0.012 }, explain: '上限换算：+1.2% 克制百分比' },
  { label: '破防 +33', delta: { breakDefense: 33 }, explain: '内功词条上限：+33 破防' },
  { label: '会心 +66', delta: { crit: 66 }, explain: '内功词条上限：+66 会心' },
  { label: '耐力 +10', delta: { attack: 10 }, explain: '上限换算：+10 攻击；防御收益不计入攻击收益' },
  { label: '根骨 +10', delta: { attack: 10 }, explain: '上限换算：+10 攻击；气血收益不计入攻击收益' },
  { label: '身法 +10', delta: { crit: 60 }, explain: '上限换算：+60 会心；会心抗性不计入攻击收益' },
];

export const ENTRY_RULES = [
  { name: '攻击', max: '33', type: 'number', role: 'offense', effects: [{ key: 'attack', factor: 1 }] },
  {
    name: '力量/气海',
    max: '10',
    type: 'number',
    role: 'offense',
    effects: [{ key: 'attack', factor: 2.5 }, { key: 'breakDefense', factor: 1 }],
  },
  { name: '赛年伤害/治疗提高', max: '1.7%', type: 'percent', role: 'offense', effects: [{ key: 'finalBonus', factor: 1 }] },
  { name: '最小攻击', max: '36', type: 'number', role: 'offense', effects: [{ key: 'attack', factor: 0.5 }] },
  { name: '最大攻击', max: '36', type: 'number', role: 'offense', effects: [{ key: 'attack', factor: 0.5 }] },
  { name: '流派克制', max: '1.2%', type: 'percent', role: 'offense', effects: [{ key: 'restraintPct', factor: 1 }] },
  { name: '破防', max: '33', type: 'number', role: 'offense', effects: [{ key: 'breakDefense', factor: 1 }] },
  { name: '会心', max: '66', type: 'number', role: 'offense', effects: [{ key: 'crit', factor: 1 }] },
  { name: '耐力', max: '10', type: 'number', role: 'mixed', effects: [{ key: 'attack', factor: 1 }] },
  { name: '根骨', max: '10', type: 'number', role: 'mixed', effects: [{ key: 'attack', factor: 1 }] },
  { name: '身法', max: '10', type: 'number', role: 'mixed', effects: [{ key: 'crit', factor: 6 }] },
  { name: '内功防御', max: '36', type: 'number', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
  { name: '首领抵御', max: '1.2%', type: 'percent', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
  { name: '流派抵御', max: '1.2%', type: 'percent', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
  { name: '抗会心', max: '66', type: 'number', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
  { name: '防御', max: '33', type: 'number', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
  { name: '气血上限', max: '991', type: 'number', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
  { name: '首领克制', max: '1.2%', type: 'percent', role: 'pve', effects: [], ignoredNote: '首领克制属于 PVE 词条，当前 PVP 计算不计入伤害收益' },
  { name: '抗内功会心', max: '72', type: 'number', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
  { name: '抗外功会心', max: '72', type: 'number', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
  { name: '外功防御', max: '36', type: 'number', role: 'defense', effects: [], ignoredNote: '防守/抗性类词条，当前攻击收益计算不计入' },
];

let activeFormulaPackage = null;
let defaultFormulaPackageCache = null;

export function createDefaultFormulaPackage() {
  return {
    scope: FORMULA_SCOPE_INTERNAL_POWER_PVP,
    version: 1,
    defaults: {
      targetPanel: cloneJson(DEFAULT_TARGET),
      attackPanel: cloneJson(DEFAULT_ATTACK),
      emptyDelta: cloneJson(EMPTY_DELTA),
    },
    fields: {
      target: cloneJson(TARGET_FIELDS),
      attack: cloneJson(ATTACK_FIELDS),
      manual: cloneJson(MANUAL_FIELDS),
    },
    fixedCells: cloneJson(FIXED_CELLS),
    entryRules: cloneJson(ENTRY_RULES),
    benefitPresets: cloneJson(BENEFIT_PRESETS),
    workbookData: cloneJson(WORKBOOK_DATA),
    formulas: cloneJson(FORMULAS),
    outputs: cloneJson(OUTPUTS),
  };
}

export function normalizeFormulaPackage(value = {}) {
  const defaults = createDefaultFormulaPackage();
  if (!value || value.builtin === true) return defaults;
  return {
    ...defaults,
    ...value,
    scope: FORMULA_SCOPE_INTERNAL_POWER_PVP,
    defaults: {
      ...defaults.defaults,
      ...(value.defaults || {}),
      targetPanel: { ...defaults.defaults.targetPanel, ...(value.defaults?.targetPanel || {}) },
      attackPanel: { ...defaults.defaults.attackPanel, ...(value.defaults?.attackPanel || {}) },
      emptyDelta: { ...defaults.defaults.emptyDelta, ...(value.defaults?.emptyDelta || {}) },
    },
    fields: {
      ...defaults.fields,
      ...(value.fields || {}),
      target: Array.isArray(value.fields?.target) ? value.fields.target : defaults.fields.target,
      attack: Array.isArray(value.fields?.attack) ? value.fields.attack : defaults.fields.attack,
      manual: Array.isArray(value.fields?.manual) ? value.fields.manual : defaults.fields.manual,
    },
    fixedCells: Array.isArray(value.fixedCells) ? value.fixedCells : defaults.fixedCells,
    entryRules: Array.isArray(value.entryRules) ? value.entryRules : defaults.entryRules,
    benefitPresets: Array.isArray(value.benefitPresets) ? value.benefitPresets : defaults.benefitPresets,
    workbookData: value.workbookData || defaults.workbookData,
    formulas: value.formulas || defaults.formulas,
    outputs: { ...defaults.outputs, ...(value.outputs || {}) },
  };
}

export function setActiveFormulaPackage(value = null) {
  activeFormulaPackage = value ? normalizeFormulaPackage(value) : null;
  return getActiveFormulaPackage();
}

export function getActiveFormulaPackage() {
  return activeFormulaPackage || getDefaultFormulaPackage();
}

export function getEntryDefinitions() {
  return getActiveFormulaPackage().entryRules.map(rule => ({
    name: rule.name,
    max: rule.max,
    type: rule.type || 'number',
    role: rule.role || 'offense',
  }));
}

export function getBenefitPresets() {
  return getActiveFormulaPackage().benefitPresets || BENEFIT_PRESETS;
}

export function parseInputNumber(value, type = 'number') {
  if (value === null || value === undefined) return 0;
  const raw = String(value).replace(/,/g, '').trim();
  if (!raw) return 0;
  if (raw.endsWith('%')) {
    const n = Number(raw.slice(0, -1));
    return Number.isFinite(n) ? n / 100 : 0;
  }
  const n = Number(raw);
  if (!Number.isFinite(n)) return 0;
  if (type === 'percent') return Math.abs(n) > 0.5 ? n / 100 : n;
  return n;
}


export function maxValueForEntry(def) {
  if (!def || !def.max || def.max === '未配置') return Infinity;
  return parseInputNumber(def.max, def.type);
}

export function isEntryOverLimit(name, value) {
  const def = getEntryDefinitions().find(item => item.name === name);
  if (!def) return false;
  const n = parseInputNumber(value, def.type);
  const max = maxValueForEntry(def);
  return Number.isFinite(max) && Math.abs(n) > max + 1e-12;
}

export function fmtNumber(value, digits = 0) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '0';
  return n.toLocaleString('zh-CN', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

export function fmtPercent(value, digits = 3) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '0.000%';
  return `${(n * 100).toFixed(digits)}%`;
}

export function createEmptyDelta() {
  return { ...getActiveFormulaPackage().defaults.emptyDelta };
}

export function addDelta(base, extra = {}) {
  const out = { ...getActiveFormulaPackage().defaults.emptyDelta, ...base };
  for (const [key, value] of Object.entries(extra || {})) {
    out[key] = (out[key] || 0) + Number(value || 0);
  }
  return out;
}

export function mergeDeltas(...deltas) {
  let out = createEmptyDelta();
  for (const delta of deltas) out = addDelta(out, delta);
  return out;
}

export function convertEntries(entries) {
  const delta = createEmptyDelta();
  const details = [];
  const defs = new Map(getActiveFormulaPackage().entryRules.map(d => [d.name, d]));

  for (const entry of entries || []) {
    const name = entry?.name;
    const def = defs.get(name);
    if (!def) continue;
    const value = parseInputNumber(entry.value, def.type);
    if (!value) continue;
    const before = { ...delta };

    for (const effect of def.effects || []) {
      if (!effect?.key) continue;
      delta[effect.key] = (delta[effect.key] || 0) + value * safeNumber(effect.factor, 1);
    }

    details.push({
      name,
      value: def.type === 'percent' ? fmtPercent(value, 2) : fmtNumber(value, 2).replace(/\.00$/, ''),
      note: describeContribution(name, value, before, delta, def),
    });
  }
  return { delta, details };
}

function describeContribution(name, value, before, after, rule = {}) {
  const changed = [];
  const labels = {
    attack: '攻击', breakDefense: '破防', crit: '会心', critDmg: '会伤', extraCritRate: '额外会心率',
    restraintPct: '克制百分比', restraintValue: '克制数值', skillBonus: '技能增强', skillBonusPct: '技能增强百分比',
    internalBonus: '内功增伤比', finalBonus: '最终增伤',
  };
  for (const [key, label] of Object.entries(labels)) {
    const diff = (after[key] || 0) - (before[key] || 0);
    if (Math.abs(diff) > 1e-12) {
      const percentKey = ['critDmg', 'extraCritRate', 'restraintPct', 'skillBonusPct', 'internalBonus', 'finalBonus'].includes(key);
      changed.push(`${label} ${diff >= 0 ? '+' : ''}${percentKey ? fmtPercent(diff, 2) : fmtNumber(diff, 2).replace(/\.00$/, '')}`);
    }
  }
  if (changed.length) {
    const main = changed.join('，');
    if (name === '根骨') return `${main}；同时理论增加气血上限 ${fmtNumber(value * 84, 2).replace(/\.00$/, '')}，当前攻击收益不计入气血`;
    if (name === '耐力') return `${main}；同时理论增加防御 ${fmtNumber(value * 2.75, 2).replace(/\.00$/, '')}，当前攻击收益不计入防御`;
    if (name === '身法') return `${main}；同时理论增加会心抗性 ${fmtNumber(value * 2, 2).replace(/\.00$/, '')}，当前攻击收益不计入会心抗性`;
    return main;
  }
  return rule.ignoredNote || '防守/抗性类词条，当前攻击收益计算不计入';
}

export function buildEngine(target = DEFAULT_TARGET, attack = DEFAULT_ATTACK, delta = EMPTY_DELTA) {
  const pkg = getActiveFormulaPackage();
  const sheet = pkg.outputs?.sheet || SHEET;
  const e = new WorkbookEngine(pkg.workbookData || WORKBOOK_DATA, pkg.formulas || FORMULAS);
  for (const item of pkg.fixedCells || FIXED_CELLS) {
    e.set(item.sheet || sheet, item.cell, safeNumber(item.value));
  }

  for (const f of pkg.fields.target || TARGET_FIELDS) e.set(sheet, f.cell, safeNumber(target[f.key]));

  const atk = { ...pkg.defaults.attackPanel, ...attack };
  const d = { ...pkg.defaults.emptyDelta, ...delta };
  for (const f of pkg.fields.attack || ATTACK_FIELDS) {
    e.set(sheet, f.cell, safeNumber(atk[f.key]) + safeNumber(d[f.key]));
  }
  return e;
}

export function computeDamage(target, attack, delta = EMPTY_DELTA) {
  const pkg = getActiveFormulaPackage();
  const outputs = pkg.outputs || OUTPUTS;
  const sheet = outputs.sheet || SHEET;
  const e = buildEngine(target, attack, delta);
  const base = asNumber(e.get(sheet, outputs.damage || OUTPUTS.damage));
  return {
    damage: base * (1 + safeNumber(delta.finalBonus)),
    rawDamage: base,
    noCritDamage: asNumber(e.get(sheet, outputs.noCritDamage || OUTPUTS.noCritDamage)),
    critRate: asNumber(e.get(sheet, outputs.critRate || OUTPUTS.critRate)),
    hitRate: asNumber(e.get(sheet, outputs.hitRate || OUTPUTS.hitRate)),
    penetrateRate: 1 - asNumber(e.get(sheet, outputs.penetrateRateSource || OUTPUTS.penetrateRateSource)),
    remainingDefense: asNumber(e.get(sheet, outputs.remainingDefense || OUTPUTS.remainingDefense)),
  };
}

export function computeAll(target, attack, entries, manualDelta) {
  const converted = convertEntries(entries);
  const totalDelta = mergeDeltas(converted.delta, manualDelta);
  const base = computeDamage(target, attack, createEmptyDelta());
  const changed = computeDamage(target, attack, totalDelta);
  const gain = base.damage ? changed.damage / base.damage - 1 : 0;
  const benefits = getBenefitPresets().map(item => {
    const result = computeDamage(target, attack, { ...getActiveFormulaPackage().defaults.emptyDelta, ...item.delta });
    return {
      ...item,
      gain: base.damage ? result.damage / base.damage - 1 : 0,
    };
  }).sort((a, b) => b.gain - a.gain);
  return { base, changed, gain, converted, totalDelta, benefits };
}

function safeNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function getDefaultFormulaPackage() {
  if (!defaultFormulaPackageCache) {
    defaultFormulaPackageCache = createDefaultFormulaPackage();
  }
  return defaultFormulaPackageCache;
}
