// Runes page — dense table + filters + side panel detail

const R = {
  bg: '#0d0907',
  bgGrad: 'radial-gradient(ellipse at 12% 0%, #3a1624 0%, #0d0907 50%), radial-gradient(ellipse at 100% 100%, #2a1018 0%, #0d0907 55%)',
  panel: 'rgba(36, 20, 26, 0.72)',
  panel2: 'rgba(48, 26, 34, 0.45)',
  border: 'rgba(255,220,230,0.06)',
  borderStr: 'rgba(255,220,230,0.10)',
  fg: '#f5ecef', fgDim: '#c2a7af', fgMute: '#7a6168',
  accent: '#f0689a', accent2: '#d93d7a', accentDim: 'rgba(240,104,154,0.14)',
  ok: '#5dd39e', warn: '#f5c16e', err: '#ef6461',
};

const RUNE_SETS_ALL = ['Violent', 'Will', 'Swift', 'Despair', 'Focus', 'Energy', 'Fatal', 'Rage', 'Blade', 'Guard', 'Endure', 'Nemesis', 'Vampire', 'Destroy', 'Fight'];
const RARITIES = { hero: { label: 'Héros', color: '#7ba6ff' }, legend: { label: 'Légende', color: '#f5c16e' } };

const SUBSTAT_POOL_R = ['HP+','HP%','ATK+','ATK%','DEF+','DEF%','SPD+','CRI Rate%','CRI Dmg%','RES%','ACC%'];

function mkRuneFull(idx) {
  const h = Math.abs((idx * 2654435761) | 0);
  const set = RUNE_SETS_ALL[h % RUNE_SETS_ALL.length];
  const slot = 1 + (h % 6);
  const grade = 5 + ((h >> 3) % 2);
  const level = (h >> 5) % 16; // 0..15
  const rarity = ((h >> 7) % 5 === 0) ? 'legend' : 'hero';

  const mainStatMap = {
    1: ['ATK+'],
    2: ['ATK%','HP%','DEF%','SPD'],
    3: ['DEF+'],
    4: ['CRI Rate%','CRI Dmg%','HP%','ATK%','DEF%'],
    5: ['HP+'],
    6: ['ACC%','RES%','HP%','ATK%','DEF%'],
  };
  const mainStat = mainStatMap[slot][(h >> 9) % mainStatMap[slot].length];
  const mainValue = mainStat.endsWith('+')
    ? (100 + ((h >> 11) % 1400))
    : (8 + ((h >> 11) % 58)) + '%';

  // 4 substats — filter out main stat's family
  const pool = SUBSTAT_POOL_R.filter(s => s.replace(/[%+]/g,'') !== mainStat.replace(/[%+]/g,''));
  const subs = [];
  let p = [...pool];
  for (let i = 0; i < 4; i++) {
    const j = (h + i * 101) % p.length;
    const n = p.splice(j, 1)[0];
    const val = n.endsWith('%') ? (3 + ((h + i * 13) % 20)) + '%' : (5 + ((h + i * 13) % 35));
    subs.push({ name: n, value: val, rolled: 1 + ((h + i * 7) % 4) });
  }

  const eff = 35 + (h % 80) + Math.random() * 8;
  const equipped = ((h >> 13) % 3) !== 0; // ~66% equipped
  const ownerIdx = equipped ? (h >> 15) % MONSTER_NAMES.length : null;
  const ownerName = ownerIdx != null ? MONSTER_NAMES[ownerIdx] : null;

  return { idx, set, slot, grade, level, rarity, mainStat, mainValue, subs, efficiency: eff, equipped, ownerName };
}

const RUNES = Array.from({ length: 180 }, (_, i) => mkRuneFull(i));

// Compact hexagon for table rows
function RuneHexMini({ slot, grade, color, size = 28 }) {
  return (
    <div style={{ width: size, height: size, position: 'relative', flexShrink: 0 }}>
      <svg viewBox="0 0 32 32" width={size} height={size}>
        <polygon points="16,2 28,9 28,23 16,30 4,23 4,9"
          fill={`${color}22`} stroke={color} strokeWidth="1.2"/>
        <text x="16" y="19" textAnchor="middle" fontFamily="JetBrains Mono" fontWeight="700"
          fontSize="10" fill={color}>{slot}</text>
      </svg>
      {grade >= 6 && (
        <div style={{ position: 'absolute', top: -2, right: -2, fontSize: 8, color: '#f5c16e' }}>★</div>
      )}
    </div>
  );
}

function RuneHexBig({ slot, grade, color, size = 92 }) {
  return (
    <div style={{ width: size, height: size, position: 'relative', flexShrink: 0 }}>
      <svg viewBox="0 0 64 64" width={size} height={size}>
        <defs>
          <radialGradient id={`rg-${slot}`} cx="50%" cy="35%">
            <stop offset="0%" stopColor={color} stopOpacity="0.4"/>
            <stop offset="100%" stopColor={color} stopOpacity="0.08"/>
          </radialGradient>
        </defs>
        <polygon points="32,4 56,18 56,46 32,60 8,46 8,18"
          fill={`url(#rg-${slot})`} stroke={color} strokeWidth="1.8"/>
        <text x="32" y="36" textAnchor="middle" fontFamily="JetBrains Mono" fontWeight="700"
          fontSize="20" fill={color}>{slot}</text>
      </svg>
      {grade >= 6 && (
        <div style={{ position: 'absolute', top: -4, right: -4, display: 'flex', gap: 1 }}>
          {Array.from({ length: grade }).map((_, i) => (
            <span key={i} style={{ fontSize: 10, color: '#f5c16e' }}>★</span>
          ))}
        </div>
      )}
    </div>
  );
}

function RarityChip({ rarity }) {
  const r = RARITIES[rarity];
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 4,
      background: r.color + '18', color: r.color,
      border: `1px solid ${r.color}33`,
      fontSize: 10, fontWeight: 600, letterSpacing: 0.3,
    }}>{r.label}</span>
  );
}

function SubstatInline({ s, color }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'baseline', gap: 3,
      fontFamily: 'JetBrains Mono', fontSize: 10,
      color: R.fgDim,
    }}>
      <span style={{ opacity: 0.7 }}>{s.name}</span>
      <span style={{ color: R.fg, fontWeight: 600 }}>{s.value}</span>
      {s.rolled > 1 && <span style={{ color, fontSize: 8, fontWeight: 700 }}>+{s.rolled - 1}</span>}
    </span>
  );
}

function RuneTableRow({ rune, onClick, selected }) {
  const effColor = rune.efficiency > 90 ? R.ok : rune.efficiency > 75 ? R.accent : rune.efficiency > 60 ? R.fgDim : R.fgMute;
  return (
    <div onClick={onClick} style={{
      display: 'grid',
      gridTemplateColumns: '32px 36px 80px 44px 80px 260px 1fr 160px',
      alignItems: 'center', gap: 12,
      padding: '8px 16px',
      borderBottom: `1px solid ${R.border}`,
      background: selected ? R.accentDim : 'transparent',
      cursor: 'pointer',
      transition: 'background 0.12s',
    }}>
      <RuneHexMini slot={rune.slot} grade={rune.grade} color={R.accent}/>
      <div style={{ display: 'flex', alignItems: 'center', gap: 3, color: R.accent, fontFamily: 'JetBrains Mono', fontWeight: 700, fontSize: 11 }}>
        <span>{rune.grade}</span>
        <span style={{ fontSize: 10 }}>★</span>
      </div>
      <div style={{ fontSize: 12, color: R.fg, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{rune.set}</div>
      <div style={{ fontSize: 11, color: R.fg, fontFamily: 'JetBrains Mono', fontWeight: 600, marginLeft: -14 }}>
        {rune.level === 15 ? <span style={{ color: R.accent }}>+15</span> : `+${rune.level}`}
      </div>
      <div>
        <div style={{ fontSize: 10, color: R.fgMute }}>{rune.mainStat}</div>
        <div style={{ fontSize: 12, color: R.fg, fontFamily: 'JetBrains Mono', fontWeight: 700 }}>{rune.mainValue}</div>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2px 8px', minWidth: 0, overflow: 'hidden', marginLeft: -6 }}>
        {rune.subs.map((s, i) => <SubstatInline key={i} s={s} color={R.accent}/>)}
      </div>
      <div/>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
        <div style={{ fontSize: 12, color: rune.equipped ? R.fg : R.fgMute, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontStyle: rune.equipped ? 'normal' : 'italic', fontWeight: rune.equipped ? 600 : 400 }}>
          {rune.equipped ? rune.ownerName : '— libre'}
        </div>
        <div style={{ fontSize: 11, fontFamily: 'JetBrains Mono', fontWeight: 700, color: effColor }}>
          {rune.efficiency.toFixed(1)}%
        </div>
      </div>
    </div>
  );
}

function RunesPage() {
  const [sortBy, setSortBy] = React.useState('efficiency');
  const [sortDir, setSortDir] = React.useState('desc');
  const [filterSet, setFilterSet] = React.useState(null);
  const [filterSlot, setFilterSlot] = React.useState(null);
  const [filterGrade, setFilterGrade] = React.useState(null);
  const [filterRarity, setFilterRarity] = React.useState(null);
  const [filterLevelMin, setFilterLevelMin] = React.useState(0);
  const [filterEquipped, setFilterEquipped] = React.useState('all');
  const [selectedIdx, setSelectedIdx] = React.useState(0);
  const [simuOpen, setSimuOpen] = React.useState(false);

  const toggleSort = (k) => {
    if (sortBy === k) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortBy(k); setSortDir('desc'); }
  };

  const sorters = {
    efficiency: (a, b) => a.efficiency - b.efficiency,
    level:      (a, b) => a.level - b.level,
    grade:      (a, b) => a.grade - b.grade,
    slot:       (a, b) => a.slot - b.slot,
    set:        (a, b) => a.set.localeCompare(b.set),
  };

  const list = RUNES
    .filter(r => !filterSet || r.set === filterSet)
    .filter(r => !filterSlot || r.slot === filterSlot)
    .filter(r => !filterGrade || r.grade === filterGrade)
    .filter(r => !filterRarity || r.rarity === filterRarity)
    .filter(r => r.level >= filterLevelMin)
    .filter(r => filterEquipped === 'all' || (filterEquipped === 'equipped' ? r.equipped : !r.equipped))
    .sort((a, b) => sortDir === 'desc' ? sorters[sortBy](b, a) : sorters[sortBy](a, b));

  const selected = list.find(r => r.idx === selectedIdx) || list[0];
  const setsPresent = [...new Set(RUNES.map(r => r.set))].sort();

  const SortHead = ({ k, label, align }) => (
    <span onClick={() => toggleSort(k)} style={{
      cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 3,
      color: sortBy === k ? R.accent : R.fgMute,
      justifyContent: align === 'right' ? 'flex-end' : 'flex-start',
      width: '100%',
    }}>
      {label}
      {sortBy === k && <span style={{ fontSize: 8 }}>{sortDir === 'desc' ? '▼' : '▲'}</span>}
    </span>
  );

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: R.bg, backgroundImage: R.bgGrad, fontFamily: 'Inter, sans-serif' }}>
      <WinTitleBar bg="rgba(13,9,7,0.6)" fg={R.fg} title="Luci2US — Runes" accent={R.accent} borderColor={R.border} />

      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <Sidebar active="runes"
          bg="rgba(20,12,16,0.72)" fg={R.fg} fgMuted={R.fgMute} accent={R.accent}
          activeBg={R.accentDim} borderColor={R.border} hoverBg="rgba(255,255,255,0.04)"
          user={{ initials: 'AZ', name: 'ArtheZ', region: 'global · 47' }}
        />

        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Header */}
          <div style={{ padding: '22px 28px 12px' }}>
            <div style={{ fontSize: 11, color: R.accent, fontWeight: 600, letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 4 }}>Inventaire</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}>
              <div style={{ fontSize: 24, fontWeight: 600, color: R.fg, letterSpacing: -0.5 }}>Runes</div>
              <div style={{ fontSize: 12.5, color: R.fgDim }}>
                <span style={{ color: R.fg, fontFamily: 'JetBrains Mono' }}>{list.length.toLocaleString()}</span>
                <span style={{ color: R.fgMute }}> sur {RUNES.length.toLocaleString()}</span>
                <span style={{ color: R.fgMute, margin: '0 8px' }}>·</span>
                <span style={{ color: R.fg, fontFamily: 'JetBrains Mono' }}>{RUNES.filter(r => r.level === 15).length}</span> +15
                <span style={{ color: R.fgMute, margin: '0 8px' }}>·</span>
                <span style={{ color: R.fg, fontFamily: 'JetBrains Mono' }}>{RUNES.filter(r => !r.equipped).length}</span> libres
              </div>
            </div>
          </div>

          {/* Toolbar */}
          <div style={{ padding: '0 28px 14px', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {/* Set filter */}
            <select value={filterSet || ''} onChange={e => setFilterSet(e.target.value || null)} style={selectStyle()}>
              <option value="">Tous les sets</option>
              {setsPresent.map(s => <option key={s} value={s} style={{ background: '#1a0f14' }}>{s}</option>)}
            </select>

            {/* Slot filter */}
            <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 999, background: 'rgba(255,255,255,0.03)', border: `1px solid ${R.border}` }}>
              <div onClick={() => setFilterSlot(null)} style={pillStyle(!filterSlot)}>Slot</div>
              {[1,2,3,4,5,6].map(s => (
                <div key={s} onClick={() => setFilterSlot(filterSlot === s ? null : s)} style={pillStyle(filterSlot === s)}>
                  {s}
                </div>
              ))}
            </div>

            {/* Grade filter */}
            <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 999, background: 'rgba(255,255,255,0.03)', border: `1px solid ${R.border}` }}>
              {[{k: null, l: 'Tous'}, {k: 6, l: '6★'}, {k: 5, l: '5★'}].map(o => (
                <div key={o.l} onClick={() => setFilterGrade(o.k)} style={pillStyle(filterGrade === o.k)}>{o.l}</div>
              ))}
            </div>

            {/* Rarity */}
            <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 999, background: 'rgba(255,255,255,0.03)', border: `1px solid ${R.border}` }}>
              <div onClick={() => setFilterRarity(null)} style={pillStyle(!filterRarity)}>Tous</div>
              <div onClick={() => setFilterRarity(filterRarity === 'legend' ? null : 'legend')} style={pillStyle(filterRarity === 'legend', '#f5c16e')}>Légende</div>
              <div onClick={() => setFilterRarity(filterRarity === 'hero' ? null : 'hero')} style={pillStyle(filterRarity === 'hero', '#7ba6ff')}>Héros</div>
            </div>

            {/* Level slider */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', borderRadius: 999, background: 'rgba(255,255,255,0.03)', border: `1px solid ${R.border}` }}>
              <span style={{ fontSize: 11, color: R.fgMute }}>Level ≥</span>
              <input type="range" min="0" max="15" value={filterLevelMin} onChange={e => setFilterLevelMin(+e.target.value)}
                className="luci-range"
                style={{ width: 80, accentColor: R.accent, background: 'transparent' }}/>
              <span style={{ fontSize: 11, color: R.fg, fontFamily: 'JetBrains Mono', fontWeight: 600, minWidth: 18 }}>+{filterLevelMin}</span>
            </div>

            {/* Equipped */}
            <div style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 999, background: 'rgba(255,255,255,0.03)', border: `1px solid ${R.border}` }}>
              {[{k:'all',l:'Toutes'},{k:'equipped',l:'Équipées'},{k:'free',l:'Libres'}].map(o => (
                <div key={o.k} onClick={() => setFilterEquipped(o.k)} style={pillStyle(filterEquipped === o.k)}>{o.l}</div>
              ))}
            </div>
          </div>

          {/* Body */}
          <div style={{ flex: 1, display: 'flex', minHeight: 0, padding: '0 28px 20px', gap: 16 }}>
            <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column',
              background: R.panel, border: `1px solid ${R.border}`, borderRadius: 12,
              backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', overflow: 'hidden' }}>
              {/* Table header */}
              <div style={{
                display: 'grid', gridTemplateColumns: '32px 36px 80px 44px 80px 260px 1fr 160px',
                gap: 12, padding: '10px 16px',
                fontSize: 9.5, letterSpacing: 0.8, fontWeight: 700, textTransform: 'uppercase',
                borderBottom: `1px solid ${R.borderStr}`, background: 'rgba(0,0,0,0.2)',
              }}>
                <SortHead k="slot" label="Slot"/>
                <SortHead k="grade" label="Grade"/>
                <SortHead k="set" label="Set"/>
                <SortHead k="level" label="Lv"/>
                <span style={{ color: R.fgMute }}>Main stat</span>
                <span style={{ color: R.fgMute }}>Substats</span>
                <span/>
                <SortHead k="efficiency" label="Équipée sur / Eff."/>
              </div>
              <div style={{ flex: 1, overflow: 'auto' }}>
                {list.map(r => <RuneTableRow key={r.idx} rune={r} onClick={() => setSelectedIdx(r.idx)} selected={r.idx === selectedIdx}/>)}
              </div>
            </div>

            {/* Side panel */}
            {selected && <RuneSidePanel rune={selected} R={R} onSimu={() => setSimuOpen(true)}/>}
          </div>
        </div>
      </div>

      {simuOpen && selected && <SimuEquipModal rune={selected} R={R} onClose={() => setSimuOpen(false)}/>}
    </div>
  );
}

function selectStyle() {
  return {
    background: 'rgba(255,255,255,0.03)', border: `1px solid ${R.border}`,
    color: R.fg, fontSize: 12, fontFamily: 'Inter', padding: '6px 10px',
    borderRadius: 999, cursor: 'pointer', outline: 'none', fontWeight: 600,
  };
}

function pillStyle(active, color) {
  return {
    padding: '5px 11px', borderRadius: 999,
    background: active ? (color ? color + '22' : R.accentDim) : 'transparent',
    color: active ? (color || R.accent) : R.fgMute,
    fontSize: 11, fontWeight: 600, cursor: 'pointer',
    whiteSpace: 'nowrap',
  };
}

function RuneSidePanel({ rune, R, onSimu }) {
  const effColor = rune.efficiency > 90 ? R.ok : rune.efficiency > 75 ? R.accent : R.fgDim;
  return (
    <div style={{
      width: 320, flexShrink: 0,
      background: R.panel, border: `1px solid ${R.border}`, borderRadius: 12,
      backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
      padding: 20, display: 'flex', flexDirection: 'column', gap: 16, overflow: 'auto',
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
        <RuneHexBig slot={rune.slot} grade={rune.grade} color={R.accent} size={88}/>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 11, color: R.accent, fontWeight: 600, letterSpacing: 1.2, textTransform: 'uppercase', marginBottom: 2 }}>
            {rune.set} · Slot {rune.slot}
          </div>
          <div style={{ display: 'flex', gap: 1, color: R.accent, fontSize: 13, justifyContent: 'center' }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <span key={i} style={{ opacity: i < rune.grade ? 1 : 0.18 }}>★</span>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <RarityChip rarity={rune.rarity}/>
          <div style={{
            padding: '3px 10px', borderRadius: 999,
            background: rune.level === 15 ? R.accentDim : 'rgba(255,255,255,0.04)',
            color: rune.level === 15 ? R.accent : R.fg,
            fontSize: 11, fontFamily: 'JetBrains Mono', fontWeight: 700,
            border: `1px solid ${rune.level === 15 ? R.accent + '44' : R.border}`,
          }}>+{rune.level}</div>
        </div>
      </div>

      <div style={{ height: 1, background: R.border }}/>

      {/* Main stat */}
      <div>
        <div style={{ fontSize: 9, color: R.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 }}>Main stat</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '10px 12px',
          background: R.accentDim, border: `1px solid ${R.accent}33`, borderRadius: 8 }}>
          <span style={{ fontSize: 13, color: R.fg, fontWeight: 600 }}>{rune.mainStat}</span>
          <span style={{ fontSize: 18, color: R.accent, fontFamily: 'JetBrains Mono', fontWeight: 700 }}>{rune.mainValue}</span>
        </div>
      </div>

      {/* Substats */}
      <div>
        <div style={{ fontSize: 9, color: R.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 }}>Substats</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {rune.subs.map((s, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 12px', background: 'rgba(255,255,255,0.02)',
              border: `1px solid ${R.border}`, borderRadius: 8, fontFamily: 'JetBrains Mono',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 11, color: R.fgDim }}>{s.name}</span>
                {s.rolled > 1 && (
                  <span style={{
                    padding: '1px 5px', borderRadius: 3, background: R.accentDim,
                    color: R.accent, fontSize: 9, fontWeight: 700,
                  }}>+{s.rolled - 1}</span>
                )}
              </div>
              <span style={{ fontSize: 13, color: R.fg, fontWeight: 700 }}>{s.value}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ height: 1, background: R.border }}/>

      {/* Efficiency */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
          <span style={{ fontSize: 9, color: R.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase' }}>Efficacité</span>
          <span style={{ fontSize: 22, color: effColor, fontFamily: 'JetBrains Mono', fontWeight: 700 }}>{rune.efficiency.toFixed(1)}%</span>
        </div>
        <div style={{ height: 6, background: 'rgba(255,255,255,0.04)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ width: Math.min(100, rune.efficiency) + '%', height: '100%', background: effColor, boxShadow: `0 0 8px ${effColor}66` }}/>
        </div>
      </div>

      {/* Equipped on */}
      <div>
        <div style={{ fontSize: 9, color: R.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 }}>Équipée sur</div>
        {rune.equipped ? (
          <div style={{ padding: '10px 12px', background: 'rgba(255,255,255,0.02)', border: `1px solid ${R.border}`, borderRadius: 8,
            display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 8,
              background: 'linear-gradient(135deg, rgba(255,122,90,0.3), rgba(255,122,90,0.1))',
              border: '1px solid rgba(255,122,90,0.4)',
            }}/>
            <div>
              <div style={{ fontSize: 13, color: R.fg, fontWeight: 600 }}>{rune.ownerName}</div>
              <div style={{ fontSize: 10, color: R.fgMute }}>lv40 · 6★</div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '10px 12px', border: `1px dashed ${R.border}`, borderRadius: 8, color: R.fgMute, fontSize: 12, fontStyle: 'italic', textAlign: 'center' }}>
            Non équipée
          </div>
        )}
      </div>

      <button onClick={onSimu} style={{
        marginTop: 'auto', padding: '10px 14px', border: 'none', borderRadius: 8,
        background: `linear-gradient(180deg, ${R.accent}, ${R.accent2})`, color: '#fff',
        fontSize: 12.5, fontWeight: 600, cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        boxShadow: `0 8px 20px -8px ${R.accent}`,
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/>
        </svg>
        Simuler sur un monstre
      </button>
    </div>
  );
}

function SimuEquipModal({ rune, R, onClose }) {
  const [target, setTarget] = React.useState(null);
  // Show a few plausible candidates
  const candidates = MONSTER_NAMES.slice(0, 5).map((name, i) => ({
    name, stars: 6, current: (55 + i * 4).toFixed(1),
    delta: (3.5 + i * 1.3) * (i % 2 === 0 ? 1 : -1),
  }));
  return (
    <div onClick={onClose} style={{
      position: 'absolute', inset: 0, zIndex: 50,
      background: 'rgba(5,3,4,0.72)',
      backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 40,
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: '100%', maxWidth: 720, maxHeight: 600,
        display: 'flex', flexDirection: 'column',
        background: '#1a0f14', borderRadius: 16,
        border: `1px solid ${R.border}`,
        boxShadow: `0 40px 80px -20px rgba(0,0,0,0.6), 0 0 0 1px ${R.accent}22`,
        overflow: 'hidden',
      }}>
        <div style={{ padding: '20px 24px', borderBottom: `1px solid ${R.border}`,
          display: 'flex', alignItems: 'center', gap: 14 }}>
          <RuneHexBig slot={rune.slot} grade={rune.grade} color={R.accent} size={56}/>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 11, color: R.accent, fontWeight: 600, letterSpacing: 1.5, textTransform: 'uppercase' }}>Simulation d'équipement</div>
            <div style={{ fontSize: 17, fontWeight: 600, color: R.fg, marginTop: 2 }}>
              {rune.set} slot {rune.slot} +{rune.level} · <span style={{ color: R.accent, fontFamily: 'JetBrains Mono' }}>{rune.efficiency.toFixed(1)}%</span>
            </div>
          </div>
          <button onClick={onClose} style={{ width: 34, height: 34, border: `1px solid ${R.border}`, borderRadius: 8,
            background: 'transparent', color: R.fgDim, cursor: 'pointer', fontSize: 18 }}>×</button>
        </div>

        <div style={{ padding: 20, overflow: 'auto' }}>
          <div style={{ fontSize: 10, color: R.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 10 }}>
            Candidats suggérés
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {candidates.map((c, i) => {
              const positive = c.delta > 0;
              const selected = target === i;
              return (
                <div key={c.name} onClick={() => setTarget(i)} style={{
                  display: 'grid', gridTemplateColumns: '40px 1fr 90px 90px 90px',
                  gap: 14, alignItems: 'center',
                  padding: '10px 14px', borderRadius: 10,
                  background: selected ? R.accentDim : 'rgba(255,255,255,0.02)',
                  border: `1px solid ${selected ? R.accent + '66' : R.border}`,
                  cursor: 'pointer',
                }}>
                  <div style={{ width: 36, height: 36, borderRadius: 8,
                    background: `linear-gradient(135deg, hsl(${i*60}, 35%, 30%), hsl(${i*60+40}, 40%, 18%))`,
                    border: `1px solid rgba(255,255,255,0.15)` }}/>
                  <div>
                    <div style={{ fontSize: 13, color: R.fg, fontWeight: 600 }}>{c.name}</div>
                    <div style={{ fontSize: 10, color: R.fgMute, marginTop: 2 }}>lv40 · 6★</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 9, color: R.fgMute, letterSpacing: 1, fontWeight: 700, textTransform: 'uppercase' }}>Actuel</div>
                    <div style={{ fontSize: 13, color: R.fgDim, fontFamily: 'JetBrains Mono', fontWeight: 600 }}>{c.current}%</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 9, color: R.fgMute, letterSpacing: 1, fontWeight: 700, textTransform: 'uppercase' }}>Après</div>
                    <div style={{ fontSize: 13, color: positive ? R.ok : R.err, fontFamily: 'JetBrains Mono', fontWeight: 700 }}>
                      {(+c.current + c.delta).toFixed(1)}%
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      padding: '4px 9px', borderRadius: 999,
                      background: positive ? '#5dd39e18' : '#ef646118',
                      color: positive ? R.ok : R.err,
                      fontFamily: 'JetBrains Mono', fontSize: 12, fontWeight: 700,
                    }}>
                      {positive ? '▲' : '▼'} {positive ? '+' : ''}{c.delta.toFixed(1)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ marginTop: 14, padding: 12, borderRadius: 10, background: 'rgba(255,255,255,0.03)', border: `1px solid ${R.border}`,
            fontSize: 11.5, color: R.fgDim, lineHeight: 1.5 }}>
            Les candidats sont calculés à partir des monstres compatibles avec le set et le slot. Sélectionne-en un pour simuler l'équipement ; la bascule est non-destructive (preview only).
          </div>
        </div>

        <div style={{ padding: '14px 20px', borderTop: `1px solid ${R.border}`, display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{
            padding: '9px 16px', border: `1px solid ${R.border}`, borderRadius: 8,
            background: 'transparent', color: R.fgDim, fontSize: 12, fontWeight: 600, cursor: 'pointer',
          }}>Annuler</button>
          <button disabled={target == null} style={{
            padding: '9px 16px', border: 'none', borderRadius: 8,
            background: target != null ? `linear-gradient(180deg, ${R.accent}, ${R.accent2})` : 'rgba(255,255,255,0.04)',
            color: target != null ? '#fff' : R.fgMute,
            fontSize: 12, fontWeight: 600, cursor: target != null ? 'pointer' : 'not-allowed',
          }}>Équiper</button>
        </div>
      </div>
    </div>
  );
}

window.RunesPage = RunesPage;
