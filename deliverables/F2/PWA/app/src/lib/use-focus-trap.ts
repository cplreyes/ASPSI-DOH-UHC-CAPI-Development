import { useEffect, type RefObject } from 'react';

/**
 * #284: trap focus inside a blocking overlay (KillSwitch / SpecDrift).
 *
 * When `active`, this:
 *  - remembers what was focused, then moves focus into `containerRef`
 *    (the first focusable child, else the container itself — so a
 *    button-less terminal overlay like KillSwitch still pulls focus
 *    off the form behind it),
 *  - keeps Tab / Shift+Tab cycling within the container (the form
 *    behind the overlay can no longer be reached or edited by keyboard
 *    or AT — it was only blocked at submit before),
 *  - restores focus to the previously-focused element on deactivate.
 *
 * Deliberately framework-light (no focus-trap dep): these overlays have
 * 0–1 focusable children, so the full library would be overkill.
 */
export function useFocusTrap(
  containerRef: RefObject<HTMLElement | null>,
  active: boolean,
): void {
  useEffect(() => {
    if (!active) return;
    const container = containerRef.current;
    if (!container) return;

    const previouslyFocused = document.activeElement as HTMLElement | null;

    // No offsetParent/getClientRects visibility filter on purpose: the
    // overlay only mounts when active and its content is always visible,
    // and those APIs return falsy under jsdom (untestable) and are flaky
    // for fixed-position containers in real browsers.
    const focusables = (): HTMLElement[] =>
      Array.from(
        container.querySelectorAll<HTMLElement>(
          'a[href],button:not([disabled]),textarea,input:not([disabled]),select:not([disabled]),[tabindex]:not([tabindex="-1"])',
        ),
      );

    const first = focusables()[0];
    if (first) {
      first.focus();
    } else {
      // Button-less overlay (KillSwitch): make the container itself the
      // focus sink so keyboard/AT focus leaves the form behind.
      container.tabIndex = -1;
      container.focus();
    }

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const items = focusables();
      if (items.length === 0) {
        // Nothing to cycle to — keep focus pinned on the container.
        e.preventDefault();
        container.focus();
        return;
      }
      const firstEl = items[0];
      const lastEl = items[items.length - 1];
      const activeEl = document.activeElement;
      if (e.shiftKey && activeEl === firstEl) {
        e.preventDefault();
        lastEl.focus();
      } else if (!e.shiftKey && activeEl === lastEl) {
        e.preventDefault();
        firstEl.focus();
      } else if (!container.contains(activeEl)) {
        // Focus somehow escaped (initial Tab from outside) — pull it back.
        e.preventDefault();
        firstEl.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown, true);
    return () => {
      document.removeEventListener('keydown', onKeyDown, true);
      previouslyFocused?.focus?.();
    };
  }, [containerRef, active]);
}
