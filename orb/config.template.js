// orb config — copy to config.js and fill in your values.
//
// SETUP
//   cp config.template.js config.js
//   # then edit config.js
//
// config.js is gitignored. Never commit a real token to version control.

const CONFIG = {
  LIVEKIT: {
    // Your LiveKit Cloud project URL. Same one your agent's .env uses.
    //   $ grep LIVEKIT_URL ../.env
    URL: 'wss://YOUR-PROJECT.livekit.cloud',

    // A short-lived LiveKit access token. Generate one:
    //   $ lk token create \
    //       --room heartbyte-orb \
    //       --identity orb-visitor \
    //       --valid-for 24h
    // Paste the eyJ... string here.
    TOKEN: 'YOUR_LIVEKIT_TOKEN',

    // The LiveKit room the orb joins. The agent dispatches to this room
    // automatically when a participant joins. Keep as-is unless you also
    // change the agent's expected room.
    ROOM: 'heartbyte-orb',
  },
};

Object.freeze(CONFIG);
Object.freeze(CONFIG.LIVEKIT);
