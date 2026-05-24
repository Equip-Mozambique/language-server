/* global React, Icon, Button, IconBtn, Chip, Card, AudioPlayer, DropZone, EmptyState, ErrorState, Skel, MD, StatusPill, CovDots */
const { useState, useEffect, useRef, useMemo } = React;

/* ============================================================
   4. RESOURCES
   ============================================================ */
function PageResources({ lang, target }) {
  const langObj = window.getLang(lang);
  const md = window.getResearch(lang);
  const toc = window.getResearchToc(lang);
  const catalog = window.MOCK_BIBLE_CATALOG[lang] || [];
  const audio = window.MOCK_BIBLE_AUDIO[lang] || [];
  const corpus = window.MOCK_UPLOADED_CORPUS[lang] || [];

  const [activeToc, setActiveToc] = useState(toc[0]);

  // Sort state for catalog
  const [catSort, setCatSort] = useState({ key: "year", dir: "desc" });
  const catalogSorted = useMemo(() => {
    const c = [...catalog];
    c.sort((a, b) => {
      const k = catSort.key;
      const av = a[k], bv = b[k];
      if (av < bv) return catSort.dir === "asc" ? -1 : 1;
      if (av > bv) return catSort.dir === "asc" ? 1 : -1;
      return 0;
    });
    return c;
  }, [catalog, catSort]);
  const sortBy = (key) => setCatSort(s => s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" });

  // Filter chips for corpus
  const [filterReg, setFilterReg] = useState(null);
  const [filterLic, setFilterLic] = useState(null);
  const filteredCorpus = useMemo(() => corpus.filter(c =>
    (!filterReg || c.register === filterReg) &&
    (!filterLic || c.license === filterLic)
  ), [corpus, filterReg, filterLic]);

  return (
    <div className="page" data-screen-label="04 Resources">
      <div className="page-header">
        <div className="titles">
          <h1>{langObj.name} <span className="mono text-muted" style={{ fontFamily: "var(--font-mono)", fontSize: 17, fontWeight: 400 }}>· {langObj.iso}</span></h1>
          <div className="sub">Reference data, research notes, and corpus for this language.</div>
        </div>
        <div className="actions">
          <StatusPill status={langObj.status} />
          <Chip outline mono>{langObj.country}</Chip>
        </div>
      </div>

      <div className="res-grid">
        <div className="col gap-4">
          {/* 1. Model coverage */}
          <Card title="Model coverage" icon="layers" subtitle={<StatusPill status={langObj.status} />}>
            <div className="row gap-3" style={{ flexWrap: "wrap" }}>
              <CoverageBadge label="Whisper"  on={langObj.whisper} />
              <CoverageBadge label="MMS-ASR"  on={langObj.mmsAsr}  proxy={langObj.proxy && !langObj.mmsAsr} />
              <CoverageBadge label="MMS-TTS"  on={langObj.mmsTts}  proxy={langObj.proxy && !langObj.mmsTts} />
              <CoverageBadge label="NLLB"     on={langObj.nllb} />
              {langObj.proxy && (
                <div className="row gap-2" style={{ marginLeft: "auto", padding: "6px 12px", background: "var(--amber-soft)", color: "var(--amber)", borderRadius: "var(--r)", fontSize: 12 }}>
                  <Icon name="link" />
                  Proxies to <strong style={{ marginLeft: 4 }}>{window.getLang(langObj.proxy)?.name}</strong>
                  <code className="mono" style={{ background: "transparent" }}>({langObj.proxy})</code>
                </div>
              )}
            </div>
          </Card>

          {/* 2. Research deep-dive */}
          <Card title="Research notes" icon="book" subtitle={<span className="text-xs text-muted">last updated 12 days ago</span>}>
            <MD source={md} />
          </Card>

          {/* 3. DBS Bible catalog */}
          <Card
            title="DBS Bible catalog"
            icon="hash"
            subtitle={`${catalog.length} entries`}
            actions={<IconBtn icon="refresh" label="Refresh from DBS API" />}
          >
            {catalog.length === 0 ? (
              <EmptyState icon="hash" title="No catalog entries yet" body="No Digital Bible Society records found for this language." />
            ) : (
              <table className="tbl">
                <thead>
                  <tr>
                    <th className="sortable" onClick={() => sortBy("id")}>ID</th>
                    <th className="sortable" onClick={() => sortBy("title")}>Title (EN)</th>
                    <th>Vernacular title</th>
                    <th className="sortable num" onClick={() => sortBy("year")}>Year</th>
                    <th>Country</th>
                  </tr>
                </thead>
                <tbody>
                  {catalogSorted.map(r => (
                    <tr key={r.id}>
                      <td><Chip mono outline>{r.id}</Chip></td>
                      <td>{r.title}</td>
                      <td style={{ fontFamily: "var(--font-serif)", fontStyle: "italic", color: "var(--text-2)" }}>{r.vern}</td>
                      <td className="num">{r.year}</td>
                      <td><Chip outline mono>{r.country}</Chip></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          {/* 4. DBP audio inventory */}
          <Card
            title="DBP audio Bible inventory"
            icon="speaker"
            subtitle={`${audio.length} bible${audio.length === 1 ? "" : "s"}`}
          >
            {audio.length === 0 ? (
              <EmptyState icon="speaker" title="No audio Bibles" body="DBP has no audio inventory for this language. Try the proxy language if configured." />
            ) : (
              <div className="col gap-3">
                {audio.map(b => (
                  <div key={b.id} style={{ border: "1px solid var(--border)", borderRadius: "var(--r)", overflow: "hidden" }}>
                    <div style={{ display: "flex", alignItems: "center", padding: "10px 14px", gap: 12, background: "var(--surface-2)", borderBottom: "1px solid var(--border)" }}>
                      <Chip mono outline>{b.id}</Chip>
                      <strong style={{ fontSize: 14 }}>{b.name}</strong>
                      <Chip tone="accent">{b.scope}</Chip>
                      <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--muted)" }}>{b.filesets.length} fileset{b.filesets.length === 1 ? "" : "s"}</span>
                    </div>
                    {b.filesets.map(fs => (
                      <div key={fs.id} style={{ display: "grid", gridTemplateColumns: "1fr auto auto auto", gap: 12, alignItems: "center", padding: "12px 14px", borderTop: "1px solid var(--border)" }}>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 500 }}>{fs.label}</div>
                          <div className="text-xs text-muted">{fs.size}</div>
                        </div>
                        <FilesetStatus fs={fs} />
                        <span className="text-xs text-muted mono" style={{ fontFamily: "var(--font-mono)" }}>
                          {fs.status === "downloaded" ? `${fs.chapters} ch` : fs.status === "partial" ? `${fs.chapters} / ${fs.totalChapters}` : `${fs.chapters} ch`}
                        </span>
                        {fs.status === "downloaded" ? (
                          <Button size="sm" variant="ghost" iconLeft="trash">Remove</Button>
                        ) : fs.status === "partial" ? (
                          <Button size="sm" iconLeft="download">Resume</Button>
                        ) : (
                          <Button size="sm" variant="primary" iconLeft="download">Download</Button>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* 5. Uploaded corpus */}
          <Card
            title="Uploaded corpus"
            icon="database"
            subtitle={`${filteredCorpus.length} of ${corpus.length} files`}
          >
            {corpus.length === 0 ? (
              <EmptyState
                icon="database"
                title="No uploads yet for this language"
                body="Add training data in the Upload tab. Audio, transcripts, and subtitle files are all accepted."
                action={<Button iconLeft="upload_cloud">Go to Upload</Button>}
              />
            ) : (
              <>
                <div className="row gap-2 mb-4" style={{ flexWrap: "wrap" }}>
                  <span className="text-xs text-muted" style={{ marginRight: 4 }}><Icon name="filter" /> Register:</span>
                  {["read", "conversational", "news", "religious", "code-switch"].map(r => (
                    <button key={r} className={"chip" + (filterReg === r ? " accent" : " outline")} style={{ cursor: "pointer" }}
                      onClick={() => setFilterReg(filterReg === r ? null : r)}
                    >{r}</button>
                  ))}
                  <span style={{ width: 1, height: 16, background: "var(--border)", margin: "0 6px" }} />
                  <span className="text-xs text-muted" style={{ marginRight: 4 }}>License:</span>
                  {["CC-BY", "CC-BY-NC", "CC0", "proprietary"].map(r => (
                    <button key={r} className={"chip" + (filterLic === r ? " accent" : " outline")} style={{ cursor: "pointer" }}
                      onClick={() => setFilterLic(filterLic === r ? null : r)}
                    >{r}</button>
                  ))}
                </div>
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Filename</th>
                      <th>Speaker</th>
                      <th>Dialect</th>
                      <th>Register</th>
                      <th>License</th>
                      <th>Uploaded</th>
                      <th className="num">Duration</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCorpus.map(c => (
                      <tr key={c.id}>
                        <td><span className="mono text-sm" style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{c.filename}</span></td>
                        <td><Chip mono outline>{c.speaker}</Chip></td>
                        <td>{c.dialect}</td>
                        <td><Chip>{c.register}</Chip></td>
                        <td><Chip outline>{c.license}</Chip></td>
                        <td className="text-muted text-sm">{c.uploaded}</td>
                        <td className="num">{c.duration}</td>
                        <td className="actions">
                          <IconBtn icon="play" label="Play" />
                          <IconBtn icon="more" label="More actions" />
                        </td>
                      </tr>
                    ))}
                    {filteredCorpus.length === 0 && (
                      <tr><td colSpan={8}><EmptyState icon="filter" title="No matches" body="Adjust your filters." /></td></tr>
                    )}
                  </tbody>
                </table>
              </>
            )}
          </Card>
        </div>

        {/* Sticky TOC */}
        <aside className="res-toc">
          <h4><Icon name="toc" /> On this page</h4>
          <ol>
            <li><a href="#coverage" className={activeToc === "Coverage" ? "active" : ""} onClick={() => setActiveToc("Coverage")}>Model coverage</a></li>
            {toc.map(t => (
              <li key={t}><a href={`#${slug(t)}`} className={activeToc === t ? "active" : ""} onClick={() => setActiveToc(t)}>{t}</a></li>
            ))}
            <li><a href="#catalog" className={activeToc === "Catalog" ? "active" : ""} onClick={() => setActiveToc("Catalog")}>DBS catalog</a></li>
            <li><a href="#audio"   className={activeToc === "Audio"   ? "active" : ""} onClick={() => setActiveToc("Audio")}>DBP audio</a></li>
            <li><a href="#corpus"  className={activeToc === "Corpus"  ? "active" : ""} onClick={() => setActiveToc("Corpus")}>Uploaded corpus</a></li>
          </ol>
        </aside>
      </div>
    </div>
  );
}

function slug(s) { return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }

function CoverageBadge({ label, on, proxy }) {
  const tone = on ? "green" : proxy ? "amber" : "red";
  const text = on ? "available" : proxy ? "via proxy" : "missing";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", border: "1px solid var(--border)", borderRadius: "var(--r)", background: "var(--surface)" }}>
      <span className={"pill"}><span className={"dot " + tone} />{label}</span>
      <span className="text-xs text-muted">{text}</span>
    </div>
  );
}
function FilesetStatus({ fs }) {
  if (fs.status === "downloaded") return <Chip tone="green">downloaded</Chip>;
  if (fs.status === "partial")    return <Chip tone="amber">{Math.round(fs.chapters / fs.totalChapters * 100)}% downloaded</Chip>;
  return <Chip outline>not downloaded</Chip>;
}

/* ============================================================
   5. UPLOAD
   ============================================================ */
function PageUpload({ lang, toast }) {
  const langObj = window.getLang(lang);
  const [file, setFile] = useState(null);
  const [speaker, setSpeaker] = useState("");
  const [dialect, setDialect] = useState("");
  const [register, setRegister] = useState("read");
  const [license, setLicense] = useState("CC-BY");
  const [showTranscript, setShowTranscript] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [recent, setRecent] = useState([]);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const dialectSuggestions = window.MOCK_DIALECT_SUGGESTIONS[lang] || [];
  const speakerSuggestions = window.MOCK_SPEAKER_IDS[lang] || [];

  const canSubmit = !!file && speaker.trim() && dialect.trim() && register && license && !uploading;

  const submit = () => {
    setUploading(true);
    setProgress(0);
    setError(null);
    let p = 0;
    const id = setInterval(() => {
      p += 8 + Math.random() * 16;
      if (p >= 100) {
        clearInterval(id);
        setUploading(false);
        // Simulate a duplicate error sometimes
        const isDupe = Math.random() < 0.15;
        if (isDupe) {
          setError({ kind: "dupe", existing: "a1f2-c3d4" });
          setProgress(0);
        } else {
          const uuid = Math.random().toString(36).slice(2, 6) + "-" + Math.random().toString(36).slice(2, 6);
          const entry = { id: uuid, filename: file.name, speaker, dialect, register, license, at: "just now" };
          setRecent(r => [entry, ...r].slice(0, 5));
          setSuccess(entry);
          setFile(null);
          setSpeaker(""); setDialect("");
          setTimeout(() => setSuccess(null), 8000);
        }
      } else setProgress(p);
    }, 180);
  };

  return (
    <div className="page" data-screen-label="05 Upload">
      <div className="page-header">
        <div className="titles">
          <h1>Upload to corpus</h1>
          <div className="sub">Add audio, transcript or subtitle files to the {langObj.name} training corpus.</div>
        </div>
        <div className="actions">
          <Chip outline mono>target: {langObj.iso}</Chip>
        </div>
      </div>

      {success && (
        <div className="card mb-4" style={{ background: "var(--green-soft)", borderColor: "var(--green-border)" }}>
          <div className="card-body row gap-3" style={{ alignItems: "center" }}>
            <Icon name="check_circle" size={20} style={{ color: "var(--green)" }} />
            <div style={{ flex: 1 }}>
              <strong style={{ color: "var(--green)" }}>Upload complete.</strong>
              <span className="text-sm text-2" style={{ marginLeft: 8 }}>
                Assigned UUID <Chip mono outline>{success.id}</Chip>
              </span>
            </div>
            <Button size="sm" iconLeft="book">View in Resources</Button>
            <IconBtn icon="x" label="Dismiss" onClick={() => setSuccess(null)} />
          </div>
        </div>
      )}

      {error && error.kind === "dupe" && (
        <div className="card mb-4" style={{ background: "var(--red-soft)", borderColor: "var(--red-border)" }}>
          <div className="card-body row gap-3" style={{ alignItems: "center" }}>
            <Icon name="alert" size={20} style={{ color: "var(--red)" }} />
            <div style={{ flex: 1 }}>
              <strong style={{ color: "var(--red)" }}>Duplicate upload.</strong>
              <div className="text-sm text-2 mt-2">A file with this audio checksum already exists: <Chip mono outline>{error.existing}</Chip>. Open the existing entry, or rename and try again.</div>
            </div>
            <Button size="sm" iconLeft="link">Open existing</Button>
            <Button size="sm" variant="ghost" onClick={() => setError(null)}>Dismiss</Button>
          </div>
        </div>
      )}

      <div className="two-col">
        <div className="col gap-4">
          <Card title="1 · File" icon="file_audio">
            <DropZone
              file={file}
              onFile={(f) => setFile({ name: f.name, size: humanSize(f.size), type: f.type, duration: "—" })}
              onClear={() => setFile(null)}
              accept="audio/*,.txt,.srt,.vtt"
              maxMB={500}
              label="Drop audio or transcript, or "
              sub="Accepts audio/*, .txt, .srt, .vtt. Up to 500 MB."
            />
          </Card>

          <Card title="2 · Metadata" icon="edit">
            <div className="field">
              <label className="label" htmlFor="speaker">Speaker ID <span className="text-xs text-muted">(required)</span></label>
              <input
                id="speaker"
                className="input"
                value={speaker}
                onChange={e => setSpeaker(e.target.value)}
                list="speaker-list"
                placeholder="e.g. MM-014"
              />
              <datalist id="speaker-list">
                {speakerSuggestions.map(s => <option key={s} value={s} />)}
              </datalist>
              {speakerSuggestions.length > 0 && (
                <div className="hint">Recently used: {speakerSuggestions.slice(0, 4).map((s, i) => (
                  <span key={s}>
                    {i > 0 && ", "}
                    <button onClick={() => setSpeaker(s)} style={{ background: "none", border: 0, color: "var(--accent-fg)", cursor: "pointer", padding: 0, fontFamily: "var(--font-mono)", fontSize: 11.5 }}>{s}</button>
                  </span>
                ))}</div>
              )}
            </div>

            <div className="field">
              <label className="label" htmlFor="dialect">Dialect <span className="text-xs text-muted">(required)</span></label>
              <input
                id="dialect"
                className="input"
                value={dialect}
                onChange={e => setDialect(e.target.value)}
                placeholder="e.g. Karanga"
              />
              {dialectSuggestions.length > 0 && (
                <div className="row gap-2 mt-2" style={{ flexWrap: "wrap" }}>
                  <span className="text-xs text-muted">Suggested:</span>
                  {dialectSuggestions.map(d => (
                    <button key={d} className={"chip " + (dialect === d ? "accent" : "outline")} style={{ cursor: "pointer" }}
                      onClick={() => setDialect(d)}>{d}</button>
                  ))}
                </div>
              )}
            </div>

            <div className="field">
              <label className="label">Register</label>
              <div className="radio-chips">
                {["read", "conversational", "news", "religious", "code-switch", "other"].map(r => (
                  <label key={r}>
                    <input type="radio" name="register" checked={register === r} onChange={() => setRegister(r)} />
                    <span className="pip">{r}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="field" style={{ marginBottom: 0 }}>
              <label className="label">License</label>
              <div className="radio-chips">
                {[
                  ["CC-BY", "Attribution — anyone may reuse, with credit."],
                  ["CC-BY-NC", "Attribution, non-commercial only."],
                  ["CC0", "Public domain. No restrictions."],
                  ["proprietary", "Restricted to Equip Mozambique internal use."],
                  ["unknown", "License unclear — flag for review."],
                ].map(([r, tip]) => (
                  <label key={r} data-tip={tip}>
                    <input type="radio" name="license" checked={license === r} onChange={() => setLicense(r)} />
                    <span className="pip">{r}</span>
                  </label>
                ))}
              </div>
            </div>
          </Card>

          <Card
            title="3 · Transcript"
            icon="file"
            subtitle={<span className="text-xs text-muted">optional</span>}
            actions={<Button size="sm" variant="ghost" onClick={() => setShowTranscript(s => !s)}>{showTranscript ? "Hide" : "Add transcript"}</Button>}
          >
            {!showTranscript ? (
              <div className="text-sm text-muted">Paste a transcript inline, or attach a .txt / .srt / .vtt sidecar with your audio.</div>
            ) : (
              <textarea
                className="textarea"
                value={transcript}
                onChange={e => setTranscript(e.target.value)}
                placeholder="Paste transcript here…"
                style={{ minHeight: 140, fontFamily: "var(--font-serif)" }}
              />
            )}
          </Card>

          {uploading ? (
            <Card title="Uploading…" icon="upload_cloud" subtitle={`${Math.round(progress)}%`}>
              <div className="progress"><div className="bar" style={{ width: progress + "%" }} /></div>
              <div className="text-xs text-muted mt-2">
                {progress < 50 ? "Hashing and uploading…" : progress < 90 ? "Computing checksum…" : "Saving metadata…"}
              </div>
            </Card>
          ) : (
            <div className="row gap-2" style={{ justifyContent: "flex-end" }}>
              <Button variant="ghost" onClick={() => { setFile(null); setSpeaker(""); setDialect(""); }}>Reset</Button>
              <Button variant="primary" iconLeft="upload_cloud" disabled={!canSubmit} onClick={submit}>
                Upload to {langObj.name} corpus
              </Button>
            </div>
          )}
        </div>

        <div className="col gap-4">
          <Card title="This session" icon="clock" subtitle={`${recent.length} of 5`}>
            {recent.length === 0 ? (
              <EmptyState icon="inbox" title="Nothing uploaded yet" body="Successful uploads from this session will show here." />
            ) : (
              <div className="col gap-2">
                {recent.map(r => (
                  <div key={r.id} style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 10, alignItems: "center", padding: "10px", border: "1px solid var(--border)", borderRadius: "var(--r)" }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.filename}</div>
                      <div className="text-xs text-muted">
                        <span className="mono" style={{ fontFamily: "var(--font-mono)" }}>{r.id}</span> · {r.register} · {r.dialect}
                      </div>
                    </div>
                    <Chip mono outline>{r.speaker}</Chip>
                    <IconBtn icon="trash" label="Remove" onClick={() => setRecent(rr => rr.filter(x => x.id !== r.id))} />
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Tips" icon="info">
            <ul style={{ paddingLeft: 16, margin: 0, fontSize: 13, lineHeight: 1.7 }}>
              <li>Use the same Speaker ID across sessions to enable speaker-level analysis.</li>
              <li>Keep audio at <strong>16 kHz mono WAV</strong> where possible — it skips a resampling step.</li>
              <li>Sidecar transcripts with timestamps (<code className="mono">.srt</code>/<code className="mono">.vtt</code>) enable forced alignment.</li>
              <li>If the licence is unclear, mark <Chip outline>unknown</Chip> and the linguistics team will follow up.</li>
            </ul>
          </Card>
        </div>
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

Object.assign(window, { PageResources, PageUpload, CoverageBadge, FilesetStatus });
