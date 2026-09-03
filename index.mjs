import { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

import { credentialRef } from '@deepseek-ai/dsh-credentials'
import { FileSystemSkillProvider } from '@deepseek-ai/dsh-skill-filesystem'
import { defineTool } from '@deepseek-ai/dsh-tools'

export const name = 'yinchao-ai-music'
export const inject = ['credentials', 'skills', 'subprocess', 'tools']

const API_KEY_REF = credentialRef('YINCHAO_API_KEY')
const TOOL_TIMEOUT_MS = 660_000
const SCRIPT_PATH = fileURLToPath(
  new URL('./skills/yinchao-ai-music/scripts/yinchao_music.py', import.meta.url),
)
const SCRIPT_DIR = dirname(SCRIPT_PATH)

function redactCredential(text, credential) {
  if (!credential || !text.includes(credential)) return text
  return text.split(credential).join('[REDACTED]')
}

async function resolvePython(ctx, signal) {
  let lastError
  for (const command of ['python3', 'python']) {
    try {
      return await ctx.subprocess.resolveExecutable(command, undefined, signal)
    } catch (error) {
      if (signal.aborted) throw error
      lastError = error
    }
  }
  throw new Error('未找到 Python 3；请先安装 Python 3.10 或更高版本', {
    cause: lastError,
  })
}

function collectedText(reader) {
  if (reader === undefined) return { text: '', lossy: false }
  const output = reader.readFrom(0)
  return { text: output.text.trim(), lossy: output.lossy }
}

function registerMusicTool(ctx) {
  ctx.tools.register(defineTool({
    name: 'yinchao_music',
    description:
      '通过音潮开放平台生成歌曲、纯音乐、歌词、参考音频作品或歌曲续写。'
      + 'API Key 由 DeepSeek Harness 凭据系统提供，绝不能放入工具参数。',
    parameters: {
      action: {
        type: 'string',
        required: true,
        enum: ['song', 'instrumental', 'lyrics', 'reference', 'extend', 'status'],
        description: '要执行的音潮操作。',
      },
      argv: {
        type: 'array',
        required: true,
        items: { type: 'string' },
        description:
          '传给音潮脚本的参数列表，不包含 action、API Key、--env-file、--json 或 --human。',
      },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          json: { type: 'string', required: true },
        },
      },
      render: (_args, value) => [{ type: 'text', text: value.json }],
    },
    timeoutMs: TOOL_TIMEOUT_MS,
    async execute({ action, argv }, exec) {
      if (
        argv.includes('--human')
        || argv.includes('--json')
        || argv.some((value) => value === '--env-file' || value.startsWith('--env-file='))
      ) {
        throw new Error(
          'yinchao_music 的 argv 不能包含 --human、--json 或 --env-file',
        )
      }

      const resolved = await ctx.credentials.resolve(API_KEY_REF)
      if (resolved === undefined) {
        throw new Error(
          '尚未配置 YINCHAO_API_KEY。请在 $DSH_HOME/.credentials.yaml '
          + '（默认 ~/.dsh/.credentials.yaml）的 refs 下配置；'
          + '不要把完整 API Key 发到对话中。',
        )
      }
      if (argv.some((value) => value.includes(resolved.value))) {
        throw new Error('yinchao_music 的 argv 不能包含 API Key')
      }

      const python = await resolvePython(ctx, exec.signal)
      const child = ctx.subprocess.spawn({
        argv: [python, SCRIPT_PATH, action, ...argv, '--json'],
        cwd: SCRIPT_DIR,
        signal: exec.signal,
        graceMs: 3_000,
        env: {
          // DSH scrubs ambient credential-shaped variables. An explicit entry
          // is the deliberate, tool-owned path that reaches only this child.
          YINCHAO_API_KEY: resolved.value,
        },
        stdio: {
          stdin: 'ignore',
          stdout: {
            maxBytes: 1_000_000,
            spill: { maxBytes: 4_000_000 },
          },
          stderr: { maxBytes: 128_000 },
        },
      })

      const outcome = await child.done
      const stdout = collectedText(child.collected.stdout)
      const stderr = collectedText(child.collected.stderr)
      const safeStdout = redactCredential(stdout.text, resolved.value)
      const safeStderr = redactCredential(stderr.text, resolved.value)

      if (stdout.lossy) {
        throw new Error('音潮脚本输出超过 DSH 工具的安全上限')
      }
      if (outcome.exitCode !== 0) {
        throw new Error(safeStderr || safeStdout || '音潮脚本执行失败')
      }

      let payload
      try {
        payload = JSON.parse(safeStdout)
      } catch (error) {
        throw new Error('音潮脚本没有返回有效 JSON', { cause: error })
      }
      return { json: JSON.stringify(payload) }
    },
  }))
}

export function apply(ctx) {
  const skillDir = fileURLToPath(new URL('./skills', import.meta.url))

  ctx.skills.registerProvider(
    (control) =>
      new FileSystemSkillProvider(ctx, control, {
        providerName: 'yinchao-ai-music',
        includeDefaultRoots: false,
        bundledSkillDir: skillDir,
      }),
  )

  registerMusicTool(ctx)
}
