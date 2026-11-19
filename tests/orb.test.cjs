// Exercise browser connection lifecycle with a fake room; no WebRTC or token needed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { test } = require('node:test');
const html = fs.readFileSync('orb/index.html', 'utf8');
const connectionCode = html.slice(html.indexOf('    // ── LiveKit connection'), html.indexOf('  })();'));

function harness({ connectError = false, micError = false, configured = true } = {}) {
  const rooms = [];
  class Room {
    constructor() {
      rooms.push(this);
      this.handlers = {};
      this.disconnected = false;
      this.localParticipant = {
        identity: 'visitor',
        setMicrophoneEnabled: async () => { if (micError) throw Error('microphone denied'); },
        getTrackPublication: () => undefined,
      };
    }
    on(event, listener) { this.handlers[event] = listener; return this; }
    async startAudio() {}
    async connect() { if (connectError) throw Error('token expired'); }
    async disconnect() { this.disconnected = true; this.handlers.disconnected?.(); }
  }
  const context = vm.createContext({
    configured,
    cfg: { URL: 'wss://test.livekit.cloud', TOKEN: 'test-token' },
    window: { LivekitClient: {
      Room,
      RoomEvent: { TrackSubscribed: 'subscribed', TrackUnsubscribed: 'unsubscribed',
                   ActiveSpeakersChanged: 'speakers', Disconnected: 'disconnected' },
      Track: { Kind: { Audio: 'audio' }, Source: { Microphone: 'mic' } },
    } },
    orbButton: { addEventListener() {} },
    state: 'idle',
    setState(next) { context.state = next; },
    ensureAudioCtx() {},
    audioCtx: { state: 'running' },
    localAnalyser: null, agentAnalyser: null,
    makeAnalyser() { return {}; },
    MediaStream: class {},
    document: { body: { appendChild() {} } },
    console: { warn() {}, error() {} },
  });
  vm.runInContext(connectionCode, context);
  return { context, rooms };
}

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
    await context.startConversation();
    assert.equal(rooms.length, 2);
    assert.equal(rooms[1].disconnected, true);
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
  assert.equal(removed, true);
  assert.equal(detached, true);
  await context.startConversation();
  assert.equal(rooms.length, 2);
});

test('unexpected disconnect enters retry state', async () => {
  const { context, rooms } = harness();
  await context.startConversation();
  rooms[0].handlers.disconnected();
  assert.equal(context.state, 'error');
  await context.startConversation();
  assert.equal(rooms.length, 2);
});
