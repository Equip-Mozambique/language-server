import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
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
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressBarModule,
  ],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.scss',
})
export class UploadComponent {
  private api = inject(ApiService);
  state = inject(LanguageStateService);

  registers = ['read', 'conversational', 'news', 'religious', 'code-switch', 'other'];
  licenses = ['CC-BY', 'CC-BY-NC', 'CC0', 'proprietary', 'unknown'];

  file = signal<File | null>(null);
  form = signal<FormState>({ ...EMPTY_FORM });
  loading = signal(false);
  error = signal<string | null>(null);
  ok = signal<{ uuid: string; sha256: string } | null>(null);

  onFile(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files?.[0]) {
      this.file.set(input.files[0]);
      this.ok.set(null);
      this.error.set(null);
    }
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
