import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IconComponent } from '../../core/icon.component';
import { ApiService } from '../../core/api.service';
import { LanguageStateService } from '../../core/language-state.service';

@Component({
  selector: 'app-tts',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  templateUrl: './tts.component.html',
  styleUrl: './tts.component.scss',
})
export class TtsComponent {
  private api = inject(ApiService);
  state = inject(LanguageStateService);

  text = signal('Mhoroi, ndinotenda kuti mauya kuno nhasi.');
  audioUrl = signal<string | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  readonly MAX_LEN = 4000;

  hasTts = computed(() => !!this.state.selectedLang()?.mms_tts);
  proxyLang = computed(() => {
    const l = this.state.selectedLang();
    if (!l || l.mms_tts) return null;
    return l.proxy_iso;
  });

  speak() {
    const t = this.text().trim();
    const lang = this.state.selectedIso();
    if (!t || !lang || !this.hasTts()) return;
    this.loading.set(true);
    this.error.set(null);
    this.api.tts(lang, t).subscribe({
      next: (blob) => {
        if (this.audioUrl()) URL.revokeObjectURL(this.audioUrl()!);
        this.audioUrl.set(URL.createObjectURL(blob));
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e?.error?.detail ?? e.message ?? 'TTS failed');
        this.loading.set(false);
      },
    });
  }

  switchToProxy() {
    const p = this.proxyLang();
    if (p) this.state.setLang(p);
  }
}
