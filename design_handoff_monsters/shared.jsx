// Shared components: window chrome, sidebar, icons, placeholder rune + data

const IconScan = (p) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/>
    <path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
    <path d="M3 12h18"/>
  </svg>
);
const IconFilters = (p) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M3 6h18"/><path d="M6 12h12"/><path d="M10 18h4"/>
  </svg>
);
const IconRunes = (p) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <polygon points="12,3 21,8 21,16 12,21 3,16 3,8"/>
    <path d="M12 3v18"/><path d="M3 8l18 8"/><path d="M21 8L3 16"/>
  </svg>
);
const IconMonsters = (p) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <circle cx="12" cy="12" r="9"/><circle cx="9" cy="10" r="1" fill="currentColor"/><circle cx="15" cy="10" r="1" fill="currentColor"/>
    <path d="M8 15c1.2 1.5 2.6 2 4 2s2.8-.5 4-2"/>
  </svg>
);
const IconProfile = (p) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>
  </svg>
);
const IconSettings = (p) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v.1a1.7 1.7 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>
  </svg>
);
const IconPlay = (p) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" {...p}>
    <path d="M6 4l14 8-14 8z"/>
  </svg>
);
const IconPause = (p) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" {...p}>
    <rect x="5" y="4" width="5" height="16"/><rect x="14" y="4" width="5" height="16"/>
  </svg>
);
const IconArrowUp = (p) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M12 19V5"/><path d="M5 12l7-7 7 7"/>
  </svg>
);
const IconSparkle = (p) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" {...p}>
    <path d="M12 2l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/>
  </svg>
);
const IconClock = (p) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>
  </svg>
);
const IconSearch = (p) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>
  </svg>
);
const IconKeep = (p) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M5 4h14v17l-7-4-7 4z"/>
  </svg>
);
const IconSell = (p) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M3 6h3l2 12h11l2-9H7"/>
    <circle cx="10" cy="21" r="1.2"/><circle cx="18" cy="21" r="1.2"/>
  </svg>
);

// Verdict badge: auto-decides keep vs sell from efficiency
function VerdictBadge({ efficiency, size = 'md', keepColor, sellColor, bgAlpha = '1a', borderAlpha = '33' }) {
  const keep = efficiency >= 70;
  const color = keep ? (keepColor || '#5dd39e') : (sellColor || '#e86161');
  const label = keep ? 'KEEP' : 'SELL';
  const Icon = keep ? IconKeep : IconSell;
  const sz = {
    sm: { pad: '4px 8px',   fs: 10, ic: 11, gap: 6 },
    md: { pad: '6px 10px',  fs: 11, ic: 13, gap: 6 },
    lg: { pad: '9px 16px',  fs: 13, ic: 16, gap: 8 },
    xl: { pad: '12px 20px', fs: 15, ic: 20, gap: 10 },
  }[size] || { pad: '6px 10px', fs: 11, ic: 13, gap: 6 };
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: sz.gap,
      padding: sz.pad, borderRadius: 999,
      background: color + bgAlpha, border: `1.5px solid ${color}${borderAlpha}`,
      color, fontSize: sz.fs, fontWeight: 700, letterSpacing: 1,
      fontFamily: 'JetBrains Mono',
      boxShadow: `0 0 0 0 ${color}00, 0 8px 24px -12px ${color}`,
    }}>
      <Icon width={sz.ic} height={sz.ic}/>
      {label}
    </div>
  );
}

// ── Windows-style title bar ──────────────────────────────────────
function WinTitleBar({ bg, fg, title, accent, borderColor, subdued }) {
  return (
    <div style={{
      height: 36, display: 'flex', alignItems: 'stretch',
      background: bg, color: fg, borderBottom: `1px solid ${borderColor}`,
      fontFamily: 'Inter, sans-serif', fontSize: 12, userSelect: 'none', flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px' }}>
        <div style={{ width: 14, height: 14, borderRadius: 3, background: accent, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0b0b0f', fontWeight: 800, fontSize: 9 }}>L</div>
        <span style={{ fontWeight: 500, letterSpacing: 0.1, opacity: 0.85 }}>{title}</span>
      </div>
      <div style={{ flex: 1 }} />
      <div style={{ display: 'flex' }}>
        {['─','▢','✕'].map((g, i) => (
          <div key={i} style={{
            width: 44, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, opacity: 0.7, cursor: 'pointer',
          }}>{g}</div>
        ))}
      </div>
    </div>
  );
}

// ── Sidebar ──────────────────────────────────────────────────────
function Sidebar({ active, bg, fg, fgMuted, accent, activeBg, borderColor, hoverBg, user, variant = 'default' }) {
  const items = [
    { key: 'scan',     label: 'Scan',     icon: <IconScan/>, badge: '•' },
    { key: 'filters',  label: 'Filtres',  icon: <IconFilters/> },
    { key: 'runes',    label: 'Runes',    icon: <IconRunes/>, badge: '1.2k' },
    { key: 'monsters', label: 'Monsters', icon: <IconMonsters/> },
    { key: 'profile',  label: 'Profile',  icon: <IconProfile/> },
    { key: 'settings', label: 'Settings', icon: <IconSettings/> },
  ];
  return (
    <div style={{
      width: 188, background: bg, color: fg, display: 'flex', flexDirection: 'column',
      borderRight: `1px solid ${borderColor}`, fontFamily: 'Inter, sans-serif', flexShrink: 0,
    }}>
      <div style={{ padding: '18px 14px 10px', fontSize: 10, fontWeight: 600, letterSpacing: 1.5, color: fgMuted, textTransform: 'uppercase' }}>
        Workspace
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2, padding: '0 8px' }}>
        {items.map(it => {
          const isActive = it.key === active;
          const isScanLive = it.key === 'scan' && it.badge === '•';
          return (
            <div key={it.key} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 10px', borderRadius: 6,
              fontSize: 13, fontWeight: isActive ? 600 : 500,
              color: isActive ? fg : fgMuted,
              background: isActive ? activeBg : 'transparent',
              cursor: 'pointer',
              borderLeft: isActive && variant === 'accentbar' ? `2px solid ${accent}` : '2px solid transparent',
            }}>
              <span style={{ color: isActive ? accent : fgMuted, display: 'flex' }}>{it.icon}</span>
              <span>{it.label}</span>
              {it.badge && (
                isScanLive ? (
                  <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ width: 7, height: 7, borderRadius: 4, background: accent, boxShadow: `0 0 8px ${accent}` }}/>
                    <span style={{ fontSize: 10, color: accent, fontWeight: 700, letterSpacing: 0.5 }}>LIVE</span>
                  </span>
                ) : (
                  <span style={{
                    marginLeft: 'auto', fontSize: 10, fontFamily: 'JetBrains Mono',
                    padding: '2px 6px', borderRadius: 4,
                    background: fgMuted + '22', color: fgMuted,
                  }}>{it.badge}</span>
                )
              )}
            </div>
          );
        })}
      </nav>
      <div style={{ flex: 1 }} />
      <div style={{
        margin: 10, padding: 10, borderRadius: 8,
        background: hoverBg, display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <div style={{
          width: 28, height: 28, borderRadius: 14,
          background: `linear-gradient(135deg, ${accent}, ${accent}80)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#0b0b0f', fontWeight: 700, fontSize: 12,
        }}>{user.initials}</div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: fg, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user.name}</div>
          <div style={{ fontSize: 10, color: fgMuted, fontFamily: 'JetBrains Mono' }}>{user.region}</div>
        </div>
      </div>
    </div>
  );
}

// ── Placeholder "rune" icon — hex with slot number ───────────────
// Generic abstract shape; user will swap for real Swarfarm assets.
function RuneGlyph({ size = 56, grade = 6, slot = 2, color = '#8a96ff', bg }) {
  const gradeStars = '★'.repeat(grade) + '☆'.repeat(Math.max(0, 6 - grade));
  return (
    <div style={{
      width: size, height: size, position: 'relative',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      clipPath: 'polygon(50% 0, 100% 25%, 100% 75%, 50% 100%, 0 75%, 0 25%)',
      background: bg || `linear-gradient(145deg, ${color}, ${color}88)`,
      color: '#0b0b10', fontFamily: 'JetBrains Mono', fontWeight: 700,
    }}>
      <div style={{ fontSize: size * 0.38, letterSpacing: -1 }}>{slot}</div>
      <div style={{
        position: 'absolute', bottom: size * 0.12, fontSize: size * 0.13,
        color: '#0b0b10', opacity: 0.7, letterSpacing: -0.5,
      }}>{gradeStars.slice(0, 3)}</div>
    </div>
  );
}

// ── Rune data ────────────────────────────────────────────────────
const SUBSTATS = ['HP%', 'ATK%', 'DEF%', 'SPD', 'CRIT', 'CDMG', 'RES', 'ACC'];

function mk(i, sec, type, slot, main, efficiency, upgrade, set, stars = 6) {
  return { i, sec, type, slot, main, efficiency, upgrade, set, stars };
}

const RUNE_HISTORY = [
  // sec ago, type (new/upgrade/reroll), slot, main stat, efficiency %, upgrade (to lv12…), set
  mk(0,    3,    'upgrade', 4, 'CRIT DMG 80%',  94.6, '→ +15', 'Rage',        6),
  mk(1,    47,   'new',     2, 'ATK 12%',       62.1, '+0',    'Violent',     6),
  mk(2,    112,  'new',     6, 'ACC 55%',       78.4, '+0',    'Will',        6),
  mk(3,    184,  'upgrade', 1, 'ATK 175',       88.2, '→ +12', 'Fatal',       5),
  mk(4,    260,  'new',     3, 'DEF 12%',       45.8, '+0',    'Despair',     5),
  mk(5,    320,  'new',     5, 'HP 12%',        71.3, '+0',    'Energy',      6),
  mk(6,    410,  'reroll',  2, 'SPD 22',        96.1, 'reroll','Swift',       6),
  mk(7,    488,  'new',     4, 'CRIT 58%',      68.5, '+0',    'Focus',       6),
  mk(8,    562,  'new',     6, 'HP 12%',        52.0, '+0',    'Guard',       5),
  mk(9,    640,  'upgrade', 3, 'DEF 12%',       81.7, '→ +9',  'Blade',       6),
  mk(10,   720,  'new',     1, 'ATK 175',       74.2, '+0',    'Rage',        6),
  mk(11,   800,  'new',     5, 'HP 63',         39.4, '+0',    'Endure',      4),
];

const SETS = {
  Rage:    '#e86161', Violent: '#b892ff', Will:    '#9dd9ff',
  Fatal:   '#f4a74a', Despair: '#7d7287', Energy:  '#f0c949',
  Swift:   '#5dd1e8', Focus:   '#ffb4a2', Guard:   '#7ea6ff',
  Blade:   '#e86161', Endure:  '#b0a896',
};

function fmtAgo(sec) {
  if (sec < 60)     return `${sec}s`;
  if (sec < 3600)   return `${Math.floor(sec/60)}m ${sec%60}s`;
  return `${Math.floor(sec/3600)}h ${Math.floor((sec%3600)/60)}m`;
}

Object.assign(window, {
  IconScan, IconFilters, IconRunes, IconMonsters, IconProfile, IconSettings,
  IconPlay, IconPause, IconArrowUp, IconSparkle, IconClock, IconSearch,
  IconKeep, IconSell, VerdictBadge,
  WinTitleBar, Sidebar, RuneGlyph, RUNE_HISTORY, SETS, SUBSTATS, fmtAgo,
});
