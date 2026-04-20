import 'vitest-axe/extend-expect';
import { axe } from 'vitest-axe';
import * as matchers from 'vitest-axe/matchers';
import { expect } from 'vitest';

expect.extend(matchers);

// color-contrast relies on computed CSS which jsdom doesn't resolve; check in Lighthouse instead.
// region only applies to full-page contexts; component-level tests don't need a landmark.
export const AXE_COMPONENT_CONFIG = {
  rules: {
    'color-contrast': { enabled: false },
    region: { enabled: false },
  },
};

export { axe };
