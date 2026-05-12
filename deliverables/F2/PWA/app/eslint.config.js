import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from 'eslint-config-prettier';

export default tseslint.config(
  { ignores: ['dist', 'dev-dist', 'coverage'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
  // Per-file overrides for files that intentionally co-locate components with
  // their hooks / variant maps / non-component exports. Splitting these into
  // sibling files would fragment idiomatic React patterns (provider+hook,
  // shadcn/ui component+cva variants) without meaningful benefit. Fast Refresh
  // is not the dominant concern in these files — they're stable boilerplate
  // edited rarely. The exhaustive-deps rule still applies to surface real bugs.
  {
    files: [
      '**/*-context.tsx',
      '**/admin/lib/pages-router.tsx',
      '**/components/ui/button.tsx',
      '**/admin/users/BulkImportModal.tsx',
    ],
    rules: {
      'react-refresh/only-export-components': 'off',
    },
  },
  eslintConfigPrettier,
);
