/* Dependency-free SDK. CommonJS for mini-programs/Node; global NshApi for web. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.NshApi = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  class ApiError extends Error {
    constructor(message, status, errorKey, requestId) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.errorKey = errorKey;
      this.requestId = requestId || null;
    }
  }

  function createFetchTransport(fetchImpl) {
    if (typeof fetchImpl !== 'function') throw new TypeError('fetch implementation is required');
    return async function (request) {
      const response = await fetchImpl(request.url, {
        method: request.method,
        headers: request.headers,
        body: request.data === undefined ? undefined : JSON.stringify(request.data),
        credentials: 'omit',
        redirect: 'error'
      });
      let data;
      try { data = await response.json(); } catch (_) { data = null; }
      return { status: response.status, data, headers: response.headers };
    };
  }

  function createWxTransport(wxApi) {
    if (!wxApi || typeof wxApi.request !== 'function') throw new TypeError('wx.request implementation is required');
    return request => new Promise((resolve, reject) => {
      wxApi.request({
        url: request.url, method: request.method, header: request.headers,
        data: request.data, timeout: 15000,
        success: response => resolve({ status: response.statusCode, data: response.data, headers: response.header }),
        fail: () => reject(new ApiError('网络请求失败', 0, 'NETWORK_ERROR'))
      });
    });
  }

  function createClient(options) {
    const { baseUrl, getToken = () => null, transport } = options || {};
    // No URL global dependency: WeChat does not guarantee the browser URL API.
    if (typeof baseUrl !== 'string' || !/^https?:\/\/[^/?#@\s]+(?:\/[^?#\s]*)?$/.test(baseUrl) || /\/api\/v1\/?$/.test(baseUrl)) {
      throw new TypeError('baseUrl must be an absolute API root without credentials/query/version prefix');
    }
    if (typeof transport !== 'function' || typeof getToken !== 'function') throw new TypeError('transport and getToken must be functions');
    const root = baseUrl.replace(/\/+$/, '') + '/api/v1';

    async function request(method, path, data, authenticated = true) {
      const headers = { Accept: 'application/json', 'Content-Type': 'application/json' };
      if (authenticated) {
        const token = await getToken();
        if (token) headers.Authorization = 'Bearer ' + token;
      }
      let response;
      try { response = await transport({ url: root + path, method, headers, data }); }
      catch (_) { throw new ApiError('网络请求失败', 0, 'NETWORK_ERROR'); }
      const body = response && response.data;
      if (!body || typeof body !== 'object' || typeof body.code !== 'number' || typeof body.success !== 'boolean') {
        throw new ApiError('服务器返回了无法识别的响应', response ? response.status : 0, 'INVALID_RESPONSE');
      }
      if (response.status < 200 || response.status >= 300 || body.success !== true || body.code !== 200) {
        throw new ApiError(body.msg || '请求失败', response.status, body.errorKey || 'API_ERROR', body.requestId);
      }
      return body.data;
    }

    function segment(value) {
      if (typeof value !== 'string' || !value) throw new TypeError('invitation code must be a non-empty string');
      return encodeURIComponent(value);
    }

    async function choice(code, kind, data) {
      if (!data || typeof data.memberId !== 'string' || !/^[1-9][0-9]{0,18}$/.test(data.memberId) || (data.memberId.length === 19 && data.memberId > '9223372036854775807')) {
        throw new TypeError('memberId must be a bounded positive decimal string');
      }
      return request('POST', '/invitations/' + segment(code) + '/' + kind, data);
    }

    // No persistence or automatic mutation retries. Caller owns token storage.
    return Object.freeze({
      capabilities: () => request('GET', '/capabilities', undefined, false),
      authConfig: () => request('GET', '/auth/config', undefined, false),
      captcha: () => request('GET', '/auth/captcha', undefined, false),
      login: data => request('POST', '/auth/login', data, false),
      me: () => request('GET', '/auth/me'),
      logout: () => request('POST', '/auth/logout'),
      leave: (code, data) => choice(code, 'leave', data),
      signup: (code, data) => choice(code, 'signup', data)
    });
  }

  return { createClient, createFetchTransport, createWxTransport, ApiError };
});
