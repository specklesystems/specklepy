import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import process from 'node:process'

export default function atlasSync(pi) {
  const cwd = process.cwd()
  const atlasRoot =
    process.env.ATLAS_ROOT ||
    (existsSync(resolve(cwd, 'atlas/scripts/check-fresh.sh'))
      ? cwd
      : resolve(cwd, '..'))
  const script = resolve(atlasRoot, 'atlas/scripts/check-fresh.sh')
  if (!existsSync(script)) return

  // ADR-0008: sync in the factory, before omp discovers skills and MCP servers.
  const result = spawnSync('bash', [script, '--sync', cwd], {
    cwd,
    encoding: 'utf8',
    input: '',
    timeout: 30_000,
    env: { ...process.env, CLAUDE_PROJECT_DIR: '' }
  })
  const message = [result.stdout, result.stderr, result.error?.message]
    .filter(Boolean)
    .join('\n')
    .trim()
  if (!message) return

  pi.on('session_start', (_event, ctx) => {
    ctx.ui.notify(message, result.status === 0 ? 'info' : 'warning')
    pi.sendMessage(
      { customType: 'atlas-agent-config', content: message, display: false },
      { triggerTurn: false }
    )
  })
}
