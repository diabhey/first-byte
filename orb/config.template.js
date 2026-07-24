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
    //   $ lk token create --join \
    //       --room heartbyte-orb \
    //       --identity orb-visitor \
    //       --valid-for 1h
    // Paste the eyJ... string here.
    TOKEN: 'YOUR_LIVEKIT_TOKEN',
  },
};

Object.freeze(CONFIG);
Object.freeze(CONFIG.LIVEKIT);
