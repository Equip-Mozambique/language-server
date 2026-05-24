import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  LangResponse,
  ResourceBundle,
  TranscribeResponse,
  TranslationTarget,
  UploadRow,
} from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = '/api';

  listLanguages(): Observable<LangResponse[]> {
    return this.http.get<LangResponse[]>(`${this.base}/languages`);
  }

  getLanguage(iso: string): Observable<LangResponse> {
    return this.http.get<LangResponse>(`${this.base}/languages/${iso}`);
  }

  transcribeFile(
    audio: Blob,
    lang: string,
    target: TranslationTarget,
  ): Observable<TranscribeResponse> {
    const form = new FormData();
    form.append('audio', audio, 'clip.wav');
    return this.http.post<TranscribeResponse>(
      `${this.base}/transcribe?lang=${encodeURIComponent(lang)}&target=${target}`,
      form,
    );
  }

  tts(lang: string, text: string): Observable<Blob> {
    return this.http.post(`${this.base}/tts`, { lang, text }, { responseType: 'blob' });
  }

  uploadFile(
    iso: string,
    audio: Blob,
    meta: Partial<{
      speaker_id: string;
      dialect: string;
      register: string;
      license: string;
      transcript: string;
      filename_orig: string;
      media_type: string;
    }>,
  ): Observable<UploadRow> {
    const form = new FormData();
    form.append('iso', iso);
    form.append('audio', audio, meta.filename_orig || 'upload.bin');
    for (const [k, v] of Object.entries(meta)) {
      if (v != null) form.append(k, v);
    }
    return this.http.post<UploadRow>(`${this.base}/uploads`, form);
  }

  listUploads(iso: string): Observable<UploadRow[]> {
    return this.http.get<UploadRow[]>(`${this.base}/uploads/${iso}`);
  }

  getResources(iso: string): Observable<ResourceBundle> {
    return this.http.get<ResourceBundle>(`${this.base}/resources/${iso}`);
  }
}
