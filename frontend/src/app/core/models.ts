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

export interface DbpFileset {
  id: string;
  label: string;
  type: string;
  scope: string;
  bitrate: string | null;
  asset_id: string | null;
  codec: string | null;
}

export interface DbpBible {
  id: string;
  name: string;
  name_vernacular: string;
  scope: string;
  filesets: DbpFileset[];
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
    nllb: boolean;
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
  dbp_bibles: DbpBible[];
  uploads: UploadRow[];
  uploads_count: number;
  corpus?: CorpusSummary;
  readiness?: ReadinessBundle | null;
}

export interface CorpusAudioFileset {
  fileset_id: string;
  path: string;
  chapter_count: number;
  file_count: number;
  total_bytes: number;
  total_duration_s: number;
  has_text_in_manifest: boolean;
}

export interface CorpusTextVersion {
  version_abbr: string;
  path: string;
  version_id: number | null;
  chapter_count: number;
  verse_count: number;
}

export interface CorpusVideoFile {
  source: string;
  name: string;
  path: string;
  bytes: number;
}

export interface CorpusBlob {
  path: string;
  file_count: number;
  total_bytes: number;
}

export interface CorpusTrainingPairs {
  path: string;
  pair_count: number;
}

export interface CorpusSummary {
  audio_filesets: CorpusAudioFileset[];
  text_versions: CorpusTextVersion[];
  video_files: CorpusVideoFile[];
  storyrunners: CorpusBlob | null;
  scriptureearth: CorpusBlob | null;
  training_pairs: CorpusTrainingPairs | null;
}

export type ReadinessTier =
  | 'bibleless' | 'bootstrap' | 'emerging' | 'adapter' | 'production' | 'mature';

export type ReadinessAxis = 'asr' | 'tts' | 'text';

export interface ReadinessReport {
  axis: ReadinessAxis;
  iso: string;
  score: number;                          // 0-100
  tier: ReadinessTier;
  breakdown: Record<string, number>;
  missing_resources: string[];
  recommended_next_actions: string[];
  flags: string[];
  notes: string[];
}

export interface ReadinessBundle {
  asr: ReadinessReport;
  tts: ReadinessReport;
  text: ReadinessReport;
  overall: number;                         // weighted 0-100
}

export interface WsChunkResponse {
  chunk_id: number | null;
  transcript: string;
  translation: string;
  engine: string;
  covered: boolean;
}
