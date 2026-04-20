import 'vitest';

declare module '@vitest/expect' {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- mirrors upstream `@vitest/expect` Matchers<T = any> signature for declaration merging
  interface Matchers<T = any> {
    toHaveNoViolations(): T;
  }
}
