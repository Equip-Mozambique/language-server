import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ApiService } from '../../core/api.service';
import { LanguageStateService } from '../../core/language-state.service';
import { TranscribeResponse } from '../../core/models';

@Component({
  selector: 'app-transcribe-file',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatCardModule, MatProgressBarModule],
  templateUrl: './transcribe-file.component.html',
  styleUrl: './transcribe-file.component.scss',
})
export class TranscribeFileComponent {
  private api = inject(ApiService);
  state = inject(LanguageStateService);

  file = signal<File | null>(null);
  result = signal<TranscribeResponse | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  onFile(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.file.set(input.files[0]);
      this.result.set(null);
      this.error.set(null);
    }
  }

  transcribe() {
    const f = this.file();
    if (!f) return;
    this.loading.set(true);
    this.error.set(null);
    this.api
      .transcribeFile(f, this.state.selectedIso(), this.state.target())
      .subscribe({
        next: (r) => {
          this.result.set(r);
          this.loading.set(false);
        },
        error: (e) => {
          this.error.set(e?.error?.detail ?? e.message ?? 'transcribe failed');
          this.loading.set(false);
        },
      });
  }
}
