// Monsters page — grid + table toggle, side panel detail, magenta warm-dark palette

const M = {
  bg: '#0d0907',
  bgGrad: 'radial-gradient(ellipse at 12% 0%, #3a1624 0%, #0d0907 50%), radial-gradient(ellipse at 100% 100%, #2a1018 0%, #0d0907 55%)',
  panel: 'rgba(36, 20, 26, 0.72)',
  panel2: 'rgba(48, 26, 34, 0.45)',
  border: 'rgba(255,220,230,0.06)',
  borderStr: 'rgba(255,220,230,0.10)',
  fg: '#f5ecef', fgDim: '#c2a7af', fgMute: '#7a6168',
  accent: '#f0689a', accent2: '#d93d7a', accentDim: 'rgba(240,104,154,0.14)',
  ok: '#5dd39e', err: '#ef6461',
};

const ELEMENTS = {
  fire:  { label: 'Feu',     color: '#ff7a5a', symbol: '◆' },
  water: { label: 'Eau',     color: '#5aa6ff', symbol: '◆' },
  wind:  { label: 'Vent',    color: '#9be37a', symbol: '◆' },
  light: { label: 'Lumière', color: '#f5d76e', symbol: '◆' },
  dark:  { label: 'Ombre',   color: '#a77ae0', symbol: '◆' },
};

// Synthetic collection — generic fantasy monster names (no copyrighted names)
const MONSTER_NAMES = [
  'Ember Knight','Tidal Seer','Gale Archer','Dawn Oracle','Dusk Reaver',
  'Cinder Mage','Wave Guardian','Storm Dancer','Radiant Saint','Void Sentinel',
  'Flame Berserker','Frost Alchemist','Thunder Hawk','Celestial Judge','Shadow Priest',
  'Magma Giant','Abyss Whisper','Cyclone Fox','Sun Paladin','Night Stalker',
  'Ashen Warlock','Coral Siren','Breeze Dancer','Aurora Herald','Umbral Wolf',
  'Pyre Drake','Riptide Ronin','Tempest Monk','Sunspear Valkyrie','Gloomreaper',
  'Phoenix Brave','Kraken Keeper','Zephyr Sage','Solar Bishop','Nightbloom',
];

function hashStr(s) { let h = 0; for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0; return Math.abs(h); }
function mkMonster(i) {
  const name = MONSTER_NAMES[i % MONSTER_NAMES.length] + (i >= MONSTER_NAMES.length ? ` ${Math.floor(i / MONSTER_NAMES.length) + 1}` : '');
  const h = hashStr(name + i);
  const elKeys = Object.keys(ELEMENTS);
  const element = elKeys[h % elKeys.length];
  const stars = 3 + (h % 4); // 3-6
  const level = stars === 6 ? 40 : 10 + (h % 30);
  const equipped = (h % 7) !== 0; // ~85% equipped
  const equippedCount = equipped ? 4 + (h % 3) : 0; // 4-6
  const eff = equipped ? 50 + ((h >> 3) % 50) + Math.random() * 10 : 0;
  return { i, name, element, stars, level, equipped, equippedCount, efficiency: eff };
}
const MONSTERS = Array.from({ length: 36 }, (_, i) => mkMonster(i));

// Placeholder portrait — colored diamond with element tint
function MonsterPortrait({ m, size = 64 }) {
  const el = ELEMENTS[m.element];
  const h = hashStr(m.name);
  const hue = (h % 360);
  return (
    <div style={{
      width: size, height: size, position: 'relative', flexShrink: 0,
      borderRadius: 12, overflow: 'hidden',
      background: `linear-gradient(135deg, hsl(${hue}, 35%, 30%), hsl(${(hue+40)%360}, 40%, 18%))`,
      border: `1.5px solid ${el.color}55`,
      boxShadow: `0 0 0 1px rgba(0,0,0,0.4) inset`,
    }}>
      {/* Abstract silhouette placeholder */}
      <svg width={size} height={size} viewBox="0 0 64 64" style={{ position: 'absolute', inset: 0, opacity: 0.55 }}>
        <circle cx="32" cy="24" r="10" fill={el.color}/>
        <path d={`M14 52 Q14 36 32 36 Q50 36 50 52 Z`} fill={el.color} opacity="0.7"/>
      </svg>
      {/* Element badge */}
      <div style={{
        position: 'absolute', top: 4, right: 4,
        width: size * 0.22, height: size * 0.22, borderRadius: '50%',
        background: el.color, color: '#0d0907',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: size * 0.14, fontWeight: 700,
      }}>{el.label[0]}</div>
      {/* Level badge */}
      <div style={{
        position: 'absolute', bottom: 4, left: 4,
        padding: '1px 5px', borderRadius: 4,
        background: 'rgba(0,0,0,0.6)', color: M.fg,
        fontSize: size * 0.14, fontWeight: 700, fontFamily: 'JetBrains Mono',
      }}>lv{m.level}</div>
    </div>
  );
}

function Stars({ n, size = 10, color }) {
  return (
    <div style={{ display: 'flex', gap: 1, color: color || M.accent, fontSize: size }}>
      {Array.from({ length: 6 }).map((_, i) => (
        <span key={i} style={{ opacity: i < n ? 1 : 0.18 }}>★</span>
      ))}
    </div>
  );
}

function ElementChip({ element, size = 'sm' }) {
  const el = ELEMENTS[element];
  const pad = size === 'sm' ? '2px 7px' : '4px 10px';
  const fs = size === 'sm' ? 10 : 11.5;
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: pad, borderRadius: 999,
      background: el.color + '1c', color: el.color,
      border: `1px solid ${el.color}33`,
      fontSize: fs, fontWeight: 600, letterSpacing: 0.3,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: 3, background: el.color }}/>
      {el.label}
    </div>
  );
}

function RuneMiniDots({ count }) {
  return (
    <div style={{ display: 'flex', gap: 3 }}>
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} style={{
          width: 7, height: 7, borderRadius: '50%',
          background: i < count ? M.accent : 'rgba(255,255,255,0.08)',
          boxShadow: i < count ? `0 0 6px ${M.accent}66` : 'none',
        }}/>
      ))}
    </div>
  );
}

function MonsterCard({ m, onClick, selected }) {
  return (
    <div onClick={onClick} style={{
      padding: 12, borderRadius: 12,
      background: selected ? M.accentDim : 'rgba(255,255,255,0.02)',
      border: `1px solid ${selected ? M.accent + '66' : M.border}`,
      display: 'flex', flexDirection: 'column', gap: 10,
      cursor: 'pointer', transition: 'all 0.15s',
    }}>
      <div style={{ display: 'flex', gap: 10 }}>
        <MonsterPortrait m={m} size={56}/>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: 13, color: M.fg, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{m.name}</div>
          <Stars n={m.stars} size={11}/>
          <div style={{ marginTop: 6 }}><ElementChip element={m.element}/></div>
        </div>
      </div>
      <div style={{ height: 1, background: M.border }}/>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 11 }}>
        <div>
          <div style={{ fontSize: 9.5, letterSpacing: 1, color: M.fgMute, fontWeight: 700, textTransform: 'uppercase', marginBottom: 3 }}>Runes</div>
          <RuneMiniDots count={m.equippedCount}/>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 9.5, letterSpacing: 1, color: M.fgMute, fontWeight: 700, textTransform: 'uppercase', marginBottom: 3 }}>Eff. moy.</div>
          <div style={{
            fontFamily: 'JetBrains Mono', fontWeight: 700, fontSize: 13,
            color: m.equipped ? (m.efficiency > 85 ? M.ok : m.efficiency > 65 ? M.accent : M.fgDim) : M.fgMute,
          }}>{m.equipped ? m.efficiency.toFixed(1) + '%' : '—'}</div>
        </div>
      </div>
    </div>
  );
}

function MonsterTableRow({ m, onClick, selected }) {
  const el = ELEMENTS[m.element];
  return (
    <div onClick={onClick} style={{
      display: 'grid', gridTemplateColumns: '48px 1fr 90px 90px 70px 130px 90px',
      alignItems: 'center', gap: 14,
      padding: '8px 18px', borderBottom: `1px solid ${M.border}`,
      background: selected ? M.accentDim : 'transparent',
      cursor: 'pointer',
    }}>
      <MonsterPortrait m={m} size={40}/>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 13, color: M.fg, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{m.name}</div>
      </div>
      <Stars n={m.stars} size={11}/>
      <ElementChip element={m.element}/>
      <div style={{ fontSize: 12, color: M.fg, fontFamily: 'JetBrains Mono', fontWeight: 600 }}>lv{m.level}</div>
      <RuneMiniDots count={m.equippedCount}/>
      <div style={{
        fontFamily: 'JetBrains Mono', fontWeight: 600, fontSize: 13, textAlign: 'right',
        color: m.equipped ? (m.efficiency > 85 ? M.ok : m.efficiency > 65 ? M.accent : M.fgDim) : M.fgMute,
      }}>{m.equipped ? m.efficiency.toFixed(1) + '%' : '—'}</div>
    </div>
  );
}

function MonstersPage() {
  const [view, setView] = React.useState('grid'); // grid | table
  const [sortBy, setSortBy] = React.useState('efficiency');
  const [filterElement, setFilterElement] = React.useState(null);
  const [filterEquipped, setFilterEquipped] = React.useState('all'); // all | equipped | empty
  const [search, setSearch] = React.useState('');
  const [selectedId, setSelectedId] = React.useState(0);
  const [detailOpen, setDetailOpen] = React.useState(false);

  const sorters = {
    name:       (a, b) => a.name.localeCompare(b.name),
    stars:      (a, b) => b.stars - a.stars || b.level - a.level,
    level:      (a, b) => b.level - a.level,
    element:    (a, b) => a.element.localeCompare(b.element),
    efficiency: (a, b) => b.efficiency - a.efficiency,
  };
  const sortLabels = { name: 'Nom', stars: 'Étoiles', level: 'Niveau', element: 'Élément', efficiency: 'Efficacité' };

  const list = MONSTERS
    .filter(m => !filterElement || m.element === filterElement)
    .filter(m => filterEquipped === 'all' || (filterEquipped === 'equipped' ? m.equipped : !m.equipped))
    .filter(m => !search || m.name.toLowerCase().includes(search.toLowerCase()))
    .sort(sorters[sortBy]);

  const selected = list.find(m => m.i === selectedId) || list[0];

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: M.bg, backgroundImage: M.bgGrad, fontFamily: 'Inter, sans-serif' }}>
      <WinTitleBar bg="rgba(13,9,7,0.6)" fg={M.fg} title="Luci2US — Monsters" accent={M.accent} borderColor={M.border} />

      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <Sidebar active="monsters"
          bg="rgba(20,12,16,0.72)" fg={M.fg} fgMuted={M.fgMute} accent={M.accent}
          activeBg={M.accentDim} borderColor={M.border} hoverBg="rgba(255,255,255,0.04)"
          user={{ initials: 'AZ', name: 'ArtheZ', region: 'global · 47' }}
        />

        {/* Main list */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Header */}
          <div style={{ padding: '22px 28px 14px', display: 'flex', alignItems: 'flex-end', gap: 14 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, color: M.accent, fontWeight: 600, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 4 }}>Collection</div>
              <div style={{ fontSize: 24, fontWeight: 600, color: M.fg, letterSpacing: -0.5 }}>Monstres</div>
              <div style={{ fontSize: 12.5, color: M.fgDim, marginTop: 3 }}>
                <span style={{ color: M.fg, fontFamily: 'JetBrains Mono' }}>{list.length}</span> sur {MONSTERS.length} · {MONSTERS.filter(m => m.stars === 6).length} nat 6★
              </div>
            </div>
            <div style={{ display: 'flex', gap: 0, padding: 3, borderRadius: 999, background: 'rgba(255,255,255,0.04)', border: `1px solid ${M.border}` }}>
              {['grid', 'table'].map(v => (
                <div key={v} onClick={() => setView(v)} style={{
                  padding: '6px 14px', borderRadius: 999,
                  background: view === v ? M.accent : 'transparent',
                  color: view === v ? '#0d0907' : M.fgDim,
                  fontSize: 11.5, fontWeight: 600, cursor: 'pointer', textTransform: 'capitalize',
                }}>{v === 'grid' ? 'Grille' : 'Tableau'}</div>
              ))}
            </div>
          </div>

          {/* Toolbar */}
          <div style={{ padding: '0 28px 14px', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            {/* Search */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '7px 12px', borderRadius: 8,
              background: 'rgba(255,255,255,0.03)', border: `1px solid ${M.border}`,
              minWidth: 240,
            }}>
              <IconSearch style={{ color: M.fgMute }}/>
              <input placeholder="Rechercher un monstre…" value={search} onChange={e => setSearch(e.target.value)}
                style={{ background: 'transparent', border: 'none', outline: 'none', color: M.fg, fontSize: 12.5, fontFamily: 'Inter', flex: 1 }}/>
            </div>

            {/* Element filter chips */}
            <div style={{ display: 'flex', gap: 4, padding: 3, borderRadius: 999, background: 'rgba(255,255,255,0.03)', border: `1px solid ${M.border}` }}>
              <div onClick={() => setFilterElement(null)} style={{
                padding: '5px 11px', borderRadius: 999,
                background: !filterElement ? M.accentDim : 'transparent',
                color: !filterElement ? M.accent : M.fgDim,
                fontSize: 11, fontWeight: 600, cursor: 'pointer',
              }}>Tous</div>
              {Object.entries(ELEMENTS).map(([k, el]) => (
                <div key={k} onClick={() => setFilterElement(filterElement === k ? null : k)} style={{
                  padding: '5px 11px', borderRadius: 999,
                  background: filterElement === k ? el.color + '22' : 'transparent',
                  color: filterElement === k ? el.color : M.fgMute,
                  fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 5,
                }}>
                  <span style={{ width: 6, height: 6, borderRadius: 3, background: el.color }}/>
                  {el.label}
                </div>
              ))}
            </div>

            {/* Equipped filter */}
            <div style={{ display: 'flex', gap: 4, padding: 3, borderRadius: 999, background: 'rgba(255,255,255,0.03)', border: `1px solid ${M.border}` }}>
              {[{ k: 'all', l: 'Tous' }, { k: 'equipped', l: 'Runés' }, { k: 'empty', l: 'Vides' }].map(o => (
                <div key={o.k} onClick={() => setFilterEquipped(o.k)} style={{
                  padding: '5px 11px', borderRadius: 999,
                  background: filterEquipped === o.k ? M.accentDim : 'transparent',
                  color: filterEquipped === o.k ? M.accent : M.fgDim,
                  fontSize: 11, fontWeight: 600, cursor: 'pointer',
                }}>{o.l}</div>
              ))}
            </div>

            <div style={{ flex: 1 }}/>

            {/* Sort */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11.5, color: M.fgDim }}>
              <span>Trier :</span>
              <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{
                background: 'rgba(255,255,255,0.03)', border: `1px solid ${M.border}`,
                color: M.fg, fontSize: 12, fontFamily: 'Inter', padding: '6px 10px', borderRadius: 8, cursor: 'pointer', outline: 'none',
              }}>
                {Object.entries(sortLabels).map(([k, v]) => <option key={k} value={k} style={{ background: '#1a0f14' }}>{v}</option>)}
              </select>
            </div>
          </div>

          {/* Body split: list + detail panel */}
          <div style={{ flex: 1, display: 'flex', minHeight: 0, padding: '0 28px 20px' }}>
            <div style={{ flex: 1, minWidth: 0, overflow: 'auto', paddingRight: 16 }}>
              {view === 'grid' ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12, alignContent: 'start' }}>
                  {list.map(m => <MonsterCard key={m.i} m={m} onClick={() => setSelectedId(m.i)} selected={m.i === selectedId}/>)}
                </div>
              ) : (
                <div style={{
                  background: M.panel, border: `1px solid ${M.border}`, borderRadius: 12,
                  backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', overflow: 'hidden',
                }}>
                  <div style={{
                    display: 'grid', gridTemplateColumns: '48px 1fr 90px 90px 70px 130px 90px',
                    gap: 14, padding: '10px 18px',
                    fontSize: 9.5, color: M.fgMute, letterSpacing: 0.8, fontWeight: 700, textTransform: 'uppercase',
                    borderBottom: `1px solid ${M.border}`, background: 'rgba(0,0,0,0.15)',
                  }}>
                    <span></span><span>Nom</span><span>Étoiles</span><span>Élément</span><span>Niveau</span><span>Runes</span><span style={{ textAlign: 'right' }}>Eff.</span>
                  </div>
                  {list.map(m => <MonsterTableRow key={m.i} m={m} onClick={() => setSelectedId(m.i)} selected={m.i === selectedId}/>)}
                </div>
              )}
            </div>

            {/* Side panel */}
            {selected && (
              <div style={{
                width: 300, flexShrink: 0,
                background: M.panel, border: `1px solid ${M.border}`, borderRadius: 12,
                backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
                padding: 20, display: 'flex', flexDirection: 'column', gap: 16,
              }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
                  <MonsterPortrait m={selected} size={88}/>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 16, color: M.fg, fontWeight: 600, marginBottom: 4 }}>{selected.name}</div>
                    <Stars n={selected.stars} size={13}/>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <ElementChip element={selected.element} size="md"/>
                    <div style={{
                      padding: '4px 10px', borderRadius: 999,
                      background: 'rgba(255,255,255,0.04)', border: `1px solid ${M.border}`,
                      color: M.fg, fontSize: 11.5, fontFamily: 'JetBrains Mono', fontWeight: 600,
                    }}>lv{selected.level}</div>
                  </div>
                </div>
                <div style={{ height: 1, background: M.border }}/>
                <div>
                  <div style={{ fontSize: 10, color: M.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 10 }}>Runes équipées</div>
                  <div style={{ display: 'flex', gap: 6, justifyContent: 'space-between' }}>
                    {[1,2,3,4,5,6].map(slot => {
                      const has = slot <= selected.equippedCount;
                      return (
                        <div key={slot} style={{
                          flex: 1, aspectRatio: '1',
                          borderRadius: 8, border: `1px dashed ${has ? M.accent + '55' : M.border}`,
                          background: has ? M.accentDim : 'transparent',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 11, fontFamily: 'JetBrains Mono',
                          color: has ? M.accent : M.fgMute, fontWeight: 700,
                        }}>{slot}</div>
                      );
                    })}
                  </div>
                </div>
                <div style={{ height: 1, background: M.border }}/>
                <div>
                  <div style={{ fontSize: 10, color: M.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 10 }}>Stats</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {[
                      { k: 'HP',  v: 12420 + (selected.i * 37) % 3000 },
                      { k: 'ATK', v: 880 + (selected.i * 13) % 400 },
                      { k: 'DEF', v: 640 + (selected.i * 17) % 300 },
                      { k: 'SPD', v: 105 + (selected.i * 7) % 40 },
                    ].map(s => (
                      <div key={s.k} style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'JetBrains Mono', fontSize: 12 }}>
                        <span style={{ color: M.fgMute }}>{s.k}</span>
                        <span style={{ color: M.fg, fontWeight: 600 }}>{s.v.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ height: 1, background: M.border }}/>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span style={{ fontSize: 10, color: M.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase' }}>Eff. moy.</span>
                  <span style={{ marginLeft: 'auto', fontSize: 22, fontFamily: 'JetBrains Mono', fontWeight: 700,
                    color: selected.equipped ? (selected.efficiency > 85 ? M.ok : M.accent) : M.fgMute }}>
                    {selected.equipped ? selected.efficiency.toFixed(1) + '%' : '—'}
                  </span>
                </div>
                <button onClick={() => setDetailOpen(true)} style={{
                  marginTop: 'auto', padding: '10px 14px', border: 'none', borderRadius: 8,
                  background: `linear-gradient(180deg, ${M.accent}, ${M.accent2})`, color: '#fff',
                  fontSize: 12.5, fontWeight: 600, cursor: 'pointer',
                }}>Voir le détail complet</button>
              </div>
            )}
          </div>
        </div>
      </div>

      {detailOpen && selected && (
        <MonsterDetailModal monster={selected} M={M} ELEMENTS={ELEMENTS} onClose={() => setDetailOpen(false)}/>
      )}
    </div>
  );
}

window.MonstersPage = MonstersPage;
