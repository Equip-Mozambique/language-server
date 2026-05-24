import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IconComponent } from '../../core/icon.component';
import { ApiService } from '../../core/api.service';
import { LanguageStateService } from '../../core/language-state.service';

interface FormState {
  speaker_id: string;
  dialect: string;
  register: string;
  license: string;
  transcript: string;
}

const EMPTY_FORM: FormState = {
  speaker_id: '',
  dialect: '',
  register: 'read',
  license: 'unknown',
  transcript: '',
};

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.scss',
})
export class UploadComponent {
  private api = inject(ApiService);
  state = inject(LanguageStateService);

  registers = ['read', 'conversational', 'news', 'religious', 'code-switch', 'other'];
  licenses = ['CC-BY', 'CC-BY-NC', 'CC0', 'proprietary', 'unknown'];

  file = signal<File | null>(null);
  dragOver = signal(false);
  form = signal<FormState>({ ...EMPTY_FORM });
  loading = signal(false);
  error = signal<string | null>(null);
  ok = signal<{ uuid: string; sha256: string } | null>(null);

  onPick(e: Event) {
    const input = e.target as HTMLInputElement;
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
    this.ok.set(null);
    this.error.set(null);
  }

  clearFile() {
    this.file.set(null);
  }

  patch<K extends keyof FormState>(k: K, v: FormState[K]) {
    this.form.update((f) => ({ ...f, [k]: v }));
  }

  submit() {
    const f = this.file();
    if (!f) return;
    this.loading.set(true);
    this.error.set(null);
    this.ok.set(null);
    const meta = { ...this.form(), filename_orig: f.name, media_type: f.type };
    this.api.uploadFile(this.state.selectedIso(), f, meta).subscribe({
      next: (row) => {
        this.ok.set({ uuid: row.uuid, sha256: row.sha256 });
        this.loading.set(false);
        this.file.set(null);
        this.form.set({ ...EMPTY_FORM });
      },
      error: (e) => {
        this.error.set(e?.error?.detail ?? e.message ?? 'upload failed');
        this.loading.set(false);
      },
    });
  }
}
