// Generated from backend Pydantic models — keep field names in sync with
// src/aiserver/api/routes_*.py and src/aiserver/resources.py.

export interface LangResponse {
  iso: string;
  name: string;
  country: string;
  mms_iso: string | null;
  mms_tts: string | null;
  whisper_code: string | null;
  preferred_stt: 'whisper' | 'mms' | 'toucan';
  preferred_tts: 'mms' | 'piper' | 'xtts' | 'toucan';
  proxy_iso: string | null;
  effective_iso: string;
  status: 'native' | 'proxy' | 'missing';
}

export type TranslationTarget = 'en' | 'pt';

export interface TranscribeResponse {
  lang: string;
  target: TranslationTarget;
  transcript: string;
  translation: string;
  engine: 'whisper-translate' | 'nllb' | 'none';
  covered: boolean;
}

export interface UploadRow {
  uuid: string;
  iso: string;
  filename_orig: string | null;
  path: string;
  media_type: string | null;
  duration_s: number | null;
  speaker_id: string | null;
  dialect: string | null;
  register: string | null;
  license: string | null;
  transcript: string | null;
  transcript_path: string | null;
  uploaded_at: string;
  sha256: string;
}

export interface ResourceBundle {
  iso: string;
  name: string;
  country: string;
  model_coverage: {
    mms_iso: string | null;
    mms_tts: string | null;
    whisper_code: string | null;
    preferred_stt: string;
    preferred_tts: string;
    proxy_iso: string | null;
  };
  research_md: string;
  dbs_bibles: Array<{
    id: string;
    iso: string;
    tt?: string;
    tv?: string;
    dt?: string;
    cn?: string;
    ln?: string;
  }>;
  uploads: UploadRow[];
  uploads_count: number;
}

export interface WsChunkResponse {
  chunk_id: number | null;
  transcript: string;
  translation: string;
  engine: string;
  covered: boolean;
}
