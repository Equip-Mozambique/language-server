/* global React, Icon */
// Reusable component atoms. Exports onto window.

const { useState, useEffect, useRef, useMemo, useCallback } = React;

/* ---------- Button ---------- */
function Button({ variant = "default", size = "md", iconLeft, iconRight, loading, children, ...rest }) {
  const cls = ["btn"];
  if (variant === "primary") cls.push("primary");
  if (variant === "danger") cls.push("danger");
  if (variant === "ghost") cls.push("ghost");
  if (size === "sm") cls.push("sm");
  if (size === "lg") cls.push("lg");
  if (!children && iconLeft) cls.push("icon-only");
  return (
    <button className={cls.join(" ")} {...rest}>
      {loading ? <span className="spin" /> : iconLeft && <Icon name={iconLeft} />}
      {children}
      {iconRight && <Icon name={iconRight} />}
    </button>
  );
}

/* ---------- IconBtn (always has aria-label) ---------- */
function IconBtn({ icon, label, ...rest }) {
  return (
    <button
      type="button"
      className="icon-btn"
      aria-label={label}
      data-tip={label}
      {...rest}
    >
      <Icon name={icon} />
    </button>
  );
}

/* ---------- Chip ---------- */
function Chip({ tone, mono, outline, lg, onRemove, children, ...rest }) {
  const cls = ["chip"];
  if (tone) cls.push(tone);
  if (mono) cls.push("mono");
  if (outline) cls.push("outline");
  if (lg) cls.push("lg");
  return (
    <span className={cls.join(" ")} {...rest}>
      {children}
      {onRemove && (
        <button className="chip-x" onClick={onRemove} aria-label="Remove">
          <Icon name="x" size={10} />
        </button>
      )}
    </span>
  );
}

/* ---------- Coverage dots ---------- */
function CovDots({ lang }) {
  return (
    <span className="cov-dots" aria-label={`Coverage for ${lang.name}: ASR ${lang.mmsAsr ? 'yes' : 'no'}, TTS ${lang.mmsTts ? 'yes' : 'no'}, Whisper ${lang.whisper ? 'yes' : 'no'}`}>
      <span className={"d " + (lang.mmsAsr ? "on" : lang.proxy ? "proxy" : "")} data-tip={`MMS-ASR: ${lang.mmsAsr ? 'native' : (lang.proxy ? 'via proxy' : 'missing')}`} />
      <span className={"d " + (lang.mmsTts ? "on" : lang.proxy ? "proxy" : "")} data-tip={`MMS-TTS: ${lang.mmsTts ? 'native' : (lang.proxy ? 'via proxy' : 'missing')}`} />
      <span className={"d " + (lang.whisper ? "on" : "")} data-tip={`Whisper: ${lang.whisper ? 'yes' : 'no'}`} />
    </span>
  );
}

/* ---------- Status pill ---------- */
function StatusPill({ status }) {
  const map = {
    native:  { tone: "green",  label: "Native",  dot: "green" },
    proxy:   { tone: "amber",  label: "Proxy",   dot: "amber" },
    missing: { tone: "red",    label: "Missing", dot: "red" },
  };
  const m = map[status] || map.missing;
  return (
    <span className="pill">
      <span className={"dot " + m.dot} />
      {m.label}
    </span>
  );
}

/* ---------- Segmented ---------- */
function Segmented({ value, options, onChange, ariaLabel }) {
  return (
    <div className="seg" role="group" aria-label={ariaLabel}>
      {options.map(o => (
        <button
          key={o.value}
          type="button"
          aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
        >
          {o.icon && <Icon name={o.icon} />}
          {o.label}
        </button>
      ))}
    </div>
  );
}

/* ---------- Language picker ---------- */
function LangPicker({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const ref = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", close);
    setTimeout(() => inputRef.current?.focus(), 30);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const list = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return window.LANGUAGES;
    return window.LANGUAGES.filter(l =>
      l.name.toLowerCase().includes(s) || l.iso.includes(s) || (l.country || "").toLowerCase().includes(s)
    );
  }, [q]);

  const current = window.getLang(value) || window.LANGUAGES[0];

  const pick = (lang) => { onChange(lang.iso); setOpen(false); setQ(""); };

  const onKey = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActive(a => Math.min(a + 1, list.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive(a => Math.max(a - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); list[active] && pick(list[active]); }
    else if (e.key === "Escape") { setOpen(false); }
  };

  return (
    <div className="lang-picker" ref={ref}>
      <button
        type="button"
        className="lang-picker-trigger"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label={`Selected language: ${current.name}. Click to change.`}
      >
        <Icon name="globe" />
        <span className="name">{current.name}</span>
        <span className="iso">{current.iso}</span>
        <Icon name="chev_down" size={12} />
      </button>
      {open && (
        <div className="lang-picker-pop" role="listbox" aria-label="Languages">
          <div className="lang-picker-search">
            <Icon name="search" />
            <input
              ref={inputRef}
              value={q}
              onChange={e => { setQ(e.target.value); setActive(0); }}
              onKeyDown={onKey}
              placeholder="Search by name, ISO or country…"
              aria-label="Search languages"
            />
            <kbd>esc</kbd>
          </div>
          <div className="lang-picker-list">
            {list.length === 0 ? (
              <div className="state" style={{ padding: "18px" }}>
                <p>No matches for "{q}".</p>
              </div>
            ) : list.map((l, i) => (
              <div
                key={l.iso}
                className="lang-row"
                role="option"
                aria-selected={i === active || l.iso === value}
                onMouseEnter={() => setActive(i)}
                onClick={() => pick(l)}
              >
                <div className="lr-name">
                  <strong>{l.name}</strong>
                  <span className="meta">
                    <Chip tone="" outline mono>{l.country}</Chip>
                    {l.proxy && <span style={{ color: "var(--muted)" }}>→ proxy {l.proxy}</span>}
                    {l.status === "missing" && <span style={{ color: "var(--red)" }}>missing</span>}
                  </span>
                </div>
                <CovDots lang={l} />
                <span className="lr-iso">{l.iso}</span>
              </div>
            ))}
          </div>
          <div className="lang-picker-foot">
            <span>{list.length} language{list.length === 1 ? "" : "s"}</span>
            <span><kbd>↑</kbd> <kbd>↓</kbd> to move, <kbd>↵</kbd> to select</span>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Card ---------- */
function Card({ title, subtitle, actions, children, dense, collapsible, defaultOpen = true, icon }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className={"card" + (collapsible ? (" collapsible " + (open ? "open" : "")) : "")}>
      <header
        className={"card-head" + (collapsible ? " collapsible-head" : "")}
        onClick={collapsible ? () => setOpen(o => !o) : undefined}
        role={collapsible ? "button" : undefined}
        aria-expanded={collapsible ? open : undefined}
      >
        <h2>
          {collapsible && <Icon name="chev_right" className="chev" />}
          {icon && <Icon name={icon} />}
          {title}
        </h2>
        <div className="row gap-2">
          {subtitle && <span className="meta">{subtitle}</span>}
          {actions}
        </div>
      </header>
      {(!collapsible || open) && (
        <div className={"card-body" + (dense ? " dense" : "")}>{children}</div>
      )}
    </section>
  );
}

/* ---------- Audio player (visual only) ---------- */
function AudioPlayer({ src, label = "Audio", initialDuration = 12.4 }) {
  const [playing, setPlaying] = useState(false);
  const [t, setT] = useState(0);
  const dur = initialDuration;
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setT(v => {
        if (v >= dur) { setPlaying(false); return 0; }
        return v + 0.1;
      });
    }, 100);
    return () => clearInterval(id);
  }, [playing, dur]);
  const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  const pct = Math.min(100, (t / dur) * 100);
  return (
    <div className="aplayer" aria-label={label}>
      <button className="play-btn" onClick={() => setPlaying(p => !p)} aria-label={playing ? "Pause" : "Play"}>
        <Icon name={playing ? "pause" : "play"} size={14} />
      </button>
      <div
        className="scrub"
        role="slider"
        aria-label="Seek"
        aria-valuemin={0}
        aria-valuemax={dur}
        aria-valuenow={t}
        onClick={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          const p = (e.clientX - r.left) / r.width;
          setT(Math.max(0, Math.min(dur, dur * p)));
        }}
      >
        <div className="fill" style={{ width: pct + "%" }} />
        <div className="head" style={{ left: pct + "%" }} />
      </div>
      <span className="time">{fmt(t)} / {fmt(dur)}</span>
      <IconBtn icon="download" label="Download" />
    </div>
  );
}

/* ---------- Drop zone ---------- */
function DropZone({ accept, maxMB, onFile, file, onClear, label, sub }) {
  const [over, setOver] = useState(false);
  const inp = useRef(null);

  const handleFile = (f) => { if (f) onFile(f); };
  const onDrop = (e) => {
    e.preventDefault(); setOver(false);
    handleFile(e.dataTransfer.files?.[0]);
  };
  const onDrag = (e) => { e.preventDefault(); setOver(true); };

  if (file) {
    return (
      <div className="card" style={{ display: "flex", alignItems: "center", padding: "14px 16px", gap: "12px" }}>
        <div style={{ width: 40, height: 40, borderRadius: 8, background: "var(--accent-soft)", color: "var(--accent-fg)", display: "grid", placeItems: "center", flexShrink: 0 }}>
          <Icon name="file_audio" />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 500, fontSize: 13.5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</div>
          <div className="text-xs text-muted">
            {file.size} · {file.duration || "—"} · {file.type || "audio"}
          </div>
        </div>
        <IconBtn icon="x" label="Remove file" onClick={onClear} />
      </div>
    );
  }

  return (
    <label
      className={"dropzone" + (over ? " over" : "")}
      onDragOver={onDrag}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      onClick={(e) => { e.preventDefault(); inp.current?.click(); }}
    >
      <div className="dz-icon"><Icon name="upload_cloud" size={20} /></div>
      <h3>{label || "Drag and drop, or "}<span style={{ color: "var(--accent-fg)" }} className="mobile-only">tap to choose</span><span style={{ color: "var(--accent-fg)" }} className="desktop-only">click to browse</span></h3>
      <p>{sub || `Accepts ${accept || "audio/*"}. Up to ${maxMB || 200} MB.`}</p>
      <input
        ref={inp}
        type="file"
        accept={accept || "audio/*"}
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files?.[0])}
        aria-label="Select file to upload"
      />
    </label>
  );
}

/* ---------- VU meter ---------- */
function VU({ active }) {
  const [vals, setVals] = useState([0.3, 0.4, 0.6, 0.4, 0.3, 0.5, 0.4, 0.3, 0.6, 0.4, 0.3, 0.5]);
  useEffect(() => {
    if (!active) { setVals(v => v.map(() => 0.18)); return; }
    const id = setInterval(() => {
      setVals(v => v.map(() => 0.25 + Math.random() * 0.75));
    }, 110);
    return () => clearInterval(id);
  }, [active]);
  return (
    <div className="vu" aria-hidden="true">
      {vals.map((v, i) => <div key={i} className="bar" style={{ height: (v * 100) + "%" }} />)}
    </div>
  );
}

/* ---------- Skeleton ---------- */
function Skel({ w = "100%", h = 12, style }) {
  return <span className="skel" style={{ width: w, height: h, ...style }} />;
}

/* ---------- Empty / error ---------- */
function EmptyState({ icon = "inbox", title, body, action }) {
  return (
    <div className="state">
      <div className="icon"><Icon name={icon} size={20} /></div>
      <h3>{title}</h3>
      {body && <p>{body}</p>}
      {action}
    </div>
  );
}
function ErrorState({ title, body, onRetry }) {
  return (
    <div className="state error">
      <div className="icon"><Icon name="alert" size={20} /></div>
      <h3>{title}</h3>
      {body && <p>{body}</p>}
      {onRetry && <Button size="sm" iconLeft="refresh" onClick={onRetry}>Retry</Button>}
    </div>
  );
}

/* ---------- Coverage banner ---------- */
function CoverageBanner({ lang, target }) {
  if (!lang) return null;
  const fully = lang.mmsAsr && lang.mmsTts && lang.nllb && lang.whisper;
  if (fully) return null;
  const tone =
    lang.status === "missing" ? "red"
    : lang.status === "proxy" ? "" /* amber default */
    : "";
  const parts = [];
  if (lang.status === "proxy") {
    parts.push(
      <span key="proxy">
        proxying ASR &amp; TTS to <strong>{window.getLang(lang.proxy)?.name}</strong> (<code className="mono">{lang.proxy}</code>)
      </span>
    );
  } else {
    if (!lang.mmsAsr) parts.push(<span key="asr">MMS-ASR <Icon name="x" size={11} /></span>);
    if (!lang.mmsTts) parts.push(<span key="tts">MMS-TTS <Icon name="x" size={11} /></span>);
    if (!lang.whisper) parts.push(<span key="w">Whisper <Icon name="x" size={11} /></span>);
    if (!lang.nllb)    parts.push(<span key="nllb">NLLB→{target} <Icon name="x" size={11} /></span>);
  }
  return (
    <div className={"coverage-banner " + tone} role="status" aria-live="polite">
      <div className="coverage-banner-inner">
        <Icon name="warn" />
        <strong>{lang.name}</strong>
        <span className="chip mono">{lang.iso}</span>
        <span>—</span>
        {parts.reduce((acc, p, i) => acc.concat(i > 0 ? [<span key={"s"+i} style={{opacity:0.5}}>·</span>, p] : [p]), [])}
        {lang.status === "missing" && <span style={{ marginLeft: "auto", fontSize: 12 }}>No models available. Try a related language.</span>}
      </div>
    </div>
  );
}

/* ---------- Theme toggle ---------- */
function ThemeToggle({ theme, setTheme }) {
  return (
    <IconBtn
      icon={theme === "dark" ? "sun" : "moon"}
      label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    />
  );
}

/* ---------- Tiny markdown ---------- */
// Render a subset of markdown: headings, paragraphs, lists, tables, code, blockquote, footnotes.
function MD({ source }) {
  const html = useMemo(() => mdToHtml(source || ""), [source]);
  return <div className="md" dangerouslySetInnerHTML={{ __html: html }} />;
}

function mdToHtml(src) {
  const lines = src.split("\n");
  let html = "";
  let i = 0;
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const inline = (s) => {
    let r = esc(s);
    r = r.replace(/`([^`]+)`/g, '<code>$1</code>');
    r = r.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    r = r.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    r = r.replace(/\[\^([^\]]+)\]/g, '<sup>[$1]</sup>');
    r = r.replace(/⟨([^⟩]+)⟩/g, '&lt;$1&gt;');
    return r;
  };
  while (i < lines.length) {
    const ln = lines[i];
    if (/^##\s/.test(ln)) { html += `<h2 id="${slug(ln.slice(3))}">${inline(ln.slice(3))}</h2>`; i++; continue; }
    if (/^###\s/.test(ln)) { html += `<h3 id="${slug(ln.slice(4))}">${inline(ln.slice(4))}</h3>`; i++; continue; }
    if (/^>\s/.test(ln))  { html += `<blockquote>${inline(ln.slice(2))}</blockquote>`; i++; continue; }
    if (/^---/.test(ln))   { html += `<hr/>`; i++; continue; }
    if (/^\|/.test(ln)) {
      const rows = [];
      while (i < lines.length && /^\|/.test(lines[i])) { rows.push(lines[i]); i++; }
      // First row header, second row separator (skip), rest body
      const splitRow = (r) => r.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(s => s.trim());
      const head = splitRow(rows[0]);
      const body = rows.slice(2).map(splitRow);
      html += `<table><thead><tr>${head.map(h => `<th>${inline(h)}</th>`).join("")}</tr></thead><tbody>${body.map(r => `<tr>${r.map(c => `<td>${inline(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
      continue;
    }
    if (/^[-*]\s/.test(ln)) {
      const items = [];
      while (i < lines.length && /^[-*]\s/.test(lines[i])) { items.push(lines[i].slice(2)); i++; }
      html += `<ul>${items.map(x => `<li>${inline(x)}</li>`).join("")}</ul>`;
      continue;
    }
    if (/^\d+\.\s/.test(ln)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) { items.push(lines[i].replace(/^\d+\.\s/, "")); i++; }
      html += `<ol>${items.map(x => `<li>${inline(x)}</li>`).join("")}</ol>`;
      continue;
    }
    if (ln.trim() === "") { i++; continue; }
    // paragraph (collect until blank)
    const buf = [];
    while (i < lines.length && lines[i].trim() !== "" && !/^(##|###|>|\||---|[-*]\s|\d+\.\s)/.test(lines[i])) {
      buf.push(lines[i]); i++;
    }
    html += `<p>${inline(buf.join(" "))}</p>`;
  }
  return html;
}
function slug(s) { return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }

/* ---------- Toast ---------- */
function useToast() {
  const [toast, setToast] = useState(null);
  const show = useCallback((t) => {
    setToast(t);
    setTimeout(() => setToast(null), t.duration || 3000);
  }, []);
  const view = toast && (
    <div
      role="status"
      style={{
        position: "fixed",
        bottom: 20, left: "50%", transform: "translateX(-50%)",
        background: "var(--text)", color: "var(--bg)",
        padding: "10px 14px",
        borderRadius: "var(--r)",
        boxShadow: "var(--shadow-lg)",
        fontSize: 13, zIndex: 100,
        display: "flex", alignItems: "center", gap: 8,
        maxWidth: "90vw",
      }}
    >
      {toast.icon && <Icon name={toast.icon} />}
      {toast.message}
    </div>
  );
  return { show, view };
}

Object.assign(window, {
  Button, IconBtn, Chip, CovDots, StatusPill, Segmented,
  LangPicker, Card, AudioPlayer, DropZone, VU,
  Skel, EmptyState, ErrorState, CoverageBanner, ThemeToggle, MD, useToast,
});
