import { Component, ElementRef, HostListener, ViewChild, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { IconComponent } from '../core/icon.component';
import { LanguageStateService } from '../core/language-state.service';
import { LangResponse, TranslationTarget } from '../core/models';

interface Tab {
  id: string;
  label: string;
  short: string;
  icon: string;
}

const TABS: Tab[] = [
  { id: 'live', label: 'Live transcribe', short: 'Live', icon: 'mic' },
  { id: 'file', label: 'Transcribe file', short: 'File', icon: 'file_audio' },
  { id: 'tts', label: 'TTS', short: 'TTS', icon: 'speaker' },
  { id: 'resources', label: 'Resources', short: 'Refs', icon: 'book' },
  { id: 'upload', label: 'Upload', short: 'Upload', icon: 'upload_cloud' },
];

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive, RouterOutlet, IconComponent],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
})
export class ShellComponent {
  state = inject(LanguageStateService);
  tabs = TABS;

  pickerOpen = signal(false);
  query = signal('');
  activeIndex = signal(0);

  @ViewChild('searchInput') searchInput?: ElementRef<HTMLInputElement>;

  filteredLangs = computed<LangResponse[]>(() => {
    const q = this.query().trim().toLowerCase();
    const all = this.state.languages();
    if (!q) return all;
    return all.filter(
      (l) =>
        l.name.toLowerCase().includes(q) ||
        l.iso.includes(q) ||
        l.country.toLowerCase().includes(q),
    );
  });

  coverageNeedsBanner = computed<boolean>(() => {
    const l = this.state.selectedLang();
    if (!l) return false;
    return l.status !== 'native' || !l.mms_iso || !l.mms_tts;
  });

  coverageTone = computed<'amber' | 'red' | ''>(() => {
    const l = this.state.selectedLang();
    if (!l) return '';
    if (l.status === 'missing') return 'red';
    if (l.status === 'proxy') return 'amber';
    return '';
  });

  togglePicker() {
    this.pickerOpen.update((v) => !v);
    if (this.pickerOpen()) {
      this.query.set('');
      this.activeIndex.set(0);
      setTimeout(() => this.searchInput?.nativeElement.focus(), 30);
    }
  }

  pickLang(iso: string) {
    this.state.setLang(iso);
    this.pickerOpen.set(false);
  }

  setTarget(t: TranslationTarget) {
    this.state.setTarget(t);
  }

  onPickerKey(e: KeyboardEvent) {
    const list = this.filteredLangs();
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.activeIndex.update((a) => Math.min(a + 1, list.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.activeIndex.update((a) => Math.max(a - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const pick = list[this.activeIndex()];
      if (pick) this.pickLang(pick.iso);
    } else if (e.key === 'Escape') {
      this.pickerOpen.set(false);
    }
  }

  @HostListener('document:mousedown', ['$event'])
  onClickOutside(ev: MouseEvent) {
    if (!this.pickerOpen()) return;
    const target = ev.target as HTMLElement;
    if (!target.closest('.lang-picker')) {
      this.pickerOpen.set(false);
    }
  }

  toggleTheme() {
    this.state.toggleTheme();
  }
}
