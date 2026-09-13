export const DRAFT_DATABASE = 'guild-schedule-drafts'
export const DRAFT_STORE = 'drafts'
let opening
function openDatabase() {
  if (!globalThis.indexedDB) return Promise.reject(Error('浏览器不支持 IndexedDB，草稿不能持久保存'))
  if (!opening) opening = new Promise((resolve, reject) => {
    const request = indexedDB.open(DRAFT_DATABASE, 1)
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(DRAFT_STORE)) request.result.createObjectStore(DRAFT_STORE, { keyPath: 'key' })
    }
    request.onsuccess = () => {
      const db = request.result
      db.onversionchange = () => { db.close(); opening = undefined }
      resolve(db)
    }
    request.onerror = () => { opening = undefined; reject(request.error || Error('无法打开本地草稿数据库')) }
    request.onblocked = () => { opening = undefined; reject(Error('本地数据库升级被其他窗口阻挡，请关闭旧页面后重试')) }
  })
  return opening
}
export function draftStorageKey(userId, scheduleId, apiEnvironment) {
  if (!userId || !scheduleId) throw Error('缺少账号或排表标识，不能写入共用草稿')
  return JSON.stringify([1, String(userId), String(scheduleId), String(apiEnvironment)])
}
export async function readScheduleDraft(key) {
  const db = await openDatabase()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(DRAFT_STORE, 'readonly'), request = tx.objectStore(DRAFT_STORE).get(key)
    tx.oncomplete = () => resolve(request.result?.draft || null)
    tx.onerror = tx.onabort = () => reject(tx.error || Error('本地草稿读取失败'))
  })
}
let writeQueue = Promise.resolve()
export function writeScheduleDraft(key, draft) {
  const snapshot = JSON.parse(JSON.stringify(draft))
  const operation = writeQueue.catch(() => {}).then(() => performWrite(key, snapshot))
  writeQueue = operation
  return operation
}
async function performWrite(key, draft) {
  const db = await openDatabase()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(DRAFT_STORE, 'readwrite')
    tx.oncomplete = () => resolve()
    tx.onerror = tx.onabort = () => reject(tx.error || Error('本地草稿保存失败'))
    const savedAt = Date.now()
    tx.objectStore(DRAFT_STORE).put({ key, draft: { ...draft, localSavedAt: savedAt }, savedAt })
  })
}
