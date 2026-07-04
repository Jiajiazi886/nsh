export class WorkbookEngine {
  constructor(workbookData, formulas) {
    this.initial = structuredClone(workbookData.sheets);
    this.sheets = structuredClone(workbookData.sheets);
    this.formulas = formulas;
    this.cache = new Map();
    this.compiled = new Map();
    this.visiting = new Set();
  }

  reset() {
    this.sheets = structuredClone(this.initial);
    this.cache.clear();
  }

  clearCache() {
    this.cache.clear();
  }

  set(sheet, addr, value) {
    if (!this.sheets[sheet]) this.sheets[sheet] = {};
    if (!this.sheets[sheet][addr]) this.sheets[sheet][addr] = { value: null };
    this.sheets[sheet][addr].value = value;
    this.clearCache();
  }

  raw(sheet, addr) {
    const cell = this.sheets?.[sheet]?.[addr];
    if (!cell || cell.value === undefined || cell.value === null || cell.value === '') return 0;
    return cell.value;
  }

  get(sheet, addr) {
    const key = `${sheet}!${addr}`;
    if (this.cache.has(key)) return this.cache.get(key);
    if (this.formulas[key]) {
      if (this.visiting.has(key)) return 0;
      this.visiting.add(key);
      let result;
      try {
        result = this.evaluate(key, this.formulas[key]);
        if (typeof result === 'number' && !Number.isFinite(result)) result = result > 0 ? '#DIV/0!' : '#NUM!';
      } catch (err) {
        console.warn('Formula error', key, this.formulas[key], err);
        result = '#ERR';
      }
      this.visiting.delete(key);
      this.cache.set(key, result);
      return result;
    }
    return this.raw(sheet, addr);
  }

  range(sheet, start, end) {
    const [r1, c1] = splitAddress(start);
    const [r2, c2] = splitAddress(end);
    const out = [];
    for (let r = Math.min(r1, r2); r <= Math.max(r1, r2); r += 1) {
      const row = [];
      for (let c = Math.min(c1, c2); c <= Math.max(c1, c2); c += 1) {
        row.push(this.get(sheet, `${columnLetter(c)}${r}`));
      }
      out.push(row);
    }
    return out;
  }

  evaluate(key, expr) {
    if (!isSafeFormulaExpression(expr)) {
      throw new Error(`Unsafe formula expression: ${key}`);
    }
    let fn = this.compiled.get(key);
    if (!fn) {
      fn = new Function('G', 'R', 'MAX', 'MIN', 'IF', 'EXP', 'ROUNDDOWN', 'VLOOKUP', `return (${expr});`);
      this.compiled.set(key, fn);
    }
    const G = (sheet, addr) => this.get(sheet, addr);
    const R = (sheet, start, end) => this.range(sheet, start, end);
    return fn(G, R, MAX, MIN, IF, Math.exp, ROUNDDOWN, VLOOKUP);
  }
}

export function isSafeFormulaExpression(expr) {
  if (typeof expr !== 'string') return false;
  const forbidden = /(;|=>|\{|\}|\[|\]|`|\bfunction\b|\bnew\b|\bthis\b|\bwindow\b|\bdocument\b|\bglobalThis\b|\bconstructor\b|\b__proto__\b|\bprototype\b|\beval\b|\bimport\b|\brequire\b|\bprocess\b)/i;
  const allowedChars = /^[\s\w\u4e00-\u9fff+\-*/%().,!<>=&|?:,"'\\]+$/;
  return !forbidden.test(expr) && allowedChars.test(expr);
}

export function asNumber(value) {
  if (typeof value === 'number') return Number.isFinite(value) ? value : 0;
  if (value === null || value === undefined || value === '') return 0;
  if (typeof value === 'boolean') return value ? 1 : 0;
  const n = Number(String(value).replace('%', '').trim());
  return Number.isFinite(n) ? n : 0;
}

function flatten(values) {
  const out = [];
  for (const v of values) {
    if (Array.isArray(v)) out.push(...flatten(v));
    else out.push(v);
  }
  return out;
}

export function MAX(...args) {
  const nums = flatten(args).map(asNumber);
  return nums.length ? Math.max(...nums) : 0;
}

export function MIN(...args) {
  const nums = flatten(args).map(asNumber);
  return nums.length ? Math.min(...nums) : 0;
}

export function IF(condition, whenTrue, whenFalse) {
  return condition ? whenTrue : whenFalse;
}

export function ROUNDDOWN(value, digits = 0) {
  const n = asNumber(value);
  const factor = Math.pow(10, asNumber(digits));
  return n >= 0 ? Math.floor(n * factor) / factor : Math.ceil(n * factor) / factor;
}

export function VLOOKUP(lookup, range, colIndex, exact = 0) {
  const col = Math.max(1, Math.trunc(asNumber(colIndex))) - 1;
  const rows = Array.isArray(range) ? range : [];
  const lookupText = String(lookup);
  for (const row of rows) {
    if (!row || row.length === 0) continue;
    const first = row[0];
    const matched = exact === 0 || exact === false
      ? String(first) === lookupText
      : asNumber(first) <= asNumber(lookup);
    if (matched) return row[col] === undefined || row[col] === null || row[col] === '' ? 0 : row[col];
  }
  return '#N/A';
}

export function splitAddress(addr) {
  const m = /^([A-Z]+)(\d+)$/.exec(addr);
  if (!m) throw new Error(`Bad address: ${addr}`);
  return [Number(m[2]), columnIndex(m[1])];
}

export function columnIndex(letters) {
  let n = 0;
  for (const ch of letters) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n;
}

export function columnLetter(index) {
  let n = index;
  let s = '';
  while (n > 0) {
    const rem = (n - 1) % 26;
    s = String.fromCharCode(65 + rem) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}
