const test = require('node:test');
const assert = require('node:assert/strict');
const { createClient, createFetchTransport, createWxTransport, ApiError } = require('../client.js');

test('shared client sends latest token and only string IDs', async () => {
  const requests = [];
  let token = 'session-a';
  const client = createClient({ baseUrl: 'https://example.invalid/prod-api', getToken: () => token, transport: async request => {
    requests.push(request);
    return { status: 200, data: { code: 200, success: true, requestId: 'req_test', data: { userId: '9223372036854775807' } } };
  }});
  const me = await client.me();
  token = 'session-b';
  await client.leave('邀请/甲', { memberId: '9', remark: '请假' });
  assert.equal(me.userId, '9223372036854775807');
  assert.equal(requests[0].headers.Authorization, 'Bearer session-a');
  assert.equal(requests[1].headers.Authorization, 'Bearer session-b');
  assert.equal(requests[1].url, 'https://example.invalid/prod-api/api/v1/invitations/%E9%82%80%E8%AF%B7%2F%E7%94%B2/leave');
  await assert.rejects(client.leave('test', { memberId: 9 }), /memberId/);
});

test('errors retain status, stable key and request ID without retrying mutations', async () => {
  let calls = 0;
  const client = createClient({ baseUrl: 'https://example.invalid', transport: async () => {
    calls++;
    return { status: 403, data: { code: 403, success: false, errorKey: 'MEMBER_NOT_OWNER', requestId: 'req_denied', msg: '无权操作' } };
  }});
  await assert.rejects(client.leave('test', { memberId: '9' }), error => error instanceof ApiError && error.status === 403 && error.errorKey === 'MEMBER_NOT_OWNER' && error.requestId === 'req_denied');
  assert.equal(calls, 1);
});

test('login never uses or retains current token', async () => {
  const requests = [];
  const client = createClient({ baseUrl: 'https://example.invalid', getToken: () => 'private-token', transport: async request => {
    requests.push(request);
    return { status: 200, data: { code: 200, success: true, data: { accessToken: 'new-token' } } };
  }});
  assert.equal((await client.login({ userName: 'demo', password: 'synthetic' })).accessToken, 'new-token');
  assert.equal(requests[0].headers.Authorization, undefined);
});

test('fetch adapter serializes JSON and handles non-JSON errors safely', async () => {
  let init;
  const transport = createFetchTransport(async (url, options) => {
    init = options;
    return { status: 200, headers: new Map(), json: async () => ({ code: 200, success: true, data: null }) };
  });
  await transport({ url: 'https://example.invalid', method: 'POST', headers: {}, data: { memberId: '9' } });
  assert.equal(init.body, '{"memberId":"9"}');
  const failing = createClient({ baseUrl: 'https://example.invalid', transport: createFetchTransport(async () => ({ status: 502, headers: new Map(), json: async () => { throw new Error('private-html'); } })) });
  await assert.rejects(failing.me(), error => error.errorKey === 'INVALID_RESPONSE' && !error.message.includes('private-html'));
});

test('wx.request adapter has same contract', async () => {
  const requests = [];
  const transport = createWxTransport({ request: options => {
    requests.push(options);
    options.success({ statusCode: 200, header: { 'X-Request-ID': 'req_wx' }, data: { code: 200, success: true, data: { userId: '23' } } });
  }});
  const client = createClient({ baseUrl: 'https://example.invalid', transport, getToken: () => 'session-wx' });
  assert.equal((await client.me()).userId, '23');
  assert.equal(requests[0].header.Authorization, 'Bearer session-wx');
  assert.equal(requests[0].timeout, 15000);
});

test('network failures are sanitized and are not retried', async () => {
  const client = createClient({ baseUrl: 'https://example.invalid', transport: async () => { throw new Error('password-private'); } });
  await assert.rejects(client.me(), error => error.errorKey === 'NETWORK_ERROR' && !error.message.includes('password-private'));
});

test('base URL cannot duplicate the version prefix or include credentials', () => {
  for (const baseUrl of ['https://example.invalid/api/v1', 'https://user:secret@example.invalid', '/dev-api', 'https://example.invalid?token=secret']) {
    assert.throws(() => createClient({ baseUrl, transport: async () => {} }), /baseUrl/);
  }
});
