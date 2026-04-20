/**
 * SW Exporter Plugin – Rune Bot Bridge
 *
 * Writes a JSON file into <filesPath>/rune-bot-drops/ for each relevant
 * in-game event so that Luci2US can pick it up via SWEXBridge.
 *
 * Compatible with https://github.com/Xzandro/sw-exporter
 */

const fs = require('fs');
const path = require('path');

const DROPS_DIR = path.join(__dirname, '..', 'rune-bot-drops');

// Map: command name -> { kind: 'drop'|'upgrade', extract: (resp) => Rune[] }
// Event names and extraction paths mirror the builtin rune-drop-efficiency.js.
const HANDLERS = {
  BattleDungeonResult: {
    kind: 'drop',
    extract: (resp) => {
      if (resp.win_lose !== 1) return [];
      const r = resp.reward && resp.reward.crate && resp.reward.crate.rune;
      return r ? [r] : [];
    },
  },
  BattleDungeonResult_V2: {
    kind: 'drop',
    extract: (resp) => {
      if (resp.win_lose !== 1) return [];
      const items = resp.changed_item_list || [];
      return items.filter((i) => i.type === 8 && i.info).map((i) => i.info);
    },
  },
  BattleScenarioResult: {
    kind: 'drop',
    extract: (resp) => {
      if (resp.win_lose !== 1) return [];
      const r = resp.reward && resp.reward.crate && resp.reward.crate.rune;
      return r ? [r] : [];
    },
  },
  BattleDimensionHoleDungeonResult: {
    kind: 'drop',
    extract: (resp) => {
      if (resp.win_lose !== 1) return [];
      const r = resp.reward && resp.reward.crate && resp.reward.crate.rune;
      return r ? [r] : [];
    },
  },
  BattleRiftDungeonResult: {
    kind: 'drop',
    extract: (resp) => {
      const items = resp.item_list || [];
      return items.filter((i) => i.type === 8 && i.info).map((i) => i.info);
    },
  },
  BattleWorldBossResult: {
    kind: 'drop',
    extract: (resp) => {
      const runes = resp.reward && resp.reward.crate && resp.reward.crate.runes;
      return runes || [];
    },
  },
  BuyShopItem: {
    kind: 'drop',
    extract: (resp) => {
      const runes = resp.reward && resp.reward.crate && resp.reward.crate.runes;
      return runes || [];
    },
  },
  BuyBlackMarketItem: {
    kind: 'drop',
    extract: (resp) => resp.runes || [],
  },
  BuyGuildBlackMarketItem: {
    kind: 'drop',
    extract: (resp) => resp.runes || [],
  },
  ConfirmRune: {
    kind: 'drop',
    extract: (resp) => (resp.rune ? [resp.rune] : []),
  },
  UpgradeRune: {
    kind: 'upgrade',
    extract: (resp) => (resp.rune ? [resp.rune] : []),
  },
  UpgradeRune_v2: {
    kind: 'upgrade',
    extract: (resp) => (resp.rune ? [resp.rune] : []),
  },
  AmplifyRune: {
    kind: 'upgrade',
    extract: (resp) => (resp.rune ? [resp.rune] : []),
  },
  AmplifyRune_v2: {
    kind: 'upgrade',
    extract: (resp) => (resp.rune ? [resp.rune] : []),
  },
  ConvertRune: {
    kind: 'upgrade',
    extract: (resp) => (resp.rune ? [resp.rune] : []),
  },
  ConvertRune_v2: {
    kind: 'upgrade',
    extract: (resp) => (resp.rune ? [resp.rune] : []),
  },
  RevalueRune: {
    kind: 'upgrade',
    extract: (resp) => (resp.rune ? [resp.rune] : []),
  },
};

const PROFILE_EVENTS = ['HubUserLogin', 'GuestLogin'];

module.exports = {
  defaultConfig: { enabled: true },

  pluginName: 'RuneBotBridge',
  pluginDescription: 'Writes rune drops to JSON files for Luci2US bot integration.',

  init(proxy) {
    if (!fs.existsSync(DROPS_DIR)) {
      fs.mkdirSync(DROPS_DIR, { recursive: true });
    }

    const log = (type, message) => {
      if (proxy && typeof proxy.log === 'function') {
        proxy.log({ type, source: 'plugin', name: 'RuneBotBridge', message });
      }
    };

    log('success', `initialized, drops -> ${DROPS_DIR}`);

    proxy.on('apiCommand', (req, resp) => {
      const command = req && req.command;
      const handler = HANDLERS[command];
      if (!handler) return;

      log('debug', `event received: ${command}`);

      let runes;
      try {
        runes = handler.extract(resp) || [];
      } catch (e) {
        log('error', `extract failed for ${command}: ${e.message}`);
        return;
      }

      if (runes.length === 0) {
        const ts = Date.now();
        const dumpPath = path.join(DROPS_DIR, `debug_${command}_${ts}.json`);
        try {
          fs.writeFileSync(
            dumpPath,
            JSON.stringify({ event: command, request: req, response: resp }, null, 2),
            'utf-8',
          );
          log('warning', `no rune extracted for ${command}, dumped ${path.basename(dumpPath)}`);
        } catch (e) {
          log('error', `failed to dump ${command}: ${e.message}`);
        }
        return;
      }

      runes.forEach((rune, idx) => {
        const ts = Date.now();
        const filename = `${command}_${ts}_${idx}.json`;
        const filepath = path.join(DROPS_DIR, filename);
        const payload = {
          event: command,
          kind: handler.kind,
          wizard_id: (req && req.wizard_id) || (resp && resp.wizard_id) || null,
          ...rune,
        };
        try {
          fs.writeFileSync(filepath, JSON.stringify(payload, null, 2), 'utf-8');
          log('success', `wrote ${filename}`);
        } catch (e) {
          log('error', `failed to write ${filename}: ${e.message}`);
        }
      });
    });

    for (const event of PROFILE_EVENTS) {
      proxy.on(event, (request, response) => {
        const timestamp = Date.now();
        const filename = `profile_${timestamp}.json`;
        const filepath = path.join(DROPS_DIR, filename);
        try {
          fs.writeFileSync(filepath, JSON.stringify(response, null, 2), 'utf-8');
          log('success', `wrote ${filename}`);
        } catch (e) {
          log('error', `failed to write ${filename}: ${e.message}`);
        }
      });
    }
  },
};
