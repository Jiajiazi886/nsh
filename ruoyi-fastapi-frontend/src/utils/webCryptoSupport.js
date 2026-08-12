/**
 * 判断当前运行环境能否使用传输加密依赖的 Web Crypto。
 * 普通 HTTP 域名通常不会暴露 subtle，localhost 和 HTTPS 不受影响。
 */
export function hasUsableWebCrypto(runtime = globalThis) {
  return Boolean(runtime?.crypto?.subtle)
}
