/* global React, Icon, Button, IconBtn, Chip, LangPicker, CovDots, Segmented, ThemeToggle */
const { useState, useEffect } = React;

function Shell({ lang, setLang, page, setPage, target, setTarget, theme, setTheme, children }) {
  const langObj = window.getLang(lang);

  return (
    <div className="app" data-screen-label={`Page · ${page}`}>
      <header className="top-bar" role="banner">
        <div className="top-bar-inner">
          <div className="brand">
            <div className="brand-mark" aria-hidden="true">L</div>
            <div>
              Language Server
            </div>
            <div className="brand-sub desktop-only">Equip Mozambique</div>
          </div>

          <div className="spacer" />

          <LangPicker value={lang} onChange={setLang} />

          <Segmented
            value={target}
            onChange={setTarget}
            ariaLabel="Translation target language"
            options={[
              { value: "en", label: "EN" },
              { value: "pt", label: "PT" },
            ]}
          />

          <ThemeToggle theme={theme} setTheme={setTheme} />

          <IconBtn icon="user" label="Signed in as field@equipmoz.org" />
        </div>

        <window.CoverageBanner lang={langObj} target={target.toUpperCase()} />

        <nav className="tab-bar desktop-only" aria-label="Sections">
          <div className="tab-bar-inner">
            {window.PAGES.map(p => (
              <button
                key={p.id}
                type="button"
                className="tab-btn"
                aria-current={page === p.id ? "page" : undefined}
                onClick={() => setPage(p.id)}
                data-screen-label={p.label}
              >
                <Icon name={pageIcon(p.id)} />
                {p.label}
                {p.devOnly && <span className="tab-count">dev</span>}
              </button>
            ))}
          </div>
        </nav>
      </header>

      <main>
        {children}
      </main>

      <nav className="bottom-nav mobile-only" aria-label="Sections">
        {window.PAGES.filter(p => !p.devOnly).map(p => (
          <button
            key={p.id}
            type="button"
            aria-current={page === p.id ? "page" : undefined}
            onClick={() => setPage(p.id)}
          >
            <Icon name={pageIcon(p.id)} size={20} />
            <span>{p.short}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

function pageIcon(id) {
  switch (id) {
    case "live": return "mic";
    case "file": return "file_audio";
    case "tts": return "speaker";
    case "resources": return "book";
    case "upload": return "upload_cloud";
    case "inventory": return "layers";
    default: return "globe";
  }
}

window.Shell = Shell;
window.pageIcon = pageIcon;
