/* global React, Icon, Button, IconBtn, Chip, Card, AudioPlayer, DropZone, VU, EmptyState, ErrorState, Skel, MD, StatusPill, CovDots, Segmented */
const { useState, useEffect, useRef, useMemo } = React;

/* ============================================================
   1. LIVE TRANSCRIBE
   ============================================================ */
function PageLiveTranscribe({ lang, target, toast }) {
  const [recording, setRecording] = useState(false);
  const [chunks, setChunks] = useState([]);
  const [permError, setPermError] = useState(false);
  const [wsError, setWsError] = useState(false);
  const tRef = useRef(null);
  const startRef = useRef(null);

  const langObj = window.getLang(lang);
  const noAsr = !langObj.mmsAsr && !langObj.whisper && !langObj.proxy;
  const noMt = !langObj.nllb;

  useEffect(() => () => clearInterval(tRef.current), []);

  const start = () => {
    if (noAsr) return;
    setRecording(true);
    setWsError(false);
    setPermError(false);
    startRef.current = Date.now();
    // Simulate chunks coming in every 4 seconds
    const linesSrc = lang === "ndc" ? window.MOCK_TRANSCRIPT_LINES_NDC : window.MOCK_TRANSCRIPT_LINES_SNA;
    const linesTr = target === "pt" ? window.MOCK_TRANSLATION_LINES_PT : window.MOCK_TRANSLATION_LINES_EN;
    let i = 0;
    tRef.current = setInterval(() => {
      const elapsed = ((Date.now() - startRef.current) / 1000) | 0;
      const stamp = `${String(Math.floor(elapsed / 60)).padStart(2, "0")}:${String(elapsed % 60).padStart(2, "0")}`;
      const src = linesSrc[i % linesSrc.length];
      const tr = noMt ? null : linesTr[i % linesTr.length];
      setChunks(cs => [...cs, { id: Date.now() + "-" + i, ts: stamp, src, tr, mt: noMt ? null : (langObj.nllb ? "nllb" : "none") }]);
      i++;
    }, 2200);
  };
  const stop = () => {
    setRecording(false);
    clearInterval(tRef.current);
  };

  return (
    <div className="page" data-screen-label="01 Live Transcribe">
      <div className="page-header">
        <div className="titles">
          <h1>Live transcribe</h1>
          <div className="sub">
            Real-time speech-to-text from your microphone, with parallel translation into{" "}
            <strong>{target === "pt" ? "Portuguese" : "English"}</strong>.
          </div>
        </div>
        <div className="actions">
          <Button size="sm" iconLeft="download" disabled={chunks.length === 0}>Download .txt</Button>
          <Button size="sm" iconLeft="trash" variant="ghost" disabled={chunks.length === 0} onClick={() => setChunks([])}>Clear</Button>
          <Button size="sm" iconLeft="database" variant="primary" disabled={chunks.length === 0 || recording}>Save session</Button>
        </div>
      </div>

      <div className="record-bay">
        <button
          className={"record-btn" + (recording ? " recording" : "")}
          onClick={recording ? stop : start}
          aria-label={recording ? "Stop recording" : "Start recording"}
          disabled={noAsr}
        >
          <Icon name={recording ? "stop" : "mic"} size={32} />
        </button>
        <div className="record-status">
          {permError ? (
            <span style={{ color: "var(--red)" }}>
              <Icon name="warn" /> Microphone permission denied. Enable it in browser settings to record.
            </span>
          ) : wsError ? (
            <span style={{ color: "var(--red)" }}>
              <Icon name="bolt_off" /> Connection lost. Reconnecting…
            </span>
          ) : recording ? (
            <>
              <Icon name="pulse" />
              Recording — 4-second chunks · streaming over WebSocket
              <VU active />
            </>
          ) : noAsr ? (
            <span style={{ color: "var(--amber)" }}>
              <Icon name="warn" /> No ASR available for {langObj.name}. Pick another language to record.
            </span>
          ) : (
            <>
              Idle. Press to begin. <kbd>Space</kbd> to toggle.
              <VU active={false} />
            </>
          )}
        </div>
      </div>

      <div className="two-col">
        <Stream
          title={`Source · ${langObj.name}`}
          subtitle={langObj.proxy ? `via ${window.getLang(langObj.proxy).name} (proxy)` : "MMS-ASR · 16 kHz"}
          chunks={chunks}
          field="src"
          recording={recording}
        />
        <Stream
          title={`Translation · ${target === "pt" ? "Português" : "English"}`}
          subtitle={noMt ? "no MT engine — transcript only" : "NLLB-200"}
          chunks={chunks}
          field="tr"
          recording={recording}
          italicEmpty
          empty={noMt}
        />
      </div>

      <div className="mt-4 text-xs text-muted row gap-2" style={{ justifyContent: "center" }}>
        <Icon name="info" />
        Audio is buffered locally and only sent to the server while recording.
        Stop and Save to commit the session to the corpus.
      </div>
    </div>
  );
}

function Stream({ title, subtitle, chunks, field, recording, italicEmpty, empty }) {
  const bodyRef = useRef(null);
  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [chunks.length]);
  return (
    <div className="stream">
      <div className="stream-head">
        <div>
          <h3 style={{ fontFamily: "var(--font-serif)", fontWeight: 500, fontSize: 15 }}>{title}</h3>
          <div className="text-xs text-muted">{subtitle}</div>
        </div>
        <div className="row gap-2">
          {recording && <span className="pill"><span className="dot green" style={{ animation: "pulse 1.2s ease-in-out infinite" }} />Live</span>}
          <IconBtn icon="copy" label="Copy all" />
        </div>
      </div>
      <div className="stream-body" ref={bodyRef}>
        {chunks.length === 0 ? (
          <EmptyState
            icon={field === "src" ? "mic" : "globe"}
            title={field === "src" ? "Nothing yet" : "Waiting for source"}
            body={field === "src" ? "Press the mic to start. Transcribed text will appear here in real time." : "Translations will appear as source chunks arrive."}
          />
        ) : (
          chunks.map((c, i) => {
            const text = c[field];
            const isLast = i === chunks.length - 1;
            return (
              <div key={c.id} className={"chunk" + (isLast && recording ? " new" : "")}>
                <span className="ts">{c.ts}</span>
                {text ? (
                  <span className="text">{text}</span>
                ) : (
                  <span className="text italic">(no translation: {c.mt || "none"})</span>
                )}
                <button className="replay" aria-label="Replay this chunk">
                  <Icon name="speaker" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

/* ============================================================
   2. TRANSCRIBE FILE
   ============================================================ */
function PageTranscribeFile({ lang, target, toast }) {
  const [file, setFile] = useState(null);
  const [phase, setPhase] = useState("idle"); // idle | uploading | transcribing | done | error
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const langObj = window.getLang(lang);

  const reset = () => { setFile(null); setPhase("idle"); setProgress(0); setResult(null); };

  const onFile = (f) => {
    setFile({
      name: f.name,
      size: humanSize(f.size),
      duration: "—",
      type: f.type,
    });
  };

  const transcribe = () => {
    setPhase("transcribing");
    setProgress(0);
    let p = 0;
    const id = setInterval(() => {
      p += 8 + Math.random() * 14;
      if (p >= 100) {
        clearInterval(id);
        setProgress(100);
        setPhase("done");
        setResult({
          transcript: window.MOCK_TRANSCRIPT_LINES_SNA.join(" "),
          translation: langObj.nllb ? (target === "pt" ? window.MOCK_TRANSLATION_LINES_PT : window.MOCK_TRANSLATION_LINES_EN).join(" ") : null,
          engine: langObj.whisper ? "whisper-large-v3" : (langObj.mmsAsr ? "mms-1b-all" : "—"),
          mtEngine: langObj.nllb ? "nllb-200-distilled" : null,
        });
      } else {
        setProgress(p);
      }
    }, 220);
  };

  return (
    <div className="page" data-screen-label="02 Transcribe File">
      <div className="page-header">
        <div className="titles">
          <h1>Transcribe a file</h1>
          <div className="sub">Upload an audio file. Get a transcript and (where available) a translation.</div>
        </div>
      </div>

      <div className="col gap-4">
        <DropZone
          file={file}
          onFile={onFile}
          onClear={reset}
          accept="audio/*"
          maxMB={200}
          label="Drop an audio file, or "
        />

        {file && phase === "idle" && (
          <div className="row gap-2" style={{ justifyContent: "flex-end" }}>
            <Button variant="ghost" onClick={reset}>Cancel</Button>
            <Button variant="primary" iconLeft="zap" onClick={transcribe}>
              Transcribe with {langObj.whisper ? "Whisper" : (langObj.mmsAsr ? "MMS-ASR" : "fallback")}
            </Button>
          </div>
        )}

        {phase === "transcribing" && (
          <Card title="Transcribing…" icon="zap" subtitle={`${Math.round(progress)}%`}>
            <div className="progress"><div className="bar" style={{ width: progress + "%" }} /></div>
            <div className="text-xs text-muted mt-2 row gap-2">
              <span className="spin" />
              {progress < 40 ? "Uploading audio…" : progress < 75 ? "Running ASR…" : "Running translation…"}
            </div>
          </Card>
        )}

        {phase === "done" && result && (
          <>
            <Card
              title="Transcript"
              icon="file"
              subtitle={<>engine: <Chip mono outline>{result.engine}</Chip></>}
              actions={
                <div className="row gap-2">
                  <IconBtn icon="copy" label="Copy transcript" />
                  <IconBtn icon="download" label="Download .txt" />
                </div>
              }
            >
              <div style={{ maxHeight: 220, overflowY: "auto", fontSize: 14, lineHeight: 1.7 }}>
                {result.transcript}
              </div>
            </Card>

            <Card
              title={`Translation · ${target === "pt" ? "Português" : "English"}`}
              icon="globe"
              subtitle={result.mtEngine
                ? <>engine: <Chip mono outline>{result.mtEngine}</Chip></>
                : <Chip tone="amber">no MT coverage</Chip>}
              actions={result.translation && (
                <div className="row gap-2">
                  <IconBtn icon="copy" label="Copy translation" />
                  <IconBtn icon="download" label="Download .txt" />
                </div>
              )}
            >
              {result.translation ? (
                <div style={{ maxHeight: 220, overflowY: "auto", fontSize: 14, lineHeight: 1.7 }}>
                  {result.translation}
                </div>
              ) : (
                <EmptyState
                  icon="globe"
                  title="No translation available"
                  body={`${langObj.name} has no NLLB coverage. Transcript only.`}
                />
              )}
            </Card>

            <div className="row gap-2" style={{ justifyContent: "flex-end" }}>
              <Button variant="ghost" onClick={reset}>Try another file</Button>
              <Button iconLeft="refresh">Re-run with different language</Button>
              <Button variant="primary" iconLeft="database">Save to corpus</Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function humanSize(b) {
  if (b < 1024) return b + " B";
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + " KB";
  if (b < 1024 * 1024 * 1024) return (b / 1024 / 1024).toFixed(1) + " MB";
  return (b / 1024 / 1024 / 1024).toFixed(2) + " GB";
}

/* ============================================================
   3. TTS
   ============================================================ */
function PageTTS({ lang, setLang, target, toast }) {
  const langObj = window.getLang(lang);
  const proxyLang = langObj.proxy && window.getLang(langObj.proxy);
  const [text, setText] = useState("Mhoroi, ndinotenda kuti mauya kuno nhasi. Tichakurukura nezve mabhuku matsva atinoshanda nawo.");
  const [generating, setGenerating] = useState(false);
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState(window.MOCK_TTS_SAMPLES);
  const maxLen = 4000;
  const noTts = !langObj.mmsTts;

  const speak = () => {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      const sample = { id: "g" + Date.now(), text, lang, duration: estimateDuration(text), at: "just now" };
      setLatest(sample);
      setHistory(h => [sample, ...h].slice(0, 10));
    }, 1400);
  };

  return (
    <div className="page" data-screen-label="03 TTS">
      <div className="page-header">
        <div className="titles">
          <h1>Text-to-speech</h1>
          <div className="sub">Synthesise speech in {langObj.name} using the MMS-TTS model.</div>
        </div>
      </div>

      {noTts && proxyLang && (
        <div className="card mb-4" style={{ background: "var(--amber-soft)", borderColor: "var(--amber-border)" }}>
          <div className="card-body" style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <Icon name="warn" size={20} />
            <div style={{ flex: 1 }}>
              <strong>No TTS available for {langObj.name}.</strong>
              <div className="text-sm text-2 mt-2">Try <strong>{proxyLang.name}</strong> (<code className="mono">{proxyLang.iso}</code>) — closest available voice. Pronunciation will differ for Ndau-specific lexicon.</div>
            </div>
            <Button onClick={() => setLang(proxyLang.iso)} iconLeft="refresh">Switch to {proxyLang.name}</Button>
          </div>
        </div>
      )}

      {noTts && !proxyLang && (
        <div className="card mb-4" style={{ background: "var(--red-soft)", borderColor: "var(--red-border)" }}>
          <div className="card-body row gap-3">
            <Icon name="alert" size={20} />
            <div>
              <strong>No TTS coverage for {langObj.name}.</strong>
              <div className="text-sm text-2 mt-2">No proxy language has been configured. Speech synthesis is unavailable.</div>
            </div>
          </div>
        </div>
      )}

      <div className="two-col">
        <Card
          title="Text"
          icon="edit"
          subtitle={<span className="text-xs" style={{ color: text.length > maxLen ? "var(--red)" : "var(--muted)" }}>{text.length} / {maxLen}</span>}
        >
          <textarea
            className="textarea"
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder={`Type or paste text in ${langObj.name}…`}
            aria-label="Text to synthesise"
            maxLength={maxLen}
            style={{ minHeight: 180, fontFamily: "var(--font-serif)", fontSize: 15 }}
          />
          <div className="row gap-3 mt-4" style={{ alignItems: "center" }}>
            <div className="field" style={{ margin: 0, flex: 1, maxWidth: 280 }}>
              <label className="label" htmlFor="voice">Voice</label>
              <select id="voice" className="select sm" disabled={noTts}>
                <option>Default MMS voice — female, neutral</option>
                <option disabled>Multi-speaker (coming soon)</option>
              </select>
            </div>
            <div style={{ flex: 1 }} />
            <Button
              variant="primary"
              size="lg"
              iconLeft={generating ? null : "speaker"}
              onClick={speak}
              disabled={noTts || !text.trim() || generating}
              loading={generating}
            >
              {generating ? "Synthesising…" : "Speak"}
            </Button>
          </div>
        </Card>

        <Card
          title="Output"
          icon="speaker"
          subtitle={latest ? <Chip tone="green">ready</Chip> : <Chip outline>idle</Chip>}
        >
          {latest ? (
            <div className="col gap-3">
              <div className="text-sm text-2 font-serif" style={{ fontFamily: "var(--font-serif)", fontSize: 14, fontStyle: "italic", padding: "12px 14px", background: "var(--surface-3)", borderRadius: "var(--r)" }}>
                "{latest.text.length > 200 ? latest.text.slice(0, 200) + "…" : latest.text}"
              </div>
              <AudioPlayer initialDuration={parseFloat(latest.duration.split(":")[1]) || 6} />
              <div className="row gap-2" style={{ justifyContent: "flex-end" }}>
                <Button size="sm" iconLeft="download">.wav</Button>
                <Button size="sm" variant="ghost" iconLeft="copy">Copy URL</Button>
              </div>
            </div>
          ) : (
            <EmptyState
              icon="speaker"
              title="No synthesis yet"
              body="Type text and press Speak. Output will appear here with a downloadable .wav."
            />
          )}
        </Card>
      </div>

      <Card title="Recent" icon="clock" subtitle={`last ${history.length}`} >
        {history.length === 0 ? (
          <EmptyState icon="clock" title="No history" body="Synthesise something to see it here." />
        ) : (
          <div className="col gap-2">
            {history.slice(0, 5).map(h => (
              <div key={h.id} style={{ display: "grid", gridTemplateColumns: "auto 1fr auto auto auto", gap: 12, alignItems: "center", padding: "8px 4px", borderBottom: "1px solid var(--border)" }}>
                <IconBtn icon="play" label={"Play: " + h.text.slice(0, 40)} />
                <div style={{ minWidth: 0 }}>
                  <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: 13 }}>{h.text}</div>
                  <div className="text-xs text-muted">{h.at} · {window.getLang(h.lang)?.name || h.lang}</div>
                </div>
                <Chip mono outline>{h.duration}</Chip>
                <IconBtn icon="download" label="Download" />
                <IconBtn icon="trash" label="Delete" />
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function estimateDuration(text) {
  const s = Math.max(1, Math.round(text.length / 16));
  return `0:${String(s).padStart(2, "0")}`;
}

Object.assign(window, {
  PageLiveTranscribe, PageTranscribeFile, PageTTS, Stream,
});
