export const DEFAULT_LOGIN_REDIRECT_PATH = '/index'

const INVALID_REDIRECT_VALUES = new Set(['false', 'true', 'null', 'undefined'])

export function resolveLoginRedirectPath(redirect, defaultPath = DEFAULT_LOGIN_REDIRECT_PATH) {
  const candidate = Array.isArray(redirect) ? redirect[0] : redirect
  if (typeof candidate !== 'string') {
    return defaultPath
  }

  const path = candidate.trim()
  if (!path || INVALID_REDIRECT_VALUES.has(path.toLowerCase())) {
    return defaultPath
  }

  if (path.startsWith('//') || /^[a-z][a-z\d+\-.]*:/i.test(path)) {
    return defaultPath
  }

  if (!path.startsWith('/') || path.startsWith('/login')) {
    return defaultPath
  }

  return path
}
