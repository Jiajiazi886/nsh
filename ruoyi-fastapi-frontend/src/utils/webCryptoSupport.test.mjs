import assert from 'node:assert/strict'

import { hasUsableWebCrypto } from './webCryptoSupport.js'

assert.equal(hasUsableWebCrypto({}), false)
assert.equal(hasUsableWebCrypto({ crypto: {} }), false)
assert.equal(hasUsableWebCrypto({ crypto: { subtle: {} } }), true)

console.log('webCryptoSupport tests passed')
