// Exercise browser connection lifecycle with a fake room; no WebRTC or token needed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { test } = require('node:test');
const html = fs.readFileSync('orb/index.html', 'utf8');
const connectionCode = html.slice(html.indexOf('    // ── LiveKit connection'), html.indexOf('  })();'));

function harness({
  connectError = false,
  deferConnect = false,
  micError = false,
  configured = true,
} = {}) {
  const rooms = [];
  const windowEvents = {};
  const releasedAnalysers = [];
  class Room {
    constructor(options) {
      rooms.push(this);
      this.options = options;
      this.handlers = {};
      this.disconnected = false;
      this.disposed = false;
      this.disposeCalls = 0;
      this.micEnabled = false;
      this.micStopped = false;
      this.localParticipant = {
        identity: 'visitor',
        setMicrophoneEnabled: async (enabled) => {
          if (enabled && micError) throw Error('microphone denied');
          this.micEnabled = enabled;
        },
        getTrackPublication: () => undefined,
      };
    }
    on(event, listener) { this.handlers[event] = listener; return this; }
    async startAudio() {}
    async connect() {
      if (connectError) throw Error('token expired');
      if (deferConnect) {
        await new Promise((resolve) => { this.resolveConnect = resolve; });
      }
    }
    async dispose() {
      this.disposeCalls += 1;
      this.disposed = true;
      this.disconnected = true;
      if (this.micEnabled) {
        this.micEnabled = false;
        this.micStopped = true;
      }
      this.handlers.disconnected?.();
    }
  }
  const context = vm.createContext({
    configured,
    cfg: { URL: 'wss://test.livekit.cloud', TOKEN: 'test-token' },
    window: {
      addEventListener(event, listener) { windowEvents[event] = listener; },
      LivekitClient: {
        Room,
        RoomEvent: { TrackSubscribed: 'subscribed', TrackUnsubscribed: 'unsubscribed',
                     ActiveSpeakersChanged: 'speakers', Disconnected: 'disconnected' },
        Track: { Kind: { Audio: 'audio' }, Source: { Microphone: 'mic' } },
      },
    },
    orbButton: { addEventListener() {} },
    state: 'idle',
    setState(next) { context.state = next; },
    ensureAudioCtx() {},
    audioCtx: { state: 'running' },
    localAnalyser: null, agentAnalyser: null,
    makeAnalyser() { return {}; },
    releaseAnalyser(analyser) { if (analyser) releasedAnalysers.push(analyser); },
    closeAudioContext() { context.audioCtx = null; },
    MediaStream: class {},
    document: { body: { appendChild() {} } },
    console: { warn() {}, error() {} },
  });
  vm.runInContext(connectionCode, context);
  return { context, releasedAnalysers, rooms, windowEvents };
}

test('pins the rehearsed LiveKit browser SDK', () => {
  assert.match(html, /livekit-client@2\.24\.0\/dist\/livekit-client\.umd\.min\.js/);
});

test('low-power and reduced-motion modes use the static render path', () => {
  assert.match(html, /prefers-reduced-motion: reduce/);
  assert.match(html, /get\('low-power'\) === '1'/);
  assert.match(html, /Static mode has no continuous animation loop/);
  assert.match(html, /if \(lowPowerMode\) requestOrbRender\(\);\s*else startRendering\(\);/);
});

test('invalid configuration never attempts a connection', async () => {
  const { context, rooms } = harness({ configured: false });
  await context.startConversation();
  assert.equal(rooms.length, 0);
});

for (const reason of ['connectError', 'micError']) {
  test(`${reason} closes the connection and permits retry`, async () => {
    const { context, rooms } = harness({ [reason]: true });
    await context.startConversation();
    assert.equal(context.state, 'error');
    assert.equal(rooms[0].disconnected, true);
    assert.equal(rooms[0].disposed, true);
    assert.equal(rooms[0].disposeCalls, 1);
    await context.startConversation();
    assert.equal(rooms.length, 2);
    assert.equal(rooms[1].disconnected, true);
    assert.equal(rooms[1].disposeCalls, 1);
  });
}

test('stop removes remote audio and releases the room', async () => {
  const { context, rooms } = harness();
  await context.startConversation();
  assert.equal(context.state, 'listening');
  let removed = false;
  let detached = false;
  const track = {
    kind: 'audio', mediaStreamTrack: {},
    attach: () => ({ style: {}, remove() { removed = true; } }),
    detach() { detached = true; },
  };
  rooms[0].handlers.subscribed(track);
  await context.endConversation();
  assert.equal(context.state, 'idle');
  assert.equal(rooms[0].disconnected, true);
  assert.equal(rooms[0].disposed, true);
  assert.equal(rooms[0].disposeCalls, 1);
  assert.equal(rooms[0].micStopped, true);
  assert.equal(removed, true);
  assert.equal(detached, true);
  await context.startConversation();
  assert.equal(rooms.length, 2);
});

test('a duplicate subscription attaches one audio element', async () => {
  const { context, rooms } = harness();
  await context.startConversation();
  let attaches = 0;
  let detaches = 0;
  const track = {
    kind: 'audio', mediaStreamTrack: {},
    attach: () => { attaches += 1; return { style: {}, remove() {} }; },
    detach() { detaches += 1; },
  };
  rooms[0].handlers.subscribed(track);
  rooms[0].handlers.subscribed(track);
  await context.endConversation();
  assert.equal(attaches, 1);
  assert.equal(detaches, 1);
});

test('unexpected disconnect enters retry state', async () => {
  const { context, rooms } = harness();
  await context.startConversation();
  rooms[0].handlers.disconnected();
  assert.equal(context.state, 'error');
  await new Promise(setImmediate);
  assert.equal(rooms[0].disposeCalls, 1);
  await context.startConversation();
  assert.equal(rooms.length, 2);
});

test('stopping while connect is pending disposes once and stays idle', async () => {
  const { context, rooms } = harness({ deferConnect: true });
  const starting = context.startConversation();
  await new Promise(setImmediate);
  assert.equal(rooms.length, 1);
  await context.endConversation();
  assert.equal(context.state, 'idle');
  assert.equal(rooms[0].disposeCalls, 1);
  rooms[0].resolveConnect();
  await starting;
  assert.equal(context.state, 'idle');
  assert.equal(rooms[0].disposeCalls, 1);
});

test('pagehide disposes the active room and releases the microphone', async () => {
  const { context, rooms, windowEvents } = harness();
  await context.startConversation();
  windowEvents.pagehide();
  await new Promise(setImmediate);
  assert.equal(rooms[0].disposeCalls, 1);
  assert.equal(rooms[0].micStopped, true);
  await context.startConversation();
  assert.equal(rooms.length, 2);
});
