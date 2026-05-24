/* global React, ReactDOM,
   Shell, PageLiveTranscribe, PageTranscribeFile, PageTTS, PageResources, PageUpload, PageInventory,
   useTweaks, TweaksPanel, TweakSection, TweakColor */

const { useState, useEffect } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#0f766e"
}/*EDITMODE-END*/;

// Curated accent options
const ACCENT_OPTIONS = ["#0f766e", "#1e40af", "#9a3412", "#4f46e5", "#111827"];

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [lang, setLang]     = useState("sna");
  const [page, setPage]     = useState("live");
  const [target, setTarget] = useState("en");
  const [theme, setTheme]   = useState(() => {
    return localStorage.getItem("ls-theme") || "light";
  });

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("ls-theme", theme);
  }, [theme]);

  // Apply accent
  useEffect(() => {
    document.documentElement.style.setProperty("--accent", t.accent);
    // Derive a hover (darker) variant for solid backgrounds. Quick mix to black 10%.
    const hover = mix(t.accent, "#000000", 0.14);
    document.documentElement.style.setProperty("--accent-hover", hover);

    // Soft / fg variants in light vs dark mode
    if (theme === "dark") {
      document.documentElement.style.setProperty("--accent-soft", mix(t.accent, "#0e0d0b", 0.78));
      document.documentElement.style.setProperty("--accent-soft-border", mix(t.accent, "#0e0d0b", 0.55));
      document.documentElement.style.setProperty("--accent-fg", mix(t.accent, "#ffffff", 0.4));
    } else {
      document.documentElement.style.setProperty("--accent-soft", mix(t.accent, "#ffffff", 0.86));
      document.documentElement.style.setProperty("--accent-soft-border", mix(t.accent, "#ffffff", 0.7));
      document.documentElement.style.setProperty("--accent-fg", mix(t.accent, "#000000", 0.3));
    }
  }, [t.accent, theme]);

  // Keyboard: Cmd/Ctrl+K (focus picker is implicit via picker), Space toggles record on Live page
  // implemented inside Live page already with its own button focus.

  const props = { lang, setLang, target, setTarget, theme, setTheme, toast: null };

  return (
    <>
      <Shell {...props} page={page} setPage={setPage}>
        {page === "live"      && <PageLiveTranscribe {...props} />}
        {page === "file"      && <PageTranscribeFile {...props} />}
        {page === "tts"       && <PageTTS            {...props} />}
        {page === "resources" && <PageResources      {...props} />}
        {page === "upload"    && <PageUpload         {...props} />}
        {page === "inventory" && <PageInventory      {...props} />}
      </Shell>

      <TweaksPanel title="Tweaks">
        <TweakSection label="Accent color" />
        <TweakColor
          label="Accent"
          value={t.accent}
          options={ACCENT_OPTIONS}
          onChange={(v) => setTweak("accent", v)}
        />
        <div style={{ fontSize: 11, color: "var(--muted)", padding: "4px 12px 12px", lineHeight: 1.5 }}>
          Used for primary buttons, focus rings, the record button, active nav, and accents in coverage banners.
          Theme (light/dark) is controlled from the top bar.
        </div>
      </TweaksPanel>
    </>
  );
}

/* Mix two hex colors. amt = 0 → c1, amt = 1 → c2 */
function mix(c1, c2, amt) {
  const a = hexToRgb(c1), b = hexToRgb(c2);
  const r = Math.round(a.r + (b.r - a.r) * amt);
  const g = Math.round(a.g + (b.g - a.g) * amt);
  const bl = Math.round(a.b + (b.b - a.b) * amt);
  return `rgb(${r}, ${g}, ${bl})`;
}
function hexToRgb(h) {
  const s = h.replace("#", "");
  return {
    r: parseInt(s.slice(0, 2), 16),
    g: parseInt(s.slice(2, 4), 16),
    b: parseInt(s.slice(4, 6), 16),
  };
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
