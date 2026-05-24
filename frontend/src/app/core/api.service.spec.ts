import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api.service';

describe('ApiService', () => {
  let api: ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('GET /api/languages returns the registry', (done) => {
    api.listLanguages().subscribe((langs) => {
      expect(langs.length).toBe(2);
      expect(langs[0].iso).toBe('sna');
      done();
    });
    const req = http.expectOne('/api/languages');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        iso: 'sna',
        name: 'Shona',
        country: 'ZW',
        mms_iso: 'sna',
        mms_tts: 'sna',
        whisper_code: 'sn',
        preferred_stt: 'whisper',
        preferred_tts: 'mms',
        proxy_iso: null,
        effective_iso: 'sna',
        status: 'native',
      },
      {
        iso: 'ndc',
        name: 'Ndau',
        country: 'MZ/ZW',
        mms_iso: null,
        mms_tts: null,
        whisper_code: null,
        preferred_stt: 'mms',
        preferred_tts: 'mms',
        proxy_iso: 'sna',
        effective_iso: 'sna',
        status: 'proxy',
      },
    ]);
  });

  it('GET /api/resources/{iso}', (done) => {
    api.getResources('seh').subscribe((bundle) => {
      expect(bundle.iso).toBe('seh');
      done();
    });
    const req = http.expectOne('/api/resources/seh');
    req.flush({
      iso: 'seh',
      name: 'Sena',
      country: 'MZ',
      model_coverage: {
        mms_iso: 'seh',
        mms_tts: 'seh',
        whisper_code: null,
        preferred_stt: 'mms',
        preferred_tts: 'mms',
        proxy_iso: null,
      },
      research_md: '',
      dbs_bibles: [],
      uploads: [],
      uploads_count: 0,
    });
  });

  it('POST /api/tts returns a blob', (done) => {
    api.tts('sna', 'Mhoroi').subscribe((blob) => {
      expect(blob.size).toBeGreaterThanOrEqual(0);
      done();
    });
    const req = http.expectOne('/api/tts');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ lang: 'sna', text: 'Mhoroi' });
    req.flush(new Blob([new Uint8Array([1, 2, 3])], { type: 'audio/wav' }));
  });
});
