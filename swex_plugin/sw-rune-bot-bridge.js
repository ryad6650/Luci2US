/**
 * SW Exporter Plugin – Rune Bot Bridge
 *
 * Writes a JSON file into ./drops/ for each relevant in-game event
 * so that Luci2US can pick it up via SWEXBridge.
 *
 * Compatible with https://github.com/Xzandro/sw-exporter
 */

const fs = require('fs');
const path = require('path');

const DROPS_DIR = path.join(__dirname, '..', 'rune-bot-drops');

const WATCHED_EVENTS = [
  'BattleDungeonResult_v2',
  'BattleScenarioResult',
  'BattleDimensionHoleDungeonResult_v2',
  'UpgradeRune',
  'BuyGuildShopRune',
  'AmplifyRune',
  'ConfirmRune',
];

const PROFILE_EVENTS = ['HubUserLogin', 'GuestLogin'];

/**
 * Extract the rune object from various SWEX event payloads.
 */
function extractRune(command, request, response) {
  if (command === 'UpgradeRune' || command === 'AmplifyRune' || command === 'ConfirmRune') {
    return response.rune || null;
  }

  // Battle results – rune rewards
  const reward = response.reward;
  if (reward && reward.crate && reward.crate.rune) {
    return reward.crate.rune;
  }

  // Some payloads nest under changed_item_list
  if (response.changed_item_list) {
    const items = response.changed_item_list;
    if (Array.isArray(items)) {
      for (const item of items) {
        if (item.type === 8 && item.info) return item.info;
      }
    }
  }

  if (response.rune) return response.rune;

  return null;
}

module.exports = {
  defaultConfig: {
    enabled: true,
  },

  pluginName: 'RuneBotBridge',
  pluginDescription: 'Writes rune drops to JSON files for Luci2US bot integration.',

  init(proxy) {
    // Ensure the drops directory exists
    if (!fs.existsSync(DROPS_DIR)) {
      fs.mkdirSync(DROPS_DIR, { recursive: true });
    }

    for (const event of WATCHED_EVENTS) {
      proxy.on(event, (request, response) => {
        const rune = extractRune(event, request, response);
        if (!rune) return;

        const payload = {
          event,
          wizard_id: request.wizard_id || response.wizard_id || null,
          ...rune,
        };

        const timestamp = Date.now();
        const filename = `${event}_${timestamp}.json`;
        const filepath = path.join(DROPS_DIR, filename);

        fs.writeFileSync(filepath, JSON.stringify(payload, null, 2), 'utf-8');
      });
    }

    for (const event of PROFILE_EVENTS) {
      proxy.on(event, (request, response) => {
        const timestamp = Date.now();
        const filename = `profile_${timestamp}.json`;
        const filepath = path.join(DROPS_DIR, filename);

        fs.writeFileSync(filepath, JSON.stringify(response, null, 2), 'utf-8');
      });
    }
  },
};
