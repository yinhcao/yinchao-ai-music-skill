import { fileURLToPath } from 'node:url'

import { FileSystemSkillProvider } from '@deepseek-ai/dsh-skill-filesystem'

export const name = 'yinchao-ai-music'
export const inject = ['skills']

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
}
