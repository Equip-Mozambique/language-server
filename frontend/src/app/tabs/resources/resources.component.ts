import { Component, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MarkdownComponent } from 'ngx-markdown';
import { IconComponent } from '../../core/icon.component';
import { ApiService } from '../../core/api.service';
import { LanguageStateService } from '../../core/language-state.service';
import { ResourceBundle } from '../../core/models';

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
