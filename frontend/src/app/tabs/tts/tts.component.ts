import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { ApiService } from '../../core/api.service';
import { LanguageStateService } from '../../core/language-state.service';

@Component({
  selector: 'app-tts',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
  ],
  templateUrl: './tts.component.html',
  styleUrl: './tts.component.scss',
})
export class TtsComponent {
  private api = inject(ApiService);
  state = inject(LanguageStateService);

  text = signal('');
  audioUrl = signal<string | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  speak() {
    const t = this.text().trim();
    const lang = this.state.selectedIso();
    if (!t || !lang) return;
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
}
