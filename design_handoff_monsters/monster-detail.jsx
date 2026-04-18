// Monster Detail Modal — runes prio + stats/skills + optimiser

// Rune slot detail (placeholder hexagon + main stat + substats)
const RUNE_SETS = ['Violent', 'Will', 'Swift', 'Despair', 'Focus', 'Energy', 'Fatal', 'Rage', 'Blade', 'Guard'];
const MAIN_STATS = {
  1: 'ATK', 2: '% ATK / HP / DEF / SPD', 3: 'DEF',
  4: '% CRIT Rate / % CRIT DMG / % HP / etc', 5: 'HP', 6: '% ACC / % RES / % ATK / etc',
};
const SUBSTAT_POOL = ['HP+', 'HP%', 'ATK+', 'ATK%', 'DEF+', 'DEF%', 'SPD+', 'CRI Rate%', 'CRI Dmg%', 'RES%', 'ACC%'];

function mkRune(slot, seed) {
  const h = Math.abs((seed * 31 + slot * 97) | 0);
  const set = RUNE_SETS[h % RUNE_SETS.length];
  const grade = 5 + (h % 2); // 5 or 6
  const level = 9 + (h % 7); // 9-15
  const eff = 55 + (h % 50) + ((h >> 4) % 10);
  const mainStatMap = {
    1: 'ATK+', 2: ['ATK%', 'HP%', 'DEF%', 'SPD'][h % 4],
    3: 'DEF+', 4: ['CRI Rate%', 'CRI Dmg%', 'HP%', 'ATK%', 'DEF%'][h % 5],
    5: 'HP+', 6: ['ACC%', 'RES%', 'HP%', 'ATK%', 'DEF%'][h % 5],
  };
  const mainStat = mainStatMap[slot];
  const mainValue = slot % 2 === 1 ? (1200 + (h % 600)) : (30 + (h % 33) + '%');
  // 4 substats
  const subs = [];
  const pool = [...SUBSTAT_POOL].filter(s => !s.startsWith(mainStat.replace(/[%+]/g, '')));
  for (let i = 0; i < 4; i++) {
    const idx = (h + i * 17) % pool.length;
    const name = pool[idx];
    pool.splice(idx, 1);
    const val = name.endsWith('%') ? (4 + ((h + i) % 12)) + '%' : Math.floor(8 + ((h + i) % 30));
    subs.push({ name, value: val, rolled: 1 + ((h + i) % 4) });
  }
  return { slot, set, grade, level, mainStat, mainValue, subs, efficiency: eff };
}

function RuneHexPlaceholder({ slot, grade, size = 56, color }) {
  const c = color || '#f0689a';
  return (
    <div style={{ width: size, height: size, position: 'relative', flexShrink: 0 }}>
      <svg viewBox="0 0 64 64" width={size} height={size}>
        <polygon points="32,4 56,18 56,46 32,60 8,46 8,18"
          fill={`${c}18`} stroke={c} strokeWidth="1.5"/>
        <text x="32" y="34" textAnchor="middle" fontFamily="JetBrains Mono" fontWeight="700"
          fontSize="15" fill={c}>{slot}</text>
        <text x="32" y="46" textAnchor="middle" fontFamily="JetBrains Mono" fontWeight="600"
          fontSize="7" fill={c} opacity="0.7">{grade}★</text>
      </svg>
    </div>
  );
}

function EfficiencyBar({ value, color, bg }) {
  const pct = Math.min(100, value);
  return (
    <div style={{ height: 3, background: bg || 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
      <div style={{ width: pct + '%', height: '100%', background: color, borderRadius: 2 }}/>
    </div>
  );
}

function RuneSlotCard({ rune, M, onClick, selected }) {
  const effColor = rune.efficiency > 90 ? '#5dd39e' : rune.efficiency > 75 ? M.accent : M.fgDim;
  return (
    <div onClick={onClick} style={{
      padding: 14, borderRadius: 12,
      background: selected ? M.accentDim : 'rgba(255,255,255,0.02)',
      border: `1px solid ${selected ? M.accent + '66' : M.border}`,
      cursor: 'pointer', transition: 'all 0.15s',
      display: 'flex', flexDirection: 'column', gap: 10,
    }}>
      <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <RuneHexPlaceholder slot={rune.slot} grade={rune.grade} size={52} color={M.accent}/>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 6 }}>
            <div style={{ fontSize: 13, color: M.fg, fontWeight: 600 }}>{rune.set}</div>
            <div style={{ fontSize: 10, color: M.fgMute, fontFamily: 'JetBrains Mono' }}>+{rune.level}</div>
          </div>
          <div style={{ fontSize: 11, color: M.fgDim, marginTop: 2 }}>{rune.mainStat}</div>
          <div style={{ fontSize: 14, color: M.fg, fontFamily: 'JetBrains Mono', fontWeight: 700, marginTop: 2 }}>{rune.mainValue}</div>
        </div>
      </div>
      {/* Substats */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingTop: 8, borderTop: `1px solid ${M.border}` }}>
        {rune.subs.map((s, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, fontFamily: 'JetBrains Mono' }}>
            <span style={{ color: M.fgDim }}>
              {s.name}
              {s.rolled > 1 && <span style={{ color: M.accent, marginLeft: 4, fontSize: 9 }}>+{s.rolled - 1}</span>}
            </span>
            <span style={{ color: M.fg, fontWeight: 600 }}>{s.value}</span>
          </div>
        ))}
      </div>
      {/* Efficiency */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
          <span style={{ fontSize: 9, color: M.fgMute, letterSpacing: 1, fontWeight: 700, textTransform: 'uppercase' }}>Efficacité</span>
          <span style={{ fontSize: 13, color: effColor, fontFamily: 'JetBrains Mono', fontWeight: 700 }}>{rune.efficiency.toFixed(1)}%</span>
        </div>
        <EfficiencyBar value={rune.efficiency} color={effColor}/>
      </div>
    </div>
  );
}

function StatRow({ label, base, total, M, highlight }) {
  const diff = total - base;
  const pct = base > 0 ? ((diff / base) * 100).toFixed(0) : 0;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '70px 1fr 70px 70px', gap: 12, alignItems: 'center', padding: '6px 0', borderBottom: `1px solid ${M.border}` }}>
      <span style={{ fontSize: 11, color: M.fgMute, fontWeight: 600, letterSpacing: 0.3 }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ flex: 1, height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, overflow: 'hidden', position: 'relative' }}>
          <div style={{ width: `${(base / (total || base) * 100).toFixed(0)}%`, height: '100%', background: M.fgMute, opacity: 0.35 }}/>
          <div style={{ position: 'absolute', left: `${(base / (total || base) * 100).toFixed(0)}%`, top: 0, height: '100%', width: `${diff > 0 ? ((diff / (total || base)) * 100).toFixed(0) : 0}%`, background: highlight ? M.accent : M.accent + '99' }}/>
        </div>
      </div>
      <span style={{ fontSize: 11.5, color: M.fgDim, fontFamily: 'JetBrains Mono', textAlign: 'right' }}>{base.toLocaleString()}</span>
      <span style={{ fontSize: 12.5, color: diff > 0 ? M.accent : M.fg, fontFamily: 'JetBrains Mono', fontWeight: 700, textAlign: 'right' }}>
        {total.toLocaleString()}
        {diff > 0 && <span style={{ fontSize: 9, color: M.accent, marginLeft: 4 }}>+{pct}%</span>}
      </span>
    </div>
  );
}

function SkillRow({ skill, M }) {
  return (
    <div style={{ padding: '12px 0', borderBottom: `1px solid ${M.border}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <div style={{ width: 32, height: 32, borderRadius: 8, background: M.accentDim, border: `1px solid ${M.accent}33`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: M.accent, fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
          {skill.n}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 13, color: M.fg, fontWeight: 600 }}>{skill.name}</span>
            {skill.cd && <span style={{ fontSize: 10, color: M.fgMute, fontFamily: 'JetBrains Mono' }}>CD {skill.cd}t</span>}
          </div>
          <div style={{ fontSize: 11, color: M.fgDim, marginTop: 2, lineHeight: 1.4 }}>{skill.desc}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 9, color: M.fgMute, letterSpacing: 1, fontWeight: 700, textTransform: 'uppercase' }}>Mult</div>
          <div style={{ fontSize: 12, color: M.fg, fontFamily: 'JetBrains Mono', fontWeight: 700 }}>{skill.mult}</div>
        </div>
      </div>
    </div>
  );
}

function MonsterDetailModal({ monster, M, ELEMENTS, onClose }) {
  const [selectedSlot, setSelectedSlot] = React.useState(1);
  const [tab, setTab] = React.useState('runes');
  if (!monster) return null;

  const el = ELEMENTS[monster.element];
  const runes = [1,2,3,4,5,6].map(s => mkRune(s, monster.i));
  const equipped = runes.slice(0, monster.equippedCount || 6);
  const avgEff = equipped.length ? equipped.reduce((a, r) => a + r.efficiency, 0) / equipped.length : 0;

  const baseStats = [
    { k: 'HP',  base: 10800 + (monster.i * 37) % 2000 },
    { k: 'ATK', base: 680 + (monster.i * 13) % 300 },
    { k: 'DEF', base: 540 + (monster.i * 17) % 250 },
    { k: 'SPD', base: 101 },
    { k: 'CRI R',  base: 15 },
    { k: 'CRI D',  base: 50 },
    { k: 'RES',    base: 15 },
    { k: 'ACC',    base: 0 },
  ];
  const runedStats = baseStats.map((s, i) => {
    const boost = equipped.length > 0 ? (1.2 + ((monster.i + i) % 7) * 0.15) : 1;
    return { ...s, total: Math.floor(s.base * boost) + (s.k === 'SPD' ? Math.floor(20 + (monster.i % 40)) : 0) };
  });

  const skills = [
    { n: 1, name: 'Frappe ancestrale', desc: 'Inflige des dégâts basés sur l\'ATK. Augmente l\'ATK de l\'alliée la plus rapide pendant 2 tours.', mult: '3.8×ATK', cd: null },
    { n: 2, name: 'Cri de guerre', desc: 'Augmente la vitesse de tous les alliés pendant 2 tours et retire 1 effet néfaste.', mult: '—', cd: 4 },
    { n: 3, name: 'Éclat astral', desc: 'Inflige des dégâts à tous les ennemis et a 50% de chance d\'étourdir. Mult augmenté par l\'ATK de la cible.', mult: '5.2×ATK', cd: 5 },
  ];

  return (
    <div onClick={onClose} style={{
      position: 'absolute', inset: 0, zIndex: 50,
      background: 'rgba(5, 3, 4, 0.72)',
      backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 40,
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: '100%', maxWidth: 1120, height: '100%', maxHeight: 720,
        display: 'flex', flexDirection: 'column',
        background: '#1a0f14', borderRadius: 16,
        border: `1px solid ${M.border}`,
        boxShadow: `0 40px 80px -20px rgba(0,0,0,0.6), 0 0 0 1px ${M.accent}22`,
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16,
          borderBottom: `1px solid ${M.border}`,
          background: `linear-gradient(180deg, ${el.color}14, transparent)`,
        }}>
          <div style={{
            width: 72, height: 72, borderRadius: 14, flexShrink: 0,
            background: `linear-gradient(135deg, ${el.color}44, ${el.color}11)`,
            border: `1.5px solid ${el.color}66`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="48" height="48" viewBox="0 0 64 64" style={{ opacity: 0.7 }}>
              <circle cx="32" cy="24" r="10" fill={el.color}/>
              <path d="M14 52 Q14 36 32 36 Q50 36 50 52 Z" fill={el.color} opacity="0.7"/>
            </svg>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 11, color: M.accent, fontWeight: 600, letterSpacing: 1.5, textTransform: 'uppercase' }}>Monster detail</div>
            <div style={{ fontSize: 22, fontWeight: 600, color: M.fg, marginTop: 2, letterSpacing: -0.3 }}>{monster.name}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 6 }}>
              <div style={{ display: 'flex', gap: 1, color: M.accent, fontSize: 12 }}>
                {Array.from({ length: 6 }).map((_, i) => <span key={i} style={{ opacity: i < monster.stars ? 1 : 0.18 }}>★</span>)}
              </div>
              <span style={{ color: M.fgMute, fontSize: 11 }}>·</span>
              <span style={{ fontSize: 11.5, color: el.color, fontWeight: 600 }}>{el.label}</span>
              <span style={{ color: M.fgMute, fontSize: 11 }}>·</span>
              <span style={{ fontSize: 11.5, color: M.fgDim, fontFamily: 'JetBrains Mono' }}>lv{monster.level}</span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 9, color: M.fgMute, letterSpacing: 1, fontWeight: 700, textTransform: 'uppercase' }}>Eff. moyenne</div>
              <div style={{ fontSize: 22, fontFamily: 'JetBrains Mono', fontWeight: 700, color: avgEff > 85 ? '#5dd39e' : M.accent, lineHeight: 1 }}>{avgEff.toFixed(1)}%</div>
            </div>
            <button style={{
              padding: '10px 16px', border: 'none', borderRadius: 10,
              background: `linear-gradient(180deg, ${M.accent}, ${M.accent2})`,
              color: '#fff', fontSize: 12.5, fontWeight: 600, cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 8,
              boxShadow: `0 8px 20px -8px ${M.accent}`,
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2l2 6 6 2-6 2-2 6-2-6-6-2 6-2z"/>
              </svg>
              Optimiser
            </button>
            <button onClick={onClose} style={{
              width: 34, height: 34, border: `1px solid ${M.border}`, borderRadius: 8,
              background: 'transparent', color: M.fgDim, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 18,
            }}>×</button>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ padding: '0 24px', display: 'flex', gap: 4, borderBottom: `1px solid ${M.border}` }}>
          {[{k:'runes',l:'Runes équipées'},{k:'stats',l:'Stats'},{k:'skills',l:'Skills'}].map(t => (
            <div key={t.k} onClick={() => setTab(t.k)} style={{
              padding: '12px 16px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
              color: tab === t.k ? M.accent : M.fgDim,
              borderBottom: `2px solid ${tab === t.k ? M.accent : 'transparent'}`,
              marginBottom: -1,
            }}>{t.l}</div>
          ))}
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          {tab === 'runes' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 14 }}>
                <div>
                  <div style={{ fontSize: 10, color: M.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase' }}>6 slots</div>
                  <div style={{ fontSize: 14, color: M.fg, fontWeight: 600, marginTop: 2 }}>
                    {equipped.length}/6 équipées · sets principaux : {[...new Set(equipped.map(r => r.set))].slice(0, 3).join(' + ') || '—'}
                  </div>
                </div>
                <div style={{ fontSize: 11, color: M.fgDim }}>Click une rune pour voir ses détails complets</div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                {runes.map(r => (
                  <div key={r.slot} style={{ opacity: r.slot <= equipped.length ? 1 : 0.3 }}>
                    {r.slot <= equipped.length ? (
                      <RuneSlotCard rune={r} M={M} onClick={() => setSelectedSlot(r.slot)} selected={selectedSlot === r.slot}/>
                    ) : (
                      <div style={{
                        padding: 14, borderRadius: 12,
                        border: `1px dashed ${M.border}`,
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        minHeight: 180, gap: 8,
                      }}>
                        <RuneHexPlaceholder slot={r.slot} grade={0} size={40} color={M.fgMute}/>
                        <div style={{ fontSize: 11, color: M.fgMute, fontWeight: 600 }}>Slot {r.slot} vide</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === 'stats' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '70px 1fr 70px 70px', gap: 12, padding: '0 0 8px',
                fontSize: 9, color: M.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase' }}>
                <span>Stat</span><span>Contribution runes</span><span style={{ textAlign: 'right' }}>Base</span><span style={{ textAlign: 'right' }}>Total</span>
              </div>
              {runedStats.map((s, i) => (
                <StatRow key={s.k} label={s.k} base={s.base} total={s.total} M={M} highlight={s.k === 'SPD'}/>
              ))}
              <div style={{ marginTop: 16, padding: 14, borderRadius: 10, background: M.accentDim, border: `1px solid ${M.accent}33` }}>
                <div style={{ fontSize: 10, color: M.accent, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 4 }}>Analyse</div>
                <div style={{ fontSize: 12, color: M.fg, lineHeight: 1.5 }}>
                  SPD élevée et CRI R correcte, mais ACC insuffisante pour du contenu endgame (objectif &gt; 55%). ATK% pourrait être optimisée sur le slot 2.
                </div>
              </div>
            </div>
          )}

          {tab === 'skills' && (
            <div>
              {skills.map(sk => <SkillRow key={sk.n} skill={sk} M={M}/>)}
              <div style={{ marginTop: 16, padding: 14, borderRadius: 10, background: 'rgba(255,255,255,0.03)', border: `1px solid ${M.border}` }}>
                <div style={{ fontSize: 10, color: M.fgMute, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 }}>Passif</div>
                <div style={{ fontSize: 12, color: M.fgDim, lineHeight: 1.5 }}>
                  Lorsqu'un allié est touché par une attaque critique, réduit la jauge d'ATB de l'attaquant de 20%. Ignore les effets de type barrière.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

window.MonsterDetailModal = MonsterDetailModal;
