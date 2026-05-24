/* global React, Icon, Button, IconBtn, Chip, Card, AudioPlayer, DropZone, EmptyState, ErrorState, Skel, MD, StatusPill, CovDots, Segmented, LangPicker, VU, CoverageBanner, CoverageBadge, FilesetStatus */
const { useState } = React;

function PageInventory({ lang, setLang, target, setTarget }) {
  const [tab, setTab] = useState("foundations");

  return (
    <div className="page" data-screen-label="06 Component inventory">
      <div className="page-header">
        <div className="titles">
          <h1>Component inventory</h1>
          <div className="sub">Every reusable widget in every state. The kit the rest of the app is built from.</div>
        </div>
        <Segmented
          value={tab}
          onChange={setTab}
          ariaLabel="Inventory sections"
          options={[
            { value: "foundations", label: "Foundations" },
            { value: "atoms",       label: "Atoms" },
            { value: "modules",     label: "Modules" },
            { value: "states",      label: "States" },
          ]}
        />
      </div>

      {tab === "foundations" && <Foundations />}
      {tab === "atoms"       && <Atoms lang={lang} />}
      {tab === "modules"     && <Modules lang={lang} setLang={setLang} target={target} setTarget={setTarget} />}
      {tab === "states"      && <States />}
    </div>
  );
}

/* ============================================================
   FOUNDATIONS — color, type, spacing, radii, shadows
   ============================================================ */
function Foundations() {
  return (
    <>
      <div className="inv-section">
        <h2>Color · neutrals</h2>
        <div className="inv-grid">
          <Swatch name="bg"             token="--bg" />
          <Swatch name="bg-tint"        token="--bg-tint" />
          <Swatch name="surface"        token="--surface" />
          <Swatch name="surface-2"      token="--surface-2" />
          <Swatch name="surface-3"      token="--surface-3" />
          <Swatch name="border"         token="--border" />
          <Swatch name="border-strong"  token="--border-strong" />
          <Swatch name="text"           token="--text" dark />
          <Swatch name="text-2"         token="--text-2" dark />
          <Swatch name="muted"          token="--muted" dark />
          <Swatch name="muted-2"        token="--muted-2" dark />
        </div>
      </div>
      <div className="inv-section">
        <h2>Color · accent &amp; status</h2>
        <div className="inv-grid">
          <Swatch name="accent"          token="--accent" dark />
          <Swatch name="accent-hover"    token="--accent-hover" dark />
          <Swatch name="accent-soft"     token="--accent-soft" />
          <Swatch name="green"           token="--green" dark />
          <Swatch name="green-soft"      token="--green-soft" />
          <Swatch name="amber"           token="--amber" dark />
          <Swatch name="amber-soft"      token="--amber-soft" />
          <Swatch name="red"             token="--red" dark />
          <Swatch name="red-soft"        token="--red-soft" />
        </div>
      </div>

      <div className="inv-section">
        <h2>Typography</h2>
        <div className="inv-grid">
          <TypeCard label="Serif · h1 / 28" fam="var(--font-serif)" sz={28}>Mhoroi, Equip Mozambique</TypeCard>
          <TypeCard label="Serif · h2 / 20" fam="var(--font-serif)" sz={20}>Sena Bible — Testamento Yatsopa</TypeCard>
          <TypeCard label="Sans · body / 14" fam="var(--font-sans)" sz={14}>Real-time speech-to-text from your microphone.</TypeCard>
          <TypeCard label="Sans · small / 12" fam="var(--font-sans)" sz={12}>last updated 12 days ago</TypeCard>
          <TypeCard label="Mono · code / 12" fam="var(--font-mono)" sz={12}>seh · ndc · sna · vmw</TypeCard>
          <TypeCard label="Mono · timestamp" fam="var(--font-mono)" sz={11}>00:04 · 01:12 · 03:47</TypeCard>
        </div>
      </div>

      <div className="inv-section">
        <h2>Radii &amp; shadows</h2>
        <div className="inv-grid">
          {["--r-xs", "--r-sm", "--r", "--r-md", "--r-lg", "--r-xl"].map(t => (
            <div key={t} className="inv-card">
              <div className="inv-card-head">
                <h4>{t}</h4>
                <span className="state-label">{t}</span>
              </div>
              <div className="inv-card-body">
                <div style={{ width: 100, height: 60, background: "var(--accent-soft)", border: "1px solid var(--accent-soft-border)", borderRadius: `var(${t})` }} />
              </div>
            </div>
          ))}
          {["--shadow-xs", "--shadow-sm", "--shadow-md", "--shadow-lg"].map(t => (
            <div key={t} className="inv-card">
              <div className="inv-card-head">
                <h4>{t}</h4>
                <span className="state-label">{t}</span>
              </div>
              <div className="inv-card-body" style={{ background: "var(--bg-tint)" }}>
                <div style={{ width: 100, height: 60, background: "var(--surface)", borderRadius: "var(--r)", boxShadow: `var(${t})` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="inv-section">
        <h2>Spacing scale</h2>
        <div className="card">
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {[4, 8, 12, 16, 20, 24, 32, 48].map(s => (
              <div key={s} className="row gap-3" style={{ alignItems: "center" }}>
                <div style={{ width: 60, fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--muted)" }}>{s}px</div>
                <div style={{ height: 16, width: s, background: "var(--accent-soft)", border: "1px solid var(--accent-soft-border)" }} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function Swatch({ name, token, dark }) {
  const ref = React.useRef(null);
  const [val, setVal] = useState("");
  React.useEffect(() => {
    if (ref.current) {
      const v = getComputedStyle(document.documentElement).getPropertyValue(token).trim();
      setVal(v);
    }
  }, [token]);
  return (
    <div className="inv-card" ref={ref}>
      <div className="inv-card-head">
        <h4>{name}</h4>
        <span className="state-label">{val}</span>
      </div>
      <div className="inv-card-body" style={{ background: `var(${token})`, color: dark ? "white" : "var(--text)", minHeight: 80 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, opacity: dark ? 0.85 : 0.5 }}>{token}</span>
      </div>
    </div>
  );
}

function TypeCard({ label, fam, sz, children }) {
  return (
    <div className="inv-card">
      <div className="inv-card-head"><h4>{label}</h4></div>
      <div className="inv-card-body" style={{ background: "var(--surface)", padding: "24px 18px", justifyContent: "flex-start" }}>
        <div style={{ fontFamily: fam, fontSize: sz, lineHeight: 1.4, color: "var(--text)" }}>{children}</div>
      </div>
    </div>
  );
}

/* ============================================================
   ATOMS — buttons, chips, inputs, etc.
   ============================================================ */
function Atoms({ lang }) {
  const [seg, setSeg] = useState("en");
  const [reg, setReg] = useState("read");

  return (
    <>
      <div className="inv-section">
        <h2>Buttons</h2>
        <div className="inv-grid">
          <InvCard label="Primary · default">
            <Button variant="primary">Save session</Button>
          </InvCard>
          <InvCard label="Primary · hover" hoverHint>
            <Button variant="primary" iconLeft="upload_cloud">Upload</Button>
          </InvCard>
          <InvCard label="Primary · loading">
            <Button variant="primary" loading>Synthesising…</Button>
          </InvCard>
          <InvCard label="Primary · disabled">
            <Button variant="primary" disabled>Save session</Button>
          </InvCard>
          <InvCard label="Default">
            <Button iconLeft="refresh">Retry</Button>
          </InvCard>
          <InvCard label="Ghost">
            <Button variant="ghost" iconLeft="trash">Clear</Button>
          </InvCard>
          <InvCard label="Danger">
            <Button variant="danger" iconLeft="trash">Delete file</Button>
          </InvCard>
          <InvCard label="Small">
            <Button size="sm" iconLeft="download">.txt</Button>
          </InvCard>
          <InvCard label="Large">
            <Button size="lg" variant="primary" iconLeft="speaker">Speak</Button>
          </InvCard>
          <InvCard label="Icon-only (with tooltip)">
            <IconBtn icon="copy" label="Copy" />
            <IconBtn icon="download" label="Download" />
            <IconBtn icon="trash" label="Delete" />
            <IconBtn icon="more" label="More" />
          </InvCard>
        </div>
      </div>

      <div className="inv-section">
        <h2>Chips &amp; pills</h2>
        <div className="inv-grid">
          <InvCard label="Default chips">
            <Chip>read</Chip><Chip>conversational</Chip><Chip>news</Chip>
          </InvCard>
          <InvCard label="Outline + mono (ISO codes)">
            <Chip outline mono>sna</Chip><Chip outline mono>ndc</Chip><Chip outline mono>seh</Chip>
          </InvCard>
          <InvCard label="Status chips">
            <Chip tone="green">downloaded</Chip>
            <Chip tone="amber">partial</Chip>
            <Chip tone="red">missing</Chip>
            <Chip tone="accent">NT</Chip>
          </InvCard>
          <InvCard label="Removable">
            <Chip onRemove={() => {}}>Karanga</Chip>
            <Chip outline onRemove={() => {}}>CC-BY</Chip>
          </InvCard>
          <InvCard label="Status pills">
            <StatusPill status="native" />
            <StatusPill status="proxy" />
            <StatusPill status="missing" />
          </InvCard>
          <InvCard label="Coverage dots">
            <CovDots lang={{ name: "Shona",  iso: "sna", mmsAsr: true,  mmsTts: true,  whisper: true }} />
            <CovDots lang={{ name: "Sena",   iso: "seh", mmsAsr: true,  mmsTts: true,  whisper: false }} />
            <CovDots lang={{ name: "Ndau",   iso: "ndc", mmsAsr: false, mmsTts: false, whisper: false, proxy: "sna" }} />
            <CovDots lang={{ name: "Nambya", iso: "nmq", mmsAsr: false, mmsTts: false, whisper: false }} />
          </InvCard>
        </div>
      </div>

      <div className="inv-section">
        <h2>Inputs</h2>
        <div className="inv-grid">
          <InvCard label="Text · default" tall>
            <div style={{ width: "100%" }}>
              <label className="label" htmlFor="i1">Speaker ID</label>
              <input id="i1" className="input" placeholder="e.g. MM-014" />
            </div>
          </InvCard>
          <InvCard label="Text · with value" tall>
            <div style={{ width: "100%" }}>
              <label className="label" htmlFor="i2">Dialect</label>
              <input id="i2" className="input" defaultValue="Karanga" />
            </div>
          </InvCard>
          <InvCard label="Text · focus" tall>
            <div style={{ width: "100%" }}>
              <label className="label">Search</label>
              <input className="input" defaultValue="Ndau" style={{ borderColor: "var(--accent)", boxShadow: "0 0 0 3px color-mix(in oklab, var(--accent) 18%, transparent)" }} />
            </div>
          </InvCard>
          <InvCard label="Text · error" tall>
            <div style={{ width: "100%" }}>
              <label className="label">Speaker ID</label>
              <input className="input" aria-invalid="true" defaultValue="" />
              <div className="err">Speaker ID is required.</div>
            </div>
          </InvCard>
          <InvCard label="Textarea" tall>
            <textarea className="textarea" defaultValue="Mhoroi, ndinotenda kuti mauya kuno nhasi." style={{ minHeight: 90 }} />
          </InvCard>
          <InvCard label="Select" tall>
            <div style={{ width: "100%" }}>
              <label className="label">Voice</label>
              <select className="select"><option>Default MMS voice</option></select>
            </div>
          </InvCard>
          <InvCard label="Radio chips" tall>
            <div style={{ width: "100%" }}>
              <label className="label">Register</label>
              <div className="radio-chips">
                {["read","conversational","news","religious"].map(r => (
                  <label key={r}>
                    <input type="radio" name="reg-demo" checked={reg === r} onChange={() => setReg(r)} />
                    <span className="pip">{r}</span>
                  </label>
                ))}
              </div>
            </div>
          </InvCard>
          <InvCard label="Segmented">
            <Segmented
              value={seg}
              onChange={setSeg}
              ariaLabel="Demo"
              options={[{ value: "en", label: "EN" }, { value: "pt", label: "PT" }]}
            />
          </InvCard>
        </div>
      </div>

      <div className="inv-section">
        <h2>Feedback</h2>
        <div className="inv-grid">
          <InvCard label="Progress · determinate">
            <div style={{ width: "100%" }}><div className="progress"><div className="bar" style={{ width: "60%" }} /></div></div>
          </InvCard>
          <InvCard label="Progress · indeterminate">
            <div style={{ width: "100%" }}><div className="progress indet"><div className="bar" /></div></div>
          </InvCard>
          <InvCard label="Spinner">
            <span className="spin" style={{ color: "var(--accent)" }} />
          </InvCard>
          <InvCard label="VU meter · idle">
            <VU active={false} />
          </InvCard>
          <InvCard label="VU meter · live">
            <VU active />
          </InvCard>
          <InvCard label="Skeleton">
            <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 6 }}>
              <Skel w="90%" /><Skel w="78%" /><Skel w="50%" />
            </div>
          </InvCard>
        </div>
      </div>

      <div className="inv-section">
        <h2>Keyboard hints</h2>
        <div className="inv-grid">
          <InvCard label="kbd"><kbd>⌘</kbd> <kbd>K</kbd> <kbd>↵</kbd> <kbd>esc</kbd></InvCard>
          <InvCard label="In context">
            <span className="text-sm">Press <kbd>Space</kbd> to toggle recording, <kbd>esc</kbd> to close.</span>
          </InvCard>
        </div>
      </div>
    </>
  );
}

/* ============================================================
   MODULES — larger composed widgets
   ============================================================ */
function Modules({ lang, setLang, target, setTarget }) {
  const langObj = window.getLang(lang);
  return (
    <>
      <div className="inv-section">
        <h2>Language picker</h2>
        <div className="card">
          <div className="card-body" style={{ background: "var(--bg-tint)", display: "flex", justifyContent: "center", padding: 36 }}>
            <LangPicker value={lang} onChange={setLang} />
          </div>
        </div>
      </div>

      <div className="inv-section">
        <h2>Coverage banner — all variants</h2>
        <div className="col gap-3">
          <CoverageBanner lang={window.getLang("ndc")} target="EN" />
          <CoverageBanner lang={window.getLang("nmq")} target="EN" />
          <CoverageBanner lang={window.getLang("toi")} target="EN" />
          <div className="text-xs text-muted">Hidden entirely when all four models are green (e.g. Shona).</div>
        </div>
      </div>

      <div className="inv-section">
        <h2>Audio player</h2>
        <div className="card">
          <div className="card-body" style={{ background: "var(--bg-tint)" }}>
            <AudioPlayer initialDuration={12.4} />
          </div>
        </div>
      </div>

      <div className="inv-section">
        <h2>Drop zone</h2>
        <div className="inv-grid">
          <InvCard label="Idle" tall stretch>
            <DropZone onFile={() => {}} accept="audio/*" maxMB={200} />
          </InvCard>
          <InvCard label="With file" tall stretch>
            <DropZone
              file={{ name: "harare_radio_2024-08-12.wav", size: "8.4 MB", duration: "12:04", type: "audio/wav" }}
              onClear={() => {}}
            />
          </InvCard>
        </div>
      </div>

      <div className="inv-section">
        <h2>Card</h2>
        <Card
          title="Model coverage"
          icon="layers"
          subtitle={<StatusPill status="native" />}
          actions={<IconBtn icon="more" label="More" />}
        >
          <div className="row gap-3" style={{ flexWrap: "wrap" }}>
            <CoverageBadge label="Whisper" on />
            <CoverageBadge label="MMS-ASR" on />
            <CoverageBadge label="MMS-TTS" on />
            <CoverageBadge label="NLLB" on />
          </div>
        </Card>
      </div>

      <div className="inv-section">
        <h2>Record button — states</h2>
        <div className="inv-grid">
          <InvCard label="Idle" tall>
            <button className="record-btn" aria-label="Start"><Icon name="mic" size={32} /></button>
          </InvCard>
          <InvCard label="Recording (pulsing)" tall>
            <button className="record-btn recording" aria-label="Stop"><Icon name="stop" size={32} /></button>
          </InvCard>
          <InvCard label="Disabled" tall>
            <button className="record-btn" disabled style={{ opacity: 0.4, cursor: "not-allowed", boxShadow: "none" }} aria-label="Unavailable"><Icon name="mic" size={32} /></button>
          </InvCard>
        </div>
      </div>

      <div className="inv-section">
        <h2>Tables</h2>
        <div className="card" style={{ overflow: "hidden" }}>
          <table className="tbl">
            <thead>
              <tr><th>Filename</th><th>Speaker</th><th>Register</th><th>License</th><th className="num">Duration</th></tr>
            </thead>
            <tbody>
              {(window.MOCK_UPLOADED_CORPUS.sna || []).slice(0, 3).map(c => (
                <tr key={c.id}>
                  <td><span className="mono" style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{c.filename}</span></td>
                  <td><Chip mono outline>{c.speaker}</Chip></td>
                  <td><Chip>{c.register}</Chip></td>
                  <td><Chip outline>{c.license}</Chip></td>
                  <td className="num">{c.duration}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="inv-section">
        <h2>Tab nav</h2>
        <div className="card" style={{ background: "var(--surface)" }}>
          <div className="tab-bar" style={{ position: "static", borderRadius: "var(--r-lg)" }}>
            <div className="tab-bar-inner">
              <button className="tab-btn" aria-current="page"><Icon name="mic" /> Live Transcribe</button>
              <button className="tab-btn"><Icon name="file_audio" /> Transcribe File</button>
              <button className="tab-btn"><Icon name="speaker" /> TTS</button>
              <button className="tab-btn"><Icon name="book" /> Resources</button>
              <button className="tab-btn"><Icon name="upload_cloud" /> Upload</button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

/* ============================================================
   STATES — empty / loading / error
   ============================================================ */
function States() {
  return (
    <>
      <div className="inv-section">
        <h2>Empty states</h2>
        <div className="inv-grid">
          <div className="card"><EmptyState icon="inbox"    title="No uploads yet" body="Add training data in the Upload tab." action={<Button size="sm" iconLeft="upload_cloud">Go to Upload</Button>} /></div>
          <div className="card"><EmptyState icon="hash"     title="No catalog entries" body="No DBS records found for this language." /></div>
          <div className="card"><EmptyState icon="speaker"  title="No audio Bibles" body="Try the proxy language." /></div>
          <div className="card"><EmptyState icon="mic"      title="Nothing yet" body="Press the mic to start." /></div>
          <div className="card"><EmptyState icon="filter"   title="No matches" body="Adjust your filters." /></div>
          <div className="card"><EmptyState icon="globe"    title="No translation" body="No NLLB coverage for this language." /></div>
        </div>
      </div>

      <div className="inv-section">
        <h2>Loading skeletons</h2>
        <div className="inv-grid">
          <div className="card">
            <div className="card-body">
              <Skel w="40%" h={16} /><div style={{ height: 10 }} />
              <Skel w="100%" /><div style={{ height: 6 }} />
              <Skel w="92%" /><div style={{ height: 6 }} />
              <Skel w="78%" />
            </div>
          </div>
          <div className="card">
            <div className="card-body">
              <div className="row gap-3">
                <Skel w={40} h={40} style={{ borderRadius: "50%" }} />
                <div style={{ flex: 1 }}>
                  <Skel w="70%" h={14} /><div style={{ height: 6 }} />
                  <Skel w="40%" h={10} />
                </div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="card-body">
              <div className="progress indet"><div className="bar" /></div>
              <div className="text-xs text-muted mt-2 row gap-2"><span className="spin" /> Running ASR…</div>
            </div>
          </div>
        </div>
      </div>

      <div className="inv-section">
        <h2>Error states</h2>
        <div className="inv-grid">
          <div className="card"><ErrorState title="Mic permission denied" body="Enable microphone access in your browser to record." onRetry={() => {}} /></div>
          <div className="card"><ErrorState title="WebSocket disconnected" body="The connection to the language server was lost." onRetry={() => {}} /></div>
          <div className="card"><ErrorState title="Upload failed" body="The file could not be saved. Check your connection and try again." onRetry={() => {}} /></div>
          <div className="card"><ErrorState title="File too large" body="Audio must be smaller than 200 MB. Yours is 412 MB." /></div>
          <div className="card"><ErrorState title="Unsupported format" body="Audio must be wav, mp3, m4a, ogg or flac." /></div>
          <div className="card"><ErrorState title="Duplicate file" body="A file with this audio checksum already exists." /></div>
        </div>
      </div>

      <div className="inv-section">
        <h2>Toast / notice variants</h2>
        <div className="col gap-2">
          <div className="card" style={{ background: "var(--green-soft)", borderColor: "var(--green-border)" }}>
            <div className="card-body row gap-3" style={{ alignItems: "center" }}>
              <Icon name="check_circle" style={{ color: "var(--green)" }} />
              <div style={{ flex: 1, color: "var(--green)" }}><strong>Upload complete.</strong> <span style={{ color: "var(--text-2)" }}>Assigned UUID <Chip mono outline>a1f2-c3d4</Chip>.</span></div>
              <Button size="sm" iconLeft="book">View</Button>
            </div>
          </div>
          <div className="card" style={{ background: "var(--amber-soft)", borderColor: "var(--amber-border)" }}>
            <div className="card-body row gap-3" style={{ alignItems: "center" }}>
              <Icon name="warn" style={{ color: "var(--amber)" }} />
              <div style={{ flex: 1, color: "var(--amber)" }}><strong>No TTS for Ndau.</strong> <span style={{ color: "var(--text-2)" }}>Try Shona (sna) — closest available voice.</span></div>
              <Button size="sm">Switch</Button>
            </div>
          </div>
          <div className="card" style={{ background: "var(--red-soft)", borderColor: "var(--red-border)" }}>
            <div className="card-body row gap-3" style={{ alignItems: "center" }}>
              <Icon name="alert" style={{ color: "var(--red)" }} />
              <div style={{ flex: 1, color: "var(--red)" }}><strong>Duplicate upload.</strong> <span style={{ color: "var(--text-2)" }}>Matches existing entry a1f2-c3d4.</span></div>
              <Button size="sm" iconLeft="link">Open existing</Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

/* ---------- helpers ---------- */
function InvCard({ label, children, tall, stretch, hoverHint }) {
  return (
    <div className="inv-card">
      <div className="inv-card-head"><h4>{label}</h4>{hoverHint && <span className="state-label">hover</span>}</div>
      <div className="inv-card-body" style={tall ? { minHeight: 140, alignItems: stretch ? "stretch" : "center" } : null}>
        {children}
      </div>
    </div>
  );
}

window.PageInventory = PageInventory;
