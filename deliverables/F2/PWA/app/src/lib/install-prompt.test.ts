import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useInstallPrompt } from './install-prompt';

describe('useInstallPrompt', () => {
  let listeners: Record<string, EventListener[]> = {};
  const originalAdd = window.addEventListener.bind(window);
  const originalRemove = window.removeEventListener.bind(window);

  beforeEach(() => {
    listeners = {};
    window.addEventListener = vi.fn((type: string, cb: EventListener) => {
      (listeners[type] ??= []).push(cb);
    }) as typeof window.addEventListener;
    window.removeEventListener = vi.fn((type: string, cb: EventListener) => {
      listeners[type] = (listeners[type] ?? []).filter((c) => c !== cb);
    }) as typeof window.removeEventListener;
  });

  afterEach(() => {
    window.addEventListener = originalAdd;
    window.removeEventListener = originalRemove;
  });

  it('initially reports not installable', () => {
    const { result } = renderHook(() => useInstallPrompt());
    expect(result.current.canInstall).toBe(false);
  });

  it('becomes installable when beforeinstallprompt fires', () => {
    const { result } = renderHook(() => useInstallPrompt());
    const evt = Object.assign(new Event('beforeinstallprompt'), {
      prompt: vi.fn().mockResolvedValue({ outcome: 'accepted' }),
      userChoice: Promise.resolve({ outcome: 'accepted', platform: 'web' }),
      preventDefault: vi.fn(),
    });
    act(() => {
      listeners['beforeinstallprompt']?.forEach((cb) => cb(evt));
    });
    expect(result.current.canInstall).toBe(true);
  });

  it('calls prompt() when install() is invoked', async () => {
    const { result } = renderHook(() => useInstallPrompt());
    const prompt = vi.fn().mockResolvedValue({ outcome: 'accepted' });
    const evt = Object.assign(new Event('beforeinstallprompt'), {
      prompt,
      userChoice: Promise.resolve({ outcome: 'accepted', platform: 'web' }),
      preventDefault: vi.fn(),
    });
    act(() => {
      listeners['beforeinstallprompt']?.forEach((cb) => cb(evt));
    });
    await act(async () => {
      await result.current.install();
    });
    expect(prompt).toHaveBeenCalledOnce();
  });
});
