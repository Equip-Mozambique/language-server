import { Component, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MarkdownComponent } from 'ngx-markdown';
import { IconComponent } from '../../core/icon.component';
import { ApiService } from '../../core/api.service';
import { LanguageStateService } from '../../core/language-state.service';
import { ResourceBundle, UploadRow } from '../../core/models';

type SortKey = 'id' | 'tt' | 'tv' | 'dt' | 'cn';
type SortDir = 'asc' | 'desc';

@Component({
  selector: 'app-resources',
  standalone: true,
  imports: [CommonModule, MarkdownComponent, IconComponent],
  templateUrl: './resources.component.html',
  styleUrl: './resources.component.scss',
})
export class ResourcesComponent {
  private api = inject(ApiService);
  state = inject(LanguageStateService);

  bundle = signal<ResourceBundle | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  // Catalog sort state
  sortKey = signal<SortKey>('dt');
  sortDir = signal<SortDir>('desc');

  // Corpus filters
  filterRegister = signal<string | null>(null);
  filterLicense = signal<string | null>(null);

  registers = ['read', 'conversational', 'news', 'religious', 'code-switch'];
  licenses = ['CC-BY', 'CC-BY-NC', 'CC0', 'proprietary'];

  catalogSorted = computed(() => {
    const b = this.bundle();
    if (!b) return [];
    const k = this.sortKey();
    const dir = this.sortDir() === 'asc' ? 1 : -1;
    return [...b.dbs_bibles].sort((a, b2) => {
      const av = (a as any)[k] ?? '';
      const bv = (b2 as any)[k] ?? '';
      if (av < bv) return -dir;
      if (av > bv) return dir;
      return 0;
    });
  });

  corpusFiltered = computed<UploadRow[]>(() => {
    const b = this.bundle();
    if (!b) return [];
    const reg = this.filterRegister();
    const lic = this.filterLicense();
    return b.uploads.filter(
      (u) => (!reg || u.register === reg) && (!lic || u.license === lic),
    );
  });

  statusClass = computed<string>(() => {
    const cov = this.bundle()?.model_coverage;
    if (!cov) return '';
    if (cov.mms_iso) return 'green';
    if (cov.proxy_iso) return 'amber';
    return 'red';
  });

  statusLabel = computed<string>(() => {
    const cov = this.bundle()?.model_coverage;
    if (!cov) return '';
    if (cov.mms_iso) return 'Native';
    if (cov.proxy_iso) return 'Proxy';
    return 'Missing';
  });

  constructor() {
    effect(
      () => {
        const iso = this.state.selectedIso();
        if (!iso) return;
        this.loading.set(true);
        this.error.set(null);
        this.api.getResources(iso).subscribe({
          next: (b) => {
            this.bundle.set(b);
            this.loading.set(false);
          },
          error: (e) => {
            this.error.set(e?.error?.detail ?? e.message ?? 'load failed');
            this.loading.set(false);
          },
        });
      },
      { allowSignalWrites: true },
    );
  }

  sortBy(k: SortKey) {
    if (this.sortKey() === k) {
      this.sortDir.update((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      this.sortKey.set(k);
      this.sortDir.set('asc');
    }
  }

  toggleRegister(r: string) {
    this.filterRegister.update((cur) => (cur === r ? null : r));
  }

  toggleLicense(l: string) {
    this.filterLicense.update((cur) => (cur === l ? null : l));
  }

  coverageTone(on: boolean | string | null | undefined, proxy: boolean): 'green' | 'amber' | 'red' {
    if (on) return 'green';
    if (proxy) return 'amber';
    return 'red';
  }

  coverageLabel(on: boolean | string | null | undefined, proxy: boolean): string {
    if (on) return 'available';
    if (proxy) return 'via proxy';
    return 'missing';
  }
}
