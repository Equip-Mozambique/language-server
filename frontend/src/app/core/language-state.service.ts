import { Injectable, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ApiService } from './api.service';
import { LangResponse, TranslationTarget } from './models';

@Injectable({ providedIn: 'root' })
export class LanguageStateService {
  private api = inject(ApiService);

  readonly languages = toSignal(this.api.listLanguages(), { initialValue: [] as LangResponse[] });

  readonly selectedIso = signal<string>('sna');
  readonly target = signal<TranslationTarget>('en');

  readonly selectedLang = computed<LangResponse | undefined>(() =>
    this.languages().find((l) => l.iso === this.selectedIso()),
  );

  setLang(iso: string) {
    this.selectedIso.set(iso);
  }

  setTarget(t: TranslationTarget) {
    this.target.set(t);
  }
}
