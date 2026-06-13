const RECOVERY_PREFIX = 'page-error-recovery:'
const RECOVERY_TTL = 10 * 60 * 1000

function getErrorMessage(error) {
  if (!error) return ''
  if (typeof error === 'string') return error
  if (error.message) return error.message
  if (error.reason) return getErrorMessage(error.reason)
  if (error.error) return getErrorMessage(error.error)
  if (error.payload) return getErrorMessage(error.payload)
  return String(error)
}

function isRecoverablePageError(error) {
  const message = getErrorMessage(error)
  if (!message) return false
  return [
    'Failed to fetch dynamically imported module',
    'Importing a module script failed',
    'error loading dynamically imported module',
    'Loading chunk',
    'ChunkLoadError',
    'vite:preloadError',
    'dynamically imported module'
  ].some(pattern => message.includes(pattern))
}

function buildRecoveryKey(kind, error) {
  const message = getErrorMessage(error)
    .replace(/\?.*$/g, '')
    .replace(/https?:\/\/[^)\s]+/g, 'asset-url')
    .slice(0, 180)
  return `${RECOVERY_PREFIX}${kind}:${location.pathname}:${message}`
}

function shouldReloadOnce(kind, error) {
  const key = buildRecoveryKey(kind, error)
  const now = Date.now()
  const lastReloadAt = Number(sessionStorage.getItem(key) || 0)
  if (lastReloadAt && now - lastReloadAt < RECOVERY_TTL) {
    return false
  }
  sessionStorage.setItem(key, String(now))
  return true
}

function reloadForRecovery(kind, error) {
  if (!isRecoverablePageError(error) || !shouldReloadOnce(kind, error)) return false
  console.warn('[page-error-recovery] reload page once for recoverable error:', error)
  location.reload()
  return true
}

export function installPageErrorRecovery(app, router) {
  const previousErrorHandler = app.config.errorHandler

  app.config.errorHandler = (error, instance, info) => {
    if (!reloadForRecovery(`vue:${info || 'runtime'}`, error)) {
      previousErrorHandler?.(error, instance, info)
      if (!previousErrorHandler) {
        console.error(error)
      }
    }
  }

  router.onError(error => {
    reloadForRecovery('router', error)
  })

  window.addEventListener('vite:preloadError', event => {
    event.preventDefault()
    reloadForRecovery('vite-preload', event)
  })

  window.addEventListener('unhandledrejection', event => {
    if (reloadForRecovery('promise', event.reason)) {
      event.preventDefault()
    }
  })

  window.addEventListener(
    'error',
    event => {
      reloadForRecovery('window', event.error || event.message)
    },
    true
  )
}
