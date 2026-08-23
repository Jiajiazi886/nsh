const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const projectRoot = path.resolve(__dirname, '..')
const errors = []

function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name)
    return entry.isDirectory() ? walk(target) : [target]
  })
}

for (const filePath of walk(projectRoot)) {
  try {
    if (filePath.endsWith('.json')) JSON.parse(fs.readFileSync(filePath, 'utf8'))
    if (filePath.endsWith('.js')) new vm.Script(fs.readFileSync(filePath, 'utf8'), { filename: filePath })
  } catch (error) {
    errors.push(`${path.relative(projectRoot, filePath)}: ${error.message}`)
  }
}

if (errors.length) {
  console.error(errors.join('\n'))
  process.exit(1)
}

console.log('小程序 JavaScript 与 JSON 工程检查通过')
