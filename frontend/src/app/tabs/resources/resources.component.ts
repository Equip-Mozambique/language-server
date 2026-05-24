import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MarkdownComponent } from 'ngx-markdown';
import { ApiService } from '../../core/api.service';
import { LanguageStateService } from '../../core/language-state.service';
import { ResourceBundle } from '../../core/models';

@Component({
  selector: 'app-resources',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatTableModule, MatChipsModule, MarkdownComponent],
  templateUrl: './resources.component.html',
  styleUrl: './resources.component.scss',
})
export class ResourcesComponent {
  private api = inject(ApiService);
  state = inject(LanguageStateService);

  bundle = signal<ResourceBundle | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);

  bibleCols = ['id', 'tt', 'tv', 'dt', 'cn'];
  uploadCols = ['uuid', 'filename_orig', 'speaker_id', 'dialect', 'register', 'license', 'uploaded_at'];

  constructor() {
    effect(() => {
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
    });
  }
}
