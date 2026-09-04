import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const file = path.join(here, 'CLAUDE.md');
const text = fs.readFileSync(file, 'utf8');

const required = [
  '# CLAUDE.md — Next.js 15 + SQLite SaaS',
  '## Stack and versions',
  '## Project structure',
  '## Naming conventions',
  '## Database rules',
  '## Migration workflow',
  '## Server Components and Client Components',
  '## Server Actions',
  '## Development commands',
  '## Patterns to follow',
  '## What we do not do — and why',
  'pnpm dev',
  'pnpm lint',
  'pnpm typecheck',
  'pnpm test',
  'pnpm db:generate',
  'pnpm db:migrate',
  'pnpm build',
  'better-sqlite3',
  'Drizzle',
  'Server Components',
  'Server Actions',
  'foreign keys',
  'transaction',
  'integer minor units',
  'tenant/account scope',
  'Do not ask generic preference questions already answered by this file.',
  'Never claim a test, migration, build, external API call, or browser check passed unless it was actually run.',
];

const missing = required.filter((needle) => !text.includes(needle));
if (missing.length) {
  console.error('Missing required template contract items:');
  for (const item of missing) console.error(`- ${item}`);
  process.exit(1);
}

const forbidden = [/\bTODO\b/i, /\bTBD\b/i, /<your[- _]/i, /replace me/i];
for (const pattern of forbidden) {
  if (pattern.test(text)) {
    console.error(`Template contains unresolved placeholder matching ${pattern}`);
    process.exit(1);
  }
}

const bullets = text.split('\n').filter((line) => line.startsWith('- '));
if (bullets.length < 70) {
  console.error(`Expected at least 70 concrete rules; found ${bullets.length}`);
  process.exit(1);
}

const reasonSignals = [' because ', ' so ', ' to avoid ', ' prevents ', ' keeps ', ' reduce', ' preserve', ' unacceptable', ' costly', ' easier'];
const reasonBearing = bullets.filter((line) => reasonSignals.some((signal) => line.toLowerCase().includes(signal)));
if (reasonBearing.length < 25) {
  console.error(`Expected at least 25 explicitly reasoned rules; found ${reasonBearing.length}`);
  process.exit(1);
}

console.log(`Template contract valid: ${bullets.length} concrete rules, ${reasonBearing.length} explicitly reasoned rules.`);
