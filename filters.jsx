// Filtres page — sidebar de filtres sauvegardés + formulaire + modal Test
// Palette identique à Runes/Monsters

const F = {
  bg: '#0d0907',
  bgGrad: 'radial-gradient(ellipse at 12% 0%, #3a1624 0%, #0d0907 50%), radial-gradient(ellipse at 100% 100%, #2a1018 0%, #0d0907 55%)',
  panel: 'rgba(36, 20, 26, 0.72)',
  panel2: 'rgba(48, 26, 34, 0.45)',
  panelRow: 'rgba(255, 255, 255, 0.015)',
  border: 'rgba(255,220,230,0.06)',
  borderStr: 'rgba(255,220,230,0.10)',
  fg: '#f5ecef', fgDim: '#c2a7af', fgMute: '#7a6168',
  accent: '#f0689a', accent2: '#d93d7a', accentDim: 'rgba(240,104,154,0.14)',
  ok: '#5dd39e', warn: '#f5c16e', err: '#ef6461',
};

// ── Data ─────────────────────────────────────────────────────────
const RUNE_SETS_F = [
  ['Violent','Will','Swift','Despair','Rage','Fatal'],
  ['Energy','Blade','Focus','Guard','Endure','Revenge'],
  ['Nemesis','Vampire','Destroy','Fight','Determination','Enhance'],
  ['Accuracy','Tolerance','Intangible','Seal','Shield'],
];

const MAIN_STATS_F  = ['SPD','HP','HP%','ATK','ATK%','DEF','DEF%','CR','CD','ACC','RES'];
const INNATE_STATS  = ['SPD','HP','HP%','ATK','ATK%','DEF','DEF%','CR','CD','ACC','RES'];
const SUB_STATS_F   = [
  { k: 'SPD',  min: 0,  max: 45,  def: 27 },
  { k: 'HP',   min: 0,  max: 375, def: 36 },
  { k: 'HP%',  min: 0,  max: 40,  def: 18 },
  { k: 'ATK',  min: 0,  max: 100, def: 36 },
  { k: 'ATK%', min: 0,  max: 40,  def: 18 },
  { k: 'DEF',  min: 0,  max: 100, def: 36 },
  { k: 'DEF%', min: 0,  max: 40,  def: 18 },
  { k: 'CR',   min: 0,  max: 40,  def: 26 },
  { k: 'CD',   min: 0,  max: 55,  def: 31 },
  { k: 'ACC',  min: 0,  max: 60,  def: 35 },
  { k: 'RES',  min: 0,  max: 60,  def: 35 },
];

// Groupes/dossiers manuels
const FILTER_TREE = [
  {
    name: 'SLOT 4/6 FILTERS (PREMIUM)', expanded: true, children: [
      { name: 'ACC, RES (SPDx2 + HP...)', active: true, premium: true },
      { name: 'ACC, RES (SPDx3)' },
      { name: 'Flat (SPDx4)' },
    ],
  },
  {
    name: 'SLOT 2 FILTERS (NORMAL)', expanded: true, children: [
      { name: 'SPD (HP + ATK + DEF)' },
      { name: 'SPD (ACC + RES + HP...)' },
      { name: 'SPD (ACCx2 + RES)' },
      { name: 'SPD (RESx2 + ACC)' },
      { name: 'SPD (CR + CD + ACC)' },
      { name: 'SPD (CDx2 + CR | ACC...)' },
      { name: 'SPD (CDx2 + HP | ATK...)' },
      { name: 'SPD (CRx2 + CD | ACC)' },
      { name: 'SPD (CRx2 + HP | ATK...)' },
      { name: 'SPD (ACCx2 + HP | DE...)' },
      { name: 'SPD (RESx2 + HP | DE...)' },
      { name: 'SPD (Triple Rolls)' },
      { name: 'SPD (HP + ATK + DEF)...' },
      { name: 'SPD (CDx2 + HP | ATK...)' },
      { name: 'SPD (CRx2 + HP | ATK...)' },
      { name: 'SPD (ACCx2 + HP | DE...)' },
      { name: 'SPD (RESx2 + HP | DE...)' },
      { name: 'ATK, HP, DEF (SPDx1...)' },
      { name: 'ATK, HP, DEF (SPDx2...)' },
      { name: 'ATK, HP, DEF (SPDx2)' },
      { name: 'ATK, HP, DEF (SPDx3)' },
    ],
  },
  {
    name: 'SLOT 2/6 FILTERS (...)', expanded: false, children: [
      { name: 'ATK (CRx3 | CDx3)' },
      { name: 'HP (DEFx3)' },
      { name: 'DEF (HPx3)' },
    ],
  },
  {
    name: 'SLOT 4/6 FILTERS (...)', expanded: false, children: [
      { name: 'HP, DEF (SPD + CR + ...)' },
      { name: 'HP, DEF (SPD + ACC + ...)' },
    ],
  },
];

// ── Primitives ───────────────────────────────────────────────────
function Checkbox({ checked, onChange, label, color = F.accent, size = 14 }) {
  return (
    <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', userSelect: 'none' }} onClick={onChange}>
      <span style={{
        width: size, height: size, borderRadius: 3,
        background: checked ? color : 'transparent',
        border: `1.5px solid ${checked ? color : F.borderStr}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0, transition: 'all 0.12s',
      }}>
        {checked && (
          <svg viewBox="0 0 12 12" width={size - 4} height={size - 4}>
            <path d="M2 6l3 3 5-6" fill="none" stroke="#0d0907" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </span>
      {label && <span style={{ fontSize: 12, color: F.fg }}>{label}</span>}
    </label>
  );
}

function Radio({ checked, onChange, label, color = F.accent }) {
  return (
    <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', userSelect: 'none' }} onClick={onChange}>
      <span style={{
        width: 14, height: 14, borderRadius: 99,
        border: `1.5px solid ${checked ? color : F.borderStr}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        {checked && <span style={{ width: 7, height: 7, borderRadius: 99, background: color }}/>}
      </span>
      <span style={{ fontSize: 12, color: F.fg }}>{label}</span>
    </label>
  );
}

function SectionCard({ title, children, right }) {
  return (
    <div style={{
      background: F.panel, backdropFilter: 'blur(20px)',
      border: `1px solid ${F.border}`, borderRadius: 12,
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '10px 16px',
        background: 'rgba(0,0,0,0.18)',
        borderBottom: `1px solid ${F.border}`,
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.2, textTransform: 'uppercase', color: F.accent }}>{title}</span>
        <div style={{ flex: 1 }}/>
        {right}
      </div>
      <div style={{ padding: 16 }}>
        {children}
      </div>
    </div>
  );
}

// Grille checkbox auto-responsive
function CheckGrid({ options, values, onToggle, cols = 6 }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: '10px 16px' }}>
      {options.map(o => (
        <Checkbox key={o} checked={values.includes(o)} onChange={() => onToggle(o)} label={o}/>
      ))}
    </div>
  );
}

// Segmented pills radio
function PillsRadio({ options, value, onChange, colorMap }) {
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {options.map(o => {
        const active = value === o.v;
        const c = (colorMap && colorMap[o.v]) || F.accent;
        return (
          <button key={o.v} onClick={() => onChange(o.v)} style={{
            padding: '5px 12px', borderRadius: 999, cursor: 'pointer',
            background: active ? c + '22' : 'rgba(255,255,255,0.025)',
            border: `1px solid ${active ? c + '66' : F.borderStr}`,
            color: active ? c : F.fgDim,
            fontSize: 11.5, fontWeight: 600, fontFamily: 'Inter, sans-serif',
            transition: 'all 0.12s', letterSpacing: 0.2,
          }}>
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

// Slider + number
function RangeRow({ value, onChange, min, max, step = 1, suffix = '', width = '100%', disabled }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, width }}>
      <input type="range" className="luci-range" min={min} max={max} step={step} value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ flex: 1, opacity: disabled ? 0.35 : 1 }}/>
      <div style={{
        minWidth: 48, padding: '4px 8px', borderRadius: 6,
        background: 'rgba(255,255,255,0.03)', border: `1px solid ${F.borderStr}`,
        fontSize: 12, fontWeight: 700, fontFamily: 'JetBrains Mono',
        color: disabled ? F.fgMute : F.fg, textAlign: 'right',
      }}>{value}{suffix}</div>
    </div>
  );
}

// ── Sidebar de filtres (gauche, après nav) ───────────────────────
function FilterTreeSidebar({ tree, selected, onSelect }) {
  const [expanded, setExpanded] = React.useState(() => {
    const m = {};
    tree.forEach((g, i) => m[i] = g.expanded);
    return m;
  });
  const toggle = (i) => setExpanded(e => ({ ...e, [i]: !e[i] }));

  return (
    <div style={{
      width: 264, flexShrink: 0,
      background: 'rgba(20,12,16,0.55)',
      borderRight: `1px solid ${F.border}`,
      display: 'flex', flexDirection: 'column',
      fontFamily: 'Inter, sans-serif',
    }}>
      {/* Header */}
      <div style={{ padding: '16px 16px 12px' }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.5, color: F.accent, textTransform: 'uppercase', marginBottom: 4 }}>
          Bibliothèque
        </div>
        <div style={{ fontSize: 15, fontWeight: 600, color: F.fg, letterSpacing: -0.2 }}>
          Filtres S2US
        </div>
      </div>

      {/* Actions (+ / − / ↑ / ↓) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 6, padding: '0 12px 10px' }}>
        {[
          { ic: '+', title: 'Ajouter', kind: 'primary' },
          { ic: '−', title: 'Supprimer' },
          { ic: '↑', title: 'Monter' },
          { ic: '↓', title: 'Descendre' },
        ].map((b, i) => (
          <button key={i} title={b.title} style={{
            padding: '6px 0', borderRadius: 6,
            background: b.kind === 'primary' ? F.accentDim : 'rgba(255,255,255,0.03)',
            border: `1px solid ${b.kind === 'primary' ? F.accent + '55' : F.borderStr}`,
            color: b.kind === 'primary' ? F.accent : F.fg,
            fontSize: 14, fontWeight: 700, cursor: 'pointer', fontFamily: 'JetBrains Mono',
          }}>{b.ic}</button>
        ))}
      </div>

      {/* Import / Export / Test */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, padding: '0 12px 8px' }}>
        <button style={{
          padding: '7px 0', borderRadius: 6,
          background: 'rgba(255,255,255,0.03)', border: `1px solid ${F.borderStr}`,
          color: F.fgDim, fontSize: 11.5, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif',
        }}>Importer</button>
        <button style={{
          padding: '7px 0', borderRadius: 6,
          background: 'rgba(255,255,255,0.03)', border: `1px solid ${F.borderStr}`,
          color: F.fgDim, fontSize: 11.5, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif',
        }}>Exporter</button>
        <button onClick={() => window.__openFilterTest && window.__openFilterTest()} style={{
          padding: '7px 0', borderRadius: 6,
          background: F.accentDim, border: `1px solid ${F.accent}55`,
          color: F.accent, fontSize: 11.5, fontWeight: 700, cursor: 'pointer', fontFamily: 'Inter, sans-serif',
        }}>Test</button>
      </div>

      {/* Recherche */}
      <div style={{ padding: '0 12px 12px' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 10px', borderRadius: 6,
          background: 'rgba(255,255,255,0.025)', border: `1px solid ${F.borderStr}`,
        }}>
          <span style={{ color: F.fgMute }}><IconSearch/></span>
          <input placeholder="Rechercher…" style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            color: F.fg, fontSize: 12, fontFamily: 'Inter, sans-serif',
          }}/>
        </div>
      </div>

      {/* Tree */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 8px 12px' }}>
        {tree.map((g, gi) => (
          <div key={gi} style={{ marginBottom: 2 }}>
            <div onClick={() => toggle(gi)} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 8px', cursor: 'pointer', borderRadius: 4,
              fontSize: 11, fontWeight: 700, color: F.fgDim,
              letterSpacing: 0.5, textTransform: 'uppercase',
            }}>
              <span style={{ fontSize: 9, color: F.fgMute, width: 10, display: 'inline-block', transform: expanded[gi] ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }}>▶</span>
              <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{g.name}</span>
              <span style={{ fontSize: 10, color: F.fgMute, fontFamily: 'JetBrains Mono' }}>{g.children.length}</span>
            </div>
            {expanded[gi] && (
              <div>
                {g.children.map((c, ci) => {
                  const key = `${gi}-${ci}`;
                  const isSel = selected === key;
                  return (
                    <div key={ci} onClick={() => onSelect(key, c)} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '6px 8px 6px 26px', cursor: 'pointer',
                      borderRadius: 4,
                      fontSize: 12, fontWeight: isSel ? 600 : 500,
                      color: isSel ? F.fg : F.fgDim,
                      background: isSel ? F.accentDim : 'transparent',
                      borderLeft: isSel ? `2px solid ${F.accent}` : '2px solid transparent',
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                    }}>
                      <span style={{
                        width: 4, height: 4, borderRadius: 99,
                        background: isSel ? F.accent : F.fgMute, flexShrink: 0,
                      }}/>
                      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.name}</span>
                      {c.premium && (
                        <span style={{ fontSize: 8, color: F.warn, fontWeight: 700, letterSpacing: 0.5 }}>◆</span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer count */}
      <div style={{
        padding: '10px 14px',
        borderTop: `1px solid ${F.border}`,
        fontSize: 10, color: F.fgMute,
        fontFamily: 'JetBrains Mono', display: 'flex', justifyContent: 'space-between',
      }}>
        <span>47 filtres</span>
        <span>12 actifs</span>
      </div>
    </div>
  );
}

// ── Substat row : étoile (ignoré/obligatoire/optionnelle) + slider min ─
function SubstatEditorRow({ s, state, min, onState, onMin }) {
  // state: 'ignore' | 'required' | 'optional'
  const starColor = state === 'required' ? F.accent : state === 'optional' ? F.warn : F.fgMute;
  const starFill  = state === 'ignore' ? 'none' : starColor;
  const disabled  = state === 'ignore';

  const cycle = () => onState(
    state === 'ignore' ? 'required' :
    state === 'required' ? 'optional' : 'ignore'
  );

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '28px 60px 80px 1fr',
      alignItems: 'center', gap: 12,
      padding: '6px 0',
    }}>
      {/* star state */}
      <button onClick={cycle} title={
        state === 'required' ? 'Obligatoire (clic pour optionnelle)' :
        state === 'optional' ? 'Optionnelle (clic pour ignorer)' :
        'Ignorée (clic pour obligatoire)'
      } style={{
        width: 26, height: 26, borderRadius: 6, cursor: 'pointer',
        background: 'transparent', border: `1px solid ${state === 'ignore' ? F.borderStr : starColor + '55'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: starColor,
      }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill={starFill} stroke={starColor} strokeWidth="1.6" strokeLinejoin="round">
          <polygon points="12,2 15,9 22,10 17,15 18,22 12,18 6,22 7,15 2,10 9,9"/>
        </svg>
      </button>

      {/* stat name */}
      <div style={{
        fontSize: 12, fontFamily: 'JetBrains Mono', fontWeight: 700,
        color: disabled ? F.fgMute : F.fg,
      }}>{s.k}</div>

      {/* number + arrows */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 2,
        padding: '2px 6px', borderRadius: 6,
        background: 'rgba(255,255,255,0.03)', border: `1px solid ${F.borderStr}`,
        opacity: disabled ? 0.4 : 1,
      }}>
        <input type="number" min={s.min} max={s.max} value={min}
          onChange={(e) => onMin(Math.max(s.min, Math.min(s.max, Number(e.target.value) || 0)))}
          disabled={disabled}
          style={{
            width: 38, background: 'transparent', border: 'none', outline: 'none',
            color: F.fg, fontSize: 12, fontFamily: 'JetBrains Mono', fontWeight: 700, textAlign: 'right',
          }}/>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span onClick={() => !disabled && onMin(Math.min(s.max, min + 1))}
            style={{ fontSize: 9, color: F.fgMute, cursor: disabled ? 'default' : 'pointer', lineHeight: 1 }}>▲</span>
          <span onClick={() => !disabled && onMin(Math.max(s.min, min - 1))}
            style={{ fontSize: 9, color: F.fgMute, cursor: disabled ? 'default' : 'pointer', lineHeight: 1 }}>▼</span>
        </div>
      </div>

      <RangeRow value={min} onChange={onMin} min={s.min} max={s.max}
        disabled={disabled}/>
    </div>
  );
}

// ── Modal Test ───────────────────────────────────────────────────
function TestModal({ open, onClose, filterName }) {
  if (!open) return null;

  // fake results
  const results = Array.from({ length: 12 }, (_, i) => ({
    idx: i,
    set: ['Violent','Will','Swift','Fatal','Rage'][i % 5],
    slot: 1 + (i % 6),
    grade: 5 + (i % 2),
    level: (i * 3) % 16,
    main: ['SPD 22','ATK 12%','HP 12%','ACC 55%','CR 26%'][i % 5],
    eff: 68 + (i * 3.7) % 35,
    match: 0.7 + (i * 0.023) % 0.3,
  }));

  return (
    <div onClick={onClose} style={{
      position: 'absolute', inset: 0, zIndex: 100,
      background: 'rgba(5,3,4,0.72)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 40,
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        width: 760, maxHeight: 640, background: '#1a0f14',
        borderRadius: 16, border: `1px solid ${F.borderStr}`,
        boxShadow: `0 40px 80px -20px rgba(0,0,0,0.6), 0 0 0 1px ${F.accent}22`,
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        fontFamily: 'Inter, sans-serif',
      }}>
        {/* Header */}
        <div style={{
          padding: '18px 24px', borderBottom: `1px solid ${F.border}`,
          display: 'flex', alignItems: 'center', gap: 14,
        }}>
          <div style={{
            width: 42, height: 42, borderRadius: 10,
            background: F.accentDim, border: `1px solid ${F.accent}44`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: F.accent,
          }}>
            <IconPlay/>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.5, color: F.accent, textTransform: 'uppercase' }}>
              Test du filtre
            </div>
            <div style={{ fontSize: 17, fontWeight: 600, color: F.fg, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {filterName}
            </div>
          </div>
          <button onClick={onClose} style={{
            width: 34, height: 34, borderRadius: 8,
            background: 'rgba(255,255,255,0.03)', border: `1px solid ${F.borderStr}`,
            color: F.fgDim, fontSize: 16, cursor: 'pointer',
          }}>✕</button>
        </div>

        {/* Résumé */}
        <div style={{
          padding: '14px 24px',
          display: 'flex', gap: 28,
          borderBottom: `1px solid ${F.border}`,
          background: 'rgba(0,0,0,0.2)',
        }}>
          {[
            { label: 'Runes testées', value: '1 247', color: F.fgDim },
            { label: 'Match', value: '142', color: F.accent },
            { label: 'Taux', value: '11.4%', color: F.ok },
            { label: 'Gardées', value: '98', color: F.ok },
            { label: 'Vendues', value: '44', color: F.err },
          ].map((s, i) => (
            <div key={i}>
              <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', color: F.fgMute, marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: 18, fontWeight: 700, fontFamily: 'JetBrains Mono', color: s.color }}>{s.value}</div>
            </div>
          ))}
        </div>

        {/* Results list */}
        <div style={{ flex: 1, overflow: 'auto', padding: '4px 16px 12px' }}>
          <div style={{
            display: 'grid', gridTemplateColumns: '32px 44px 70px 44px 90px 1fr 70px 60px',
            padding: '10px 12px', gap: 10,
            fontSize: 9.5, fontWeight: 700, letterSpacing: 0.8, textTransform: 'uppercase', color: F.fgMute,
            borderBottom: `1px solid ${F.border}`, position: 'sticky', top: 0, background: '#1a0f14',
          }}>
            <span/>
            <span>Grade</span>
            <span>Set</span>
            <span>Lv</span>
            <span>Main</span>
            <span/>
            <span style={{ textAlign: 'right' }}>Eff.</span>
            <span style={{ textAlign: 'right' }}>Match</span>
          </div>
          {results.map(r => {
            const effColor = r.eff > 90 ? F.ok : r.eff > 75 ? F.accent : r.eff > 60 ? F.fgDim : F.fgMute;
            return (
              <div key={r.idx} style={{
                display: 'grid', gridTemplateColumns: '32px 44px 70px 44px 90px 1fr 70px 60px',
                padding: '8px 12px', gap: 10, alignItems: 'center',
                borderBottom: `1px solid ${F.border}`,
              }}>
                <svg viewBox="0 0 32 32" width="26" height="26">
                  <polygon points="16,2 28,9 28,23 16,30 4,23 4,9" fill={F.accent + '22'} stroke={F.accent} strokeWidth="1.2"/>
                  <text x="16" y="19" textAnchor="middle" fontFamily="JetBrains Mono" fontWeight="700" fontSize="10" fill={F.accent}>{r.slot}</text>
                </svg>
                <div style={{ fontSize: 11, fontFamily: 'JetBrains Mono', fontWeight: 700, color: F.accent }}>{r.grade}★</div>
                <div style={{ fontSize: 12, fontWeight: 600, color: F.fg }}>{r.set}</div>
                <div style={{ fontSize: 11, fontFamily: 'JetBrains Mono', fontWeight: 700, color: r.level === 15 ? F.accent : F.fg }}>+{r.level}</div>
                <div style={{ fontSize: 12, fontFamily: 'JetBrains Mono', fontWeight: 700, color: F.fg }}>{r.main}</div>
                <div/>
                <div style={{ fontSize: 11, fontFamily: 'JetBrains Mono', fontWeight: 700, color: effColor, textAlign: 'right' }}>{r.eff.toFixed(1)}%</div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    display: 'inline-block', padding: '2px 6px', borderRadius: 99,
                    background: F.ok + '22', color: F.ok, border: `1px solid ${F.ok}44`,
                    fontSize: 10, fontFamily: 'JetBrains Mono', fontWeight: 700,
                  }}>{(r.match * 100).toFixed(0)}%</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px', borderTop: `1px solid ${F.border}`,
          display: 'flex', gap: 10, justifyContent: 'flex-end',
        }}>
          <button onClick={onClose} style={{
            padding: '9px 18px', borderRadius: 8,
            background: 'transparent', border: `1px solid ${F.borderStr}`,
            color: F.fgDim, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'Inter, sans-serif',
          }}>Fermer</button>
          <button style={{
            padding: '9px 18px', borderRadius: 8,
            background: `linear-gradient(180deg, ${F.accent}, ${F.accent2})`,
            border: 'none', color: '#fff', fontSize: 12, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'Inter, sans-serif',
            boxShadow: `0 8px 20px -8px ${F.accent}`,
          }}>Appliquer sur l'inventaire</button>
        </div>
      </div>
    </div>
  );
}

// ── Page principale ──────────────────────────────────────────────
function FiltresPage() {
  const [selectedKey, setSelectedKey] = React.useState('0-0');
  const [selectedFilter, setSelectedFilter] = React.useState({ name: 'ACC, RES (SPDx2 + HP...)', premium: true });
  const [testOpen, setTestOpen] = React.useState(false);
  React.useEffect(() => { window.__openFilterTest = () => setTestOpen(true); return () => { delete window.__openFilterTest; }; }, []);

  const [enabled, setEnabled] = React.useState(true);
  const [filterName, setFilterName] = React.useState('ACC, RES (SPDx2 + HP...)');

  // Form state
  const [sets, setSets]           = React.useState(['Violent','Will']);
  const [smartLevel, setSmartLevel] = React.useState(5);
  const [rarity, setRarity]       = React.useState(['Hero','Legend']);
  const [slots, setSlots]         = React.useState([4, 6]);
  const [stars, setStars]         = React.useState([6]);
  const [klass, setKlass]         = React.useState('all'); // all | ancient | normal
  const [mains, setMains]         = React.useState(['SPD','HP%','ATK%','DEF%','ACC','RES']);
  const [innates, setInnates]     = React.useState(['SPD']);

  const [subIgnoreMode, setSubIgnoreMode] = React.useState(false);
  const [subStates, setSubStates] = React.useState({
    SPD: 'required', HP: 'required', 'HP%': 'required', ATK: 'required', 'ATK%': 'required',
    DEF: 'required', 'DEF%': 'required', CR: 'required', CD: 'required', ACC: 'required', RES: 'required',
  });
  const [subMins, setSubMins] = React.useState(() => {
    const m = {}; SUB_STATS_F.forEach(s => m[s.k] = s.def); return m;
  });
  const [optionalRequired, setOptionalRequired] = React.useState(4);

  const [effMin, setEffMin]       = React.useState(141);
  const [effSource, setEffSource] = React.useState('S2US');

  const [grindstone, setGrindstone] = React.useState('');
  const [gem, setGem]               = React.useState('');

  const toggleArr = (arr, setArr) => (val) => {
    setArr(arr.includes(val) ? arr.filter(x => x !== val) : [...arr, val]);
  };

  const onSelectFilter = (key, c) => {
    setSelectedKey(key);
    setSelectedFilter(c);
    setFilterName(c.name);
  };

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: F.bg, backgroundImage: F.bgGrad, fontFamily: 'Inter, sans-serif', position: 'relative' }}>
      <WinTitleBar bg="rgba(13,9,7,0.6)" fg={F.fg} title="Luci2US — Filtres" accent={F.accent} borderColor={F.border} />

      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <Sidebar active="filters"
          bg="rgba(20,12,16,0.72)" fg={F.fg} fgMuted={F.fgMute} accent={F.accent}
          activeBg={F.accentDim} borderColor={F.border} hoverBg="rgba(255,255,255,0.04)"
          user={{ initials: 'AZ', name: 'ArtheZ', region: 'global · 47' }}
          variant="accentbar"
        />

        <FilterTreeSidebar tree={FILTER_TREE} selected={selectedKey} onSelect={onSelectFilter}/>

        {/* Main form column */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
          {/* Header bar */}
          <div style={{
            padding: '14px 24px',
            borderBottom: `1px solid ${F.border}`,
            background: 'rgba(0,0,0,0.15)',
            display: 'flex', alignItems: 'center', gap: 14,
            flexShrink: 0,
          }}>
            <Checkbox checked={enabled} onChange={() => setEnabled(e => !e)}/>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.2, color: F.fgMute, textTransform: 'uppercase' }}>Nom</span>
            <div style={{
              flex: 1, maxWidth: 560,
              padding: '7px 12px', borderRadius: 8,
              background: 'rgba(255,255,255,0.025)', border: `1px solid ${F.borderStr}`,
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <input value={filterName} onChange={(e) => setFilterName(e.target.value)}
                style={{
                  flex: 1, background: 'transparent', border: 'none', outline: 'none',
                  color: F.fg, fontSize: 13, fontWeight: 600, fontFamily: 'Inter, sans-serif',
                }}/>
              {selectedFilter.premium && (
                <span style={{
                  padding: '2px 8px', borderRadius: 99,
                  background: F.warn + '18', border: `1px solid ${F.warn}44`,
                  color: F.warn, fontSize: 9.5, fontWeight: 700, letterSpacing: 0.8,
                }}>◆ PREMIUM</span>
              )}
            </div>
            <div style={{ flex: 1 }}/>
            <button style={{
              padding: '8px 22px', borderRadius: 8, cursor: 'pointer',
              background: `linear-gradient(180deg, ${F.accent}, ${F.accent2})`,
              border: 'none', color: '#fff', fontSize: 12, fontWeight: 700, fontFamily: 'Inter, sans-serif',
              boxShadow: `0 8px 20px -8px ${F.accent}`, letterSpacing: 0.3,
            }}>Enregistrer</button>
          </div>

          {/* Form (full height, no inner scroll — artboard scrolls if needed) */}
          <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>

            {/* SETS */}
            <SectionCard title="Sets de runes" right={
              <span style={{ fontSize: 10.5, color: F.fgMute, fontFamily: 'JetBrains Mono' }}>
                {sets.length} / {RUNE_SETS_F.flat().length} sélectionnés
              </span>
            }>
              <div style={{ display: 'flex', gap: 24 }}>
                {RUNE_SETS_F.map((col, ci) => (
                  <div key={ci} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {col.map(s => (
                      <Checkbox key={s} checked={sets.includes(s)} onChange={() => toggleArr(sets, setSets)(s)} label={s}/>
                    ))}
                  </div>
                ))}
              </div>
            </SectionCard>

            {/* Row: Niveau + Rareté */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 14 }}>
              <SectionCard title="Niveau (Smart Filter)" right={
                <span style={{ fontSize: 10.5, color: F.fgMute }}>Niveau minimal d'upgrade</span>
              }>
                <RangeRow value={smartLevel} onChange={setSmartLevel} min={0} max={12}/>
              </SectionCard>

              <SectionCard title="Rareté">
                <div style={{ display: 'flex', gap: 20 }}>
                  {[
                    { k: 'Rare',   c: '#9dd9ff' },
                    { k: 'Hero',   c: '#7ba6ff' },
                    { k: 'Legend', c: F.warn },
                  ].map(r => (
                    <Checkbox key={r.k} checked={rarity.includes(r.k)} onChange={() => toggleArr(rarity, setRarity)(r.k)} label={r.k} color={r.c}/>
                  ))}
                </div>
              </SectionCard>
            </div>

            {/* Row: Slot + Etoiles + Classe */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr 1fr', gap: 14 }}>
              <SectionCard title="Slot">
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 6 }}>
                  {[1,2,3,4,5,6].map(n => {
                    const active = slots.includes(n);
                    return (
                      <button key={n} onClick={() => toggleArr(slots, setSlots)(n)} style={{
                        padding: '8px 0', borderRadius: 6, cursor: 'pointer',
                        background: active ? F.accentDim : 'rgba(255,255,255,0.025)',
                        border: `1px solid ${active ? F.accent + '55' : F.borderStr}`,
                        color: active ? F.accent : F.fgDim,
                        fontSize: 12, fontWeight: 700, fontFamily: 'JetBrains Mono',
                      }}>{n}</button>
                    );
                  })}
                </div>
              </SectionCard>

              <SectionCard title="Étoiles">
                <div style={{ display: 'flex', gap: 14 }}>
                  {[5,6].map(n => (
                    <Checkbox key={n} checked={stars.includes(n)} onChange={() => toggleArr(stars, setStars)(n)} label={`${n}★`} color={n === 6 ? F.warn : '#c2a7af'}/>
                  ))}
                </div>
              </SectionCard>

              <SectionCard title="Classe">
                <div style={{ display: 'flex', gap: 14 }}>
                  <Radio checked={klass === 'all'}     onChange={() => setKlass('all')}     label="Tous"/>
                  <Radio checked={klass === 'ancient'} onChange={() => setKlass('ancient')} label="Ancient"/>
                  <Radio checked={klass === 'normal'}  onChange={() => setKlass('normal')}  label="Normal"/>
                </div>
              </SectionCard>
            </div>

            {/* Propriété principale */}
            <SectionCard title="Propriété principale">
              <CheckGrid options={MAIN_STATS_F} values={mains} onToggle={toggleArr(mains, setMains)} cols={6}/>
            </SectionCard>

            {/* Propriété innée */}
            <SectionCard title="Propriété innée (préfixe)">
              <CheckGrid options={INNATE_STATS} values={innates} onToggle={toggleArr(innates, setInnates)} cols={6}/>
            </SectionCard>

            {/* Sous-propriétés */}
            <SectionCard title="Sous-propriétés" right={
              <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                <Checkbox checked={subIgnoreMode} onChange={() => setSubIgnoreMode(v => !v)} label="Tout ignorer"/>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, color: F.fgDim }}>
                  <span style={{ width: 10, height: 10, borderRadius: 99, background: F.accent }}/> obligatoire
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, color: F.fgDim }}>
                  <span style={{ width: 10, height: 10, borderRadius: 99, background: F.warn }}/> optionnelle
                </span>
              </div>
            }>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 200px', gap: 20 }}>
                <div>
                  {SUB_STATS_F.map(s => (
                    <SubstatEditorRow key={s.k} s={s}
                      state={subIgnoreMode ? 'ignore' : subStates[s.k]}
                      min={subMins[s.k]}
                      onState={(st) => setSubStates(m => ({ ...m, [s.k]: st }))}
                      onMin={(v) => setSubMins(m => ({ ...m, [s.k]: v }))}
                    />
                  ))}
                </div>

                <div style={{
                  padding: 14, borderRadius: 8,
                  background: 'rgba(255,255,255,0.02)', border: `1px solid ${F.border}`,
                  alignSelf: 'start',
                }}>
                  <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', color: F.fgMute, marginBottom: 10 }}>
                    Facultatives requises
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {[1,2,3,4].map(n => (
                      <Radio key={n} checked={optionalRequired === n} onChange={() => setOptionalRequired(n)} label={`${n} minimum`} color={F.warn}/>
                    ))}
                  </div>
                  <div style={{
                    marginTop: 12, paddingTop: 10,
                    borderTop: `1px solid ${F.border}`,
                    fontSize: 10.5, color: F.fgMute, lineHeight: 1.5,
                  }}>
                    La rune doit atteindre le minimum sur <b style={{ color: F.warn }}>{optionalRequired}</b> substat(s) optionnelle(s).
                  </div>
                </div>
              </div>
            </SectionCard>

            {/* Efficacité */}
            <SectionCard title="Efficacité" right={
              <span style={{ fontSize: 10.5, color: F.fgMute }}>Score minimum calculé par {effSource}</span>
            }>
              <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                <div style={{ flex: 1 }}>
                  <RangeRow value={effMin} onChange={setEffMin} min={0} max={200} suffix="%"/>
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  {['Swarfarm','S2US'].map(s => (
                    <button key={s} onClick={() => setEffSource(s)} style={{
                      padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
                      background: effSource === s ? F.accentDim : 'rgba(255,255,255,0.025)',
                      border: `1px solid ${effSource === s ? F.accent + '55' : F.borderStr}`,
                      color: effSource === s ? F.accent : F.fgDim,
                      fontSize: 11, fontWeight: 700, letterSpacing: 0.3, fontFamily: 'Inter, sans-serif',
                    }}>{s}</button>
                  ))}
                </div>
              </div>
            </SectionCard>

            {/* Simuler Meule / Gemme */}
            <SectionCard title="Simuler Meule / Gemme" right={
              <span style={{ fontSize: 10.5, color: F.fgMute }}>Appliqué avant évaluation</span>
            }>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                {[
                  { label: 'Meule', value: grindstone, set: setGrindstone, opts: ['Aucune','Legend ATK%','Legend SPD','Hero CD','Hero ACC'] },
                  { label: 'Gemme', value: gem,         set: setGem,         opts: ['Aucune','Legend ATK%','Legend HP%','Hero SPD','Hero CR'] },
                ].map((d, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ fontSize: 11, color: F.fgMute, fontWeight: 600, minWidth: 50 }}>{d.label}</div>
                    <div style={{ flex: 1, position: 'relative' }}>
                      <select value={d.value || 'Aucune'} onChange={(e) => d.set(e.target.value === 'Aucune' ? '' : e.target.value)}
                        style={{
                          width: '100%', appearance: 'none',
                          padding: '8px 30px 8px 12px', borderRadius: 6,
                          background: 'rgba(255,255,255,0.025)', border: `1px solid ${F.borderStr}`,
                          color: F.fg, fontSize: 12, fontWeight: 500, fontFamily: 'Inter, sans-serif',
                          cursor: 'pointer', outline: 'none',
                        }}>
                        {d.opts.map(o => <option key={o} value={o} style={{ background: '#1a0f14' }}>{o}</option>)}
                      </select>
                      <span style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: F.fgMute, fontSize: 10, pointerEvents: 'none' }}>▼</span>
                    </div>
                  </div>
                ))}
              </div>
            </SectionCard>

            <div style={{ height: 8 }}/>
          </div>
        </div>
      </div>

      <TestModal open={testOpen} onClose={() => setTestOpen(false)} filterName={filterName}/>
    </div>
  );
}

Object.assign(window, { FiltresPage });
