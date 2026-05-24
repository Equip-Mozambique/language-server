import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from '../../core/icon.component';
import { ApiService } from '../../core/api.service';
import { LanguageStateService } from '../../core/language-state.service';
import { TranscribeResponse } from '../../core/models';

@Component({
  selector: 'app-transcribe-file',
  standalone: true,
  imports: [CommonModule, IconComponent],
  templateUrl: './transcribe-file.component.html',
  styleUrl: './transcribe-file.component.scss',
})
export class TranscribeFileComponent {
  private api = inject(ApiService);
  state = inject(LanguageStateService);

  file = signal<File | null>(null);
  dragOver = signal(false);
  result = signal<TranscribeResponse | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  onPick(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files?.[0]) this.setFile(input.files[0]);
  }

  onDrop(e: DragEvent) {
    e.preventDefault();
    this.dragOver.set(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) this.setFile(f);
  }

  onDragOver(e: DragEvent) {
    e.preventDefault();
    this.dragOver.set(true);
  }

  onDragLeave() {
    this.dragOver.set(false);
  }

  private setFile(f: File) {
    this.file.set(f);
    this.result.set(null);
    this.error.set(null);
  }

  clear() {
    this.file.set(null);
    this.result.set(null);
    this.error.set(null);
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
