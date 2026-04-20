import { spawnSync } from 'node:child_process';

const result = spawnSync('vite', ['build'], {
  stdio: 'inherit',
  shell: true,
  env: { ...process.env, BUNDLE_VISUALIZE: '1' },
});
process.exit(result.status ?? 0);
