import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'resources' },
  {
    path: 'live',
    loadComponent: () =>
      import('./tabs/live-transcribe/live-transcribe.component').then(
        (m) => m.LiveTranscribeComponent,
      ),
  },
  {
    path: 'file',
    loadComponent: () =>
      import('./tabs/transcribe-file/transcribe-file.component').then(
        (m) => m.TranscribeFileComponent,
      ),
  },
  {
    path: 'tts',
    loadComponent: () =>
      import('./tabs/tts/tts.component').then((m) => m.TtsComponent),
  },
  {
    path: 'resources',
    loadComponent: () =>
      import('./tabs/resources/resources.component').then(
        (m) => m.ResourcesComponent,
      ),
  },
  {
    path: 'upload',
    loadComponent: () =>
      import('./tabs/upload/upload.component').then((m) => m.UploadComponent),
  },
];
