import { Component, Input, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

const PATHS: Record<string, string> = {
  search: '<circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/>',
  chev_down: '<path d="M3.5 6L8 10.5L12.5 6"/>',
  chev_right: '<path d="M6 3.5L10.5 8L6 12.5"/>',
  chev_up: '<path d="M3.5 10L8 5.5L12.5 10"/>',
  x: '<path d="M3.5 3.5L12.5 12.5"/><path d="M12.5 3.5L3.5 12.5"/>',
  check: '<path d="M3 8.5L6.5 12L13 4"/>',
  mic: '<rect x="6" y="2" width="4" height="8" rx="2"/><path d="M3.5 8a4.5 4.5 0 0 0 9 0"/><path d="M8 12.5V14.5"/><path d="M5.5 14.5h5"/>',
  stop: '<rect x="4" y="4" width="8" height="8" rx="1.5"/>',
  play: '<path d="M5 3.5L13 8L5 12.5z" fill="currentColor"/>',
  pause: '<rect x="4.5" y="3.5" width="2.5" height="9" rx="0.5" fill="currentColor"/><rect x="9" y="3.5" width="2.5" height="9" rx="0.5" fill="currentColor"/>',
  speaker: '<path d="M3 6v4h2.5L9 13V3L5.5 6z"/><path d="M11.5 5.5a3.5 3.5 0 0 1 0 5"/>',
  download: '<path d="M8 2V10.5"/><path d="M4.5 7L8 10.5L11.5 7"/><path d="M3 13.5H13"/>',
  upload_cloud: '<path d="M4 11a3 3 0 0 1 0.5 -5.95A4 4 0 0 1 12 5.5a2.5 2.5 0 0 1 0 5"/><path d="M8 7.5V13.5"/><path d="M5.5 10L8 7.5L10.5 10"/>',
  file: '<path d="M4 1.5h5.5L12 4V14a0.5 0.5 0 0 1 -0.5 0.5h-7.5A0.5 0.5 0 0 1 3.5 14V2a0.5 0.5 0 0 1 0.5 -0.5z"/><path d="M9.5 1.5V4H12"/>',
  file_audio: '<path d="M4 1.5h5.5L12 4V14a0.5 0.5 0 0 1 -0.5 0.5h-7.5A0.5 0.5 0 0 1 3.5 14V2a0.5 0.5 0 0 1 0.5 -0.5z"/><path d="M9.5 1.5V4H12"/><path d="M6 9v3"/><path d="M8 8v5"/><path d="M10 10v1"/>',
  trash: '<path d="M3 4.5h10"/><path d="M5 4.5V3a0.5 0.5 0 0 1 0.5 -0.5h5A0.5 0.5 0 0 1 11 3V4.5"/><path d="M4.5 4.5L5 13a0.5 0.5 0 0 0 0.5 0.5h5A0.5 0.5 0 0 0 11 13L11.5 4.5"/>',
  zap: '<path d="M8.5 1.5L3 9h4l-0.5 5.5L13 7H9z" fill="currentColor" stroke="none"/>',
  alert: '<path d="M8 1.5L14.5 13H1.5z"/><path d="M8 6V9"/><circle cx="8" cy="11.2" r="0.6" fill="currentColor" stroke="none"/>',
  info: '<circle cx="8" cy="8" r="6.5"/><path d="M8 7V11.5"/><circle cx="8" cy="5" r="0.6" fill="currentColor" stroke="none"/>',
  sun: '<circle cx="8" cy="8" r="3"/><path d="M8 1.5V3"/><path d="M8 13V14.5"/><path d="M1.5 8H3"/><path d="M13 8H14.5"/><path d="M3.4 3.4L4.5 4.5"/><path d="M11.5 11.5L12.6 12.6"/><path d="M12.6 3.4L11.5 4.5"/><path d="M4.5 11.5L3.4 12.6"/>',
  moon: '<path d="M13 9.5a5.5 5.5 0 1 1 -6.5 -7a4.5 4.5 0 0 0 6.5 7z"/>',
  globe: '<circle cx="8" cy="8" r="6.5"/><path d="M1.5 8H14.5"/><path d="M8 1.5C10 4 10 12 8 14.5C6 12 6 4 8 1.5z"/>',
  layers: '<path d="M8 2L1.5 5.5L8 9L14.5 5.5L8 2z"/><path d="M1.5 10.5L8 14L14.5 10.5"/>',
  book: '<path d="M3 2.5h5a2.5 2.5 0 0 1 2.5 2.5v9a2 2 0 0 0 -2 -2H3z M13 2.5h-3a2.5 2.5 0 0 0 -2.5 2.5v9a2 2 0 0 1 2 -2H13z"/>',
  database: '<ellipse cx="8" cy="4" rx="5.5" ry="2"/><path d="M2.5 4V8C2.5 9.1 5 10 8 10C11 10 13.5 9.1 13.5 8V4"/><path d="M2.5 8V12C2.5 13.1 5 14 8 14C11 14 13.5 13.1 13.5 12V8"/>',
  edit: '<path d="M3 13H6L13 6L10 3L3 10z"/><path d="M9 4L12 7"/>',
  filter: '<path d="M1.5 3h13L9.5 9V13.5L6.5 12V9z"/>',
  more: '<circle cx="3" cy="8" r="1" fill="currentColor" stroke="none"/><circle cx="8" cy="8" r="1" fill="currentColor" stroke="none"/><circle cx="13" cy="8" r="1" fill="currentColor" stroke="none"/>',
  refresh: '<path d="M2 8a6 6 0 0 1 10.5 -4"/><path d="M14 8a6 6 0 0 1 -10.5 4"/><path d="M10 4H12.5V1.5"/><path d="M6 12H3.5V14.5"/>',
  hash: '<path d="M3 6h10"/><path d="M3 10h10"/><path d="M6 2L5 14"/><path d="M11 2L10 14"/>',
  toc: '<path d="M3 4h10"/><path d="M3 8h6"/><path d="M3 12h8"/>',
  menu: '<path d="M2.5 4.5h11"/><path d="M2.5 8h11"/><path d="M2.5 11.5h11"/>',
  link: '<path d="M7 9a2.5 2.5 0 0 0 3.5 0L13 6.5a2.5 2.5 0 0 0 -3.5 -3.5L8.5 4"/><path d="M9 7a2.5 2.5 0 0 0 -3.5 0L3 9.5a2.5 2.5 0 0 0 3.5 3.5L7.5 12"/>',
  copy: '<rect x="5" y="5" width="9" height="9" rx="1"/><path d="M3 11V3a0.5 0.5 0 0 1 0.5 -0.5H11"/>',
  pulse: '<path d="M1.5 8H4l2 -4 4 8 2 -4h2.5"/>',
  wave: '<path d="M2 8V8.001"/><path d="M5 6V10"/><path d="M8 4V12"/><path d="M11 6V10"/><path d="M14 7V9"/>',
  user: '<circle cx="8" cy="5.5" r="2.5"/><path d="M3 13.5a5 5 0 0 1 10 0"/>',
  clock: '<circle cx="8" cy="8" r="6.5"/><path d="M8 4.5V8L10.5 9.5"/>',
  warn: '<path d="M8 2L14.5 13.5H1.5z"/><path d="M8 6V9.5"/><circle cx="8" cy="11.8" r="0.6" fill="currentColor" stroke="none"/>',
  inbox: '<path d="M2 9L4 3h8l2 6"/><path d="M2 9V13a0.5 0.5 0 0 0 0.5 0.5h11A0.5 0.5 0 0 0 14 13V9"/><path d="M2 9H5L6 11h4l1 -2h3"/>',
  check_circle: '<circle cx="8" cy="8" r="6.5"/><path d="M5 8.5L7 10.5L11 6"/>',
};

@Component({
  selector: 'app-icon',
  standalone: true,
  template: `<span class="ic" [innerHTML]="svg"></span>`,
  styles: [
    `:host { display: inline-flex; line-height: 0; }
     .ic { display: inline-flex; }
     .ic ::ng-deep svg { display: block; }`,
  ],
})
export class IconComponent {
  private san = inject(DomSanitizer);

  @Input() name: keyof typeof PATHS | string = '';
  @Input() size = 16;

  get svg(): SafeHtml {
    const body = PATHS[this.name] ?? '';
    const html =
      `<svg width="${this.size}" height="${this.size}" viewBox="0 0 16 16" ` +
      `fill="none" stroke="currentColor" stroke-width="1.5" ` +
      `stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
    return this.san.bypassSecurityTrustHtml(html);
  }
}
