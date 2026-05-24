import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ApiService } from './api.service';
import { LangResponse, TranslationTarget } from './models';

type Theme = 'light' | 'dark';

@Injectable({ providedIn: 'root' })
export class LanguageStateService {
  private api = inject(ApiService);

  readonly languages = toSignal(this.api.listLanguages(), { initialValue: [] as LangResponse[] });

  readonly selectedIso = signal<string>('sna');
  readonly target = signal<TranslationTarget>('en');
  readonly theme = signal<Theme>(this.initialTheme());

  readonly selectedLang = computed<LangResponse | undefined>(() =>
    this.languages().find((l) => l.iso === this.selectedIso()),
  );

  constructor() {
    effect(() => {
      const t = this.theme();
      document.documentElement.setAttribute('data-theme', t);
      try {
        localStorage.setItem('bp-theme', t);
      } catch {
        /* private mode etc. */
      }
    });
  }

  setLang(iso: string) {
    this.selectedIso.set(iso);
  }

  setTarget(t: TranslationTarget) {
    this.target.set(t);
  }

  setTheme(t: Theme) {
    this.theme.set(t);
  }

  toggleTheme() {
    this.theme.update((t) => (t === 'dark' ? 'light' : 'dark'));
  }

  private initialTheme(): Theme {
    try {
      const stored = localStorage.getItem('bp-theme');
      if (stored === 'dark' || stored === 'light') return stored;
    } catch {
      /* noop */
    }
    if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }
}
