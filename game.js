/*
  game.js — "Super 3Sheets" (NES theme bonus stage)

  A tiny single-level side-scroller drawn on a 256x240 canvas.
  No images or libraries: every sprite is a pixel map below.

  Controls: ←/→ or A/D run · Z / Space / ↑ jump · X / Shift sprint
            Enter or click to start / resume. Touch buttons on phones.

  Power-ups (from the site copy):
    $ coin ........ data points
    Dashboard ..... "clarity": break bricks + survive one hit
    Automation .... "updates that send themselves": short invincibility
  Enemies: Overtime clocks, Rogue Invoices. Pits = visibility gaps.
*/

(() => {
  'use strict';

  const canvas = document.getElementById('game-canvas');
  if (!canvas) return;
  const W = 256, H = 240, T = 16;

  // Everything is drawn at native NES resolution into this buffer, then
  // copied to the visible canvas at a whole-number scale (see fit()).
  const view = canvas.getContext('2d');
  const buffer = document.createElement('canvas');
  buffer.width = W; buffer.height = H;
  const ctx = buffer.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  const FONT = '8px "Press Start 2P", monospace';

  const C = {
    sky: '#5c94fc', black: '#000000', white: '#fcfcfc', grey: '#bcbcbc', greyDark: '#7c7c7c',
    brick: '#c84c0c', brickDark: '#881400', brickLight: '#fc9838', tan: '#fcbcb0',
    gold: '#f8b800', goldDark: '#ac7c00', orange: '#fc9838',
    green: '#00a800', greenLight: '#b8f818', greenDark: '#005800',
    red: '#d82800', skin: '#fcbcb0', hair: '#7c3c00', lens: '#a4e4fc',
    trousers: '#50507c', blue: '#0058f8'
  };

  /* ================================================================ SPRITES */

  function sprite(rows, map) {
    const w = Math.max(...rows.map(r => r.length));
    const c = document.createElement('canvas');
    c.width = w; c.height = rows.length;
    const g = c.getContext('2d');
    rows.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        const col = map[row[x]];
        if (col) { g.fillStyle = col; g.fillRect(x, y, 1, 1); }
      }
    });
    return c;
  }

  function flipped(src) {
    const c = document.createElement('canvas');
    c.width = src.width; c.height = src.height;
    const g = c.getContext('2d');
    g.translate(src.width, 0); g.scale(-1, 1); g.drawImage(src, 0, 0);
    return c;
  }

  // Little businessman ("Chibi Analyst"): big head, round glasses,
  // rolled-sleeve white shirt, navy trousers. No tie, no jacket. 16x16.
  const HEAD = [
    '.....hhhhhh.....',
    '...hhhhhhhhhh...',
    '..hhhhhhhhhhhh..',
    '..hhhsssssssh...',
    '..hhkkkkskkkk...',
    '..hsklllkklllk..',
    '..hSkkkkskkkks..',
    '...ssssssSsss...',
    '....sssskkss....',
  ];
  const BODY = {
    stand: ['.....wwbbww.....', '....wwwwwwww....', '...swwwwwwwws...', '....wwwwwwww....', '....tttttttt....', '....ttt..ttt....', '...oooo..oooo...'],
    run1:  ['.....wwbbww.....', '...swwwwwwww....', '....wwwwwwwwws..', '....wwwwwwww....', '...tttttttttt...', '..ttt......ttt..', '.ooo........ooo.'],
    run2:  ['.....wwbbww.....', '....wwwwwwww....', '....swwwwwws....', '....wwwwwwww....', '.....tttttt.....', '......tttt......', '.....ooooo......'],
    jump:  ['.....wwbbww.sss.', '....wwwwwwwws...', '...swwwwwwww....', '....wwwwwwww....', '...ttttttttt....', '..ttt....ttt....', '..oo......ooo...'],
  };

  // Afro puff, gold earring, no glasses
  const HEAD_PUFF = [
    '....hhhhhhh.....',
    '...hhhhhhhhh....',
    '..hhhhhhhhhhh...',
    '..hhhhhhhhhhh...',
    '..hhhsssssssh...',
    '..hhssksssksS...',
    '..hySsssssssS...',
    '...ssssssSss....',
    '....sssrrss.....',
  ];

  // Hijab, no glasses
  const HEAD_HIJAB = [
    '.....hhhhhh.....',
    '...hhhhhhhhhh...',
    '..hhhhhhhhhhhh..',
    '..hhhhsssssshh..',
    '..hhhssksssksh..',
    '..hhhsssssssSh..',
    '..hhhsSssssSsh..',
    '..hhhhsssrrshh..',
    '..hhhhhhhhhhhh..',
  ];

  // Non-binary: lilac swoop over a shaved side (H), earring, no glasses
  const HEAD_SWOOP = [
    '......hhhhhh....',
    '....hhhhhhhhhh..',
    '...hhhhhhhhhhhh.',
    '..HHHhsssssss...',
    '..HHssksssksS...',
    '..HHsssssssss...',
    '..HSysssssSss...',
    '...ssssssSss....',
    '....sssskss.....',
  ];

  // Wheelchair user: short black hair, round glasses
  const HEAD_CHAIR = [
    '.....hhhhhh.....',
    '....hhhhhhhh....',
    '...hhhhhhhhhh...',
    '...hhsssssssh...',
    '...hkkkkskkkk...',
    '...sklllkklllk..',
    '...sSkkkskkkks..',
    '....sssssSss....',
    '.....sssskss....',
  ];

  // Seated in a wheelchair: big wheel (g rim, G spokes), chair back,
  // footrest. Spokes turn between the two run frames.
  const CHAIR_BODY = {
    stand: ['.kk..wwbbww.....', '..k.ggggwwwws...', '..kgwwGwgwwss...', '..kgttGGgtttt...', '..kgtGttg...tt..', '..kgGtttg..ktt..', '...kggggk.kkooo.'],
    run1:  ['.kk..wwbbww.....', '..k.ggggwwwws...', '..kgwGwwgwwss...', '..kgttGGgtttt...', '..kgtttGg...tt..', '..kgtttGg..ktt..', '...kggggk.kkooo.'],
    run2:  ['.kk..wwbbww.....', '..k.ggggwwwws...', '..kgGwwwgwwss...', '..kgGGGGgtttt...', '..kgttttg...tt..', '..kgtttGg..ktt..', '...kggggk.kkooo.'],
    jump:  ['.kk..wwbbww.ss..', '..k.ggggwwwws...', '..kgwwGwgwww....', '..kgttGGgtttt...', '..kgtGttg...tt..', '..kgGtttg..ktt..', '...kggggk.kkooo.'],
  };

  // The cast (5). Skin tones range light to deep; men, women and a
  // non-binary character, glasses/no glasses, a hijab, a wheelchair user.
  const CHARACTERS = {
    him:   { head: HEAD,       hair: C.hair,    skin: '#fcbcb0', shadeSkin: '#e09470', shirt: C.white,   shade: C.grey },
    puff:  { head: HEAD_PUFF,  hair: '#201008', skin: '#7c4a2c', shadeSkin: '#5c3018', shirt: '#00a8a8', shade: '#005858' },
    hijab: { head: HEAD_HIJAB, hair: '#583880', skin: '#b87050', shadeSkin: '#8c4c30', shirt: '#fce0a8', shade: '#c8a060' },
    swoop: { head: HEAD_SWOOP, hair: '#b8a0f8', hairShaved: '#5c4c7c', skin: '#fcc8a0', shadeSkin: '#e0a07c', shirt: '#3c3c3c', shade: '#181818' },
    chair: { head: HEAD_CHAIR, hair: '#101010', skin: '#9c5c38', shadeSkin: '#744024', shirt: '#58d854', shade: '#00a800', body: CHAIR_BODY },
  };
  const ROSTER = Object.keys(CHARACTERS);

  function playerPalette(ch, shirt, shade, trousers) {
    return {
      h: ch.hair, H: ch.hairShaved || ch.hair, s: ch.skin, S: ch.shadeSkin, y: C.gold,
      k: C.black, l: C.lens, r: C.red, w: shirt, b: shade, t: trousers, o: C.black,
      g: C.grey, G: '#7c7c7c',
    };
  }

  // Big (Clarity) version: same head, taller body — torso and legs rows
  // doubled, like Mario after a mushroom. 21 rows tall. The wheelchair
  // user grows taller in the torso so the wheel stays round.
  const bigBody = r => [r[0], r[1], r[1], r[2], r[2], r[3], r[3], r[4], r[5], r[5], r[5], r[6]];
  const bigChair = r => [r[0], r[0], r[0], r[0], r[0], r[0], r[1], r[2], r[3], r[4], r[5], r[6]];
  const SMALL_H = 15, BIG_H = 20;

  const PLAYER = {}, PLAYER_BIG = {};
  for (const [id, ch] of Object.entries(CHARACTERS)) {
    const body = ch.body || BODY;
    const grow = ch.body ? bigChair : bigBody;
    const palettes = {
      normal: playerPalette(ch, ch.shirt, ch.shade, '#3c3c7c'),
      star1:  playerPalette(ch, C.gold, C.red, C.black),
      star2:  playerPalette(ch, C.greenLight, C.green, C.red),
      star3:  playerPalette(ch, C.orange, C.brickDark, C.blue),
    };
    PLAYER[id] = {}; PLAYER_BIG[id] = {};
    for (const [pal, map] of Object.entries(palettes)) {
      PLAYER[id][pal] = {}; PLAYER_BIG[id][pal] = {};
      for (const f of Object.keys(BODY)) {
        const r = sprite([...ch.head, ...body[f]], map);
        PLAYER[id][pal][f] = { r, l: flipped(r) };
        const b = sprite([...ch.head, ...grow(body[f])], map);
        PLAYER_BIG[id][pal][f] = { r: b, l: flipped(b) };
      }
    }
  }

  // Player name (shown top-left). Typed into the NAME box under the game.
  const nameInput = document.getElementById('player-name');
  let playerName = 'PLAYER';
  const cleanName = v => (v || '').toUpperCase().replace(/[^A-Z0-9 .!-]/g, '').trim().slice(0, 8);
  try { playerName = cleanName(localStorage.getItem('s3-name')) || 'PLAYER'; } catch (e) { /* storage blocked */ }

  let character = 'him';
  try { const saved = localStorage.getItem('s3-character'); if (CHARACTERS[saved]) character = saved; } catch (e) { /* storage blocked */ }

  function cycleCharacter(dir) {
    const i = ROSTER.indexOf(character);
    setCharacter(ROSTER[(i + dir + ROSTER.length) % ROSTER.length]);
  }

  function setCharacter(id) {
    character = id;
    try { localStorage.setItem('s3-character', id); } catch (e) { /* ignore */ }
  }

  const CLOCK_TOP = [
    '....rrrrrrrr....',
    '..rrwwwwwwwwrr..',
    '.rwwwwwkwwwwwwr.',
    '.rwwwwwkwwwwwwr.',
    'rwwwwwwkwwwwwwwr',
    'rwwwwwwkwwwwwwwr',
    'rwwwwwwkkkkkwwwr',
    'rwwwwwwwwwwwwwwr',
    'rwwkkwwwwwwkkwwr',
    '.rwwwkwwwwkwwwr.',
    '.rwwwwwwwwwwwwr.',
    '..rrwwwwwwwwrr..',
    '....rrrrrrrr....',
  ];
  const CLOCK_MAP = { r: C.red, w: C.white, k: C.black };
  const CLOCK = [
    sprite([...CLOCK_TOP, '...kk......kk...', '..kkkk....kkkk..', '..kkkk....kkkk..'], CLOCK_MAP),
    sprite([...CLOCK_TOP, '....kk....kk....', '...kkkk..kkkk...', '...kkkk..kkkk...'], CLOCK_MAP),
  ];

  const INVOICE_TOP = [
    '..kkkkkkkkkk....',
    '..kwwwwwwwwwk...',
    '..kwkkwwkkwwwk..',
    '..kwwkwwkwwwwwk.',
    '..kwwwwwwwwwwwk.',
    '..kwbbbbbbbbwwk.',
    '..kwwwwwwwwwwwk.',
    '..kwbbbbbbwwwwk.',
    '..kwwwwwwwwwwwk.',
    '..kwwwwrrrwwwwk.',
    '..kwwwwrwwwwwwk.',
    '..kwwwwrrrwwwwk.',
    '..kwwwwwwrwwwwk.',
    '..kwwwwrrrwwwwk.',
    '..kkkkkkkkkkkkk.',
  ];
  const INVOICE_MAP = { k: C.black, w: C.white, b: C.grey, r: C.red };
  const INVOICE = [
    sprite([...INVOICE_TOP, '...kk......kk...'], INVOICE_MAP),
    sprite([...INVOICE_TOP, '....kk....kk....'], INVOICE_MAP),
  ];

  const COIN = sprite([
    '...oooo...',
    '..oyyyyo..',
    '.oyyddyyo.',
    '.oyddddyo.',
    '.oydyyyyo.',
    '.oyddddyo.',
    '.oyyyydyo.',
    '.oyddddyo.',
    '.oyyddyyo.',
    '..oyyyyo..',
    '...oooo...',
  ], { o: C.goldDark, y: C.gold, d: C.brickDark });

  const DASHBOARD = sprite([
    'kkkkkkkkkkkkkkkk',
    'kwwwwwwwwwwwwwwk',
    'kwwwwwwwwwwggwwk',
    'kwwwwwwwwwwggwwk',
    'kwwwwwwggwwggwwk',
    'kwwwwwwggwwggwwk',
    'kwwggwwggwwggwwk',
    'kwwggwwggwwggwwk',
    'kwwggwwggwwggwwk',
    'kwwwwwwwwwwwwwwk',
    'kkkkkkkkkkkkkkkk',
    '......kkkk......',
    '......kkkk......',
    '....kkkkkkkk....',
  ], { k: C.black, w: C.white, g: C.green });

  const BOLT = sprite([
    '........oooooo..',
    '.......oyyyyo...',
    '......oyyyyo....',
    '.....oyyyyo.....',
    '....oyyyyooooo..',
    '...oyyyyyyyyo...',
    '...oooooyyyo....',
    '.......oyyo.....',
    '......oyyo......',
    '.....oyyo.......',
    '....oyo.........',
    '...oo...........',
  ], { o: C.brickDark, y: C.gold });

  /* ================================================================ TILES */

  function tile(draw) {
    const c = document.createElement('canvas');
    c.width = T; c.height = T;
    draw(c.getContext('2d'));
    return c;
  }

  const px = (g, col, x, y, w = 1, h = 1) => { g.fillStyle = col; g.fillRect(x, y, w, h); };

  const TILE = {
    G: tile(g => {
      px(g, C.brick, 0, 0, 16, 16);
      px(g, C.tan, 0, 0, 16, 1); px(g, C.tan, 0, 0, 1, 16);
      px(g, C.black, 15, 0, 1, 16); px(g, C.black, 0, 15, 16, 1);
      px(g, C.black, 8, 1, 1, 7); px(g, C.black, 1, 8, 7, 1);
      px(g, C.tan, 9, 1, 1, 6); px(g, C.black, 4, 9, 1, 6);
    }),
    B: tile(g => {
      px(g, C.brick, 0, 0, 16, 16);
      px(g, C.tan, 0, 0, 16, 1);
      [3, 7, 11, 15].forEach(y => px(g, C.black, 0, y, 16, 1));
      [[7, 0], [15, 0], [3, 4], [11, 4], [7, 8], [15, 8], [3, 12], [11, 12]]
        .forEach(([x, y]) => px(g, C.black, x, y, 1, 3));
    }),
    Q: tile(g => {
      px(g, C.black, 0, 0, 16, 16);
      px(g, C.orange, 0, 0, 15, 15);
      px(g, C.gold, 1, 1, 13, 13);
      [[1, 1], [13, 1], [1, 13], [13, 13]].forEach(([x, y]) => px(g, C.black, x, y));
      // "?"
      const q = ['.kkkk.', 'kk..kk', '....kk', '...kk.', '..kk..', '......', '..kk..'];
      q.forEach((row, y) => [...row].forEach((ch, x) => ch === 'k' && px(g, C.brickDark, 5 + x, 3 + y)));
    }),
    U: tile(g => {
      px(g, C.black, 0, 0, 16, 16);
      px(g, C.brick, 0, 0, 15, 15);
      [[1, 1], [13, 1], [1, 13], [13, 13]].forEach(([x, y]) => px(g, C.black, x, y));
    }),
    S: tile(g => {
      px(g, C.brickDark, 0, 0, 16, 16);
      px(g, C.brick, 1, 1, 14, 14);
      px(g, C.tan, 0, 0, 15, 1); px(g, C.tan, 0, 0, 1, 15);
      px(g, C.black, 15, 0, 1, 16); px(g, C.black, 0, 15, 16, 1);
      px(g, C.brickLight, 3, 3, 10, 10);
      px(g, C.brick, 4, 4, 8, 8);
    }),
    '[': tile(g => {
      px(g, C.black, 0, 0, 16, 16);
      px(g, C.green, 1, 1, 15, 14);
      px(g, C.greenLight, 3, 1, 3, 14);
    }),
    ']': tile(g => {
      px(g, C.black, 0, 0, 16, 16);
      px(g, C.green, 0, 1, 15, 14);
      px(g, C.greenDark, 10, 1, 4, 14);
    }),
    '{': tile(g => {
      px(g, C.black, 2, 0, 14, 16);
      px(g, C.green, 3, 0, 13, 16);
      px(g, C.greenLight, 5, 0, 3, 16);
    }),
    '}': tile(g => {
      px(g, C.black, 0, 0, 14, 16);
      px(g, C.green, 0, 0, 13, 16);
      px(g, C.greenDark, 8, 0, 4, 16);
    }),
  };
  TILE['?'] = TILE.Q; TILE.D = TILE.Q; TILE.A = TILE.Q;

  const SOLID = new Set(['G', 'B', '?', 'D', 'A', 'U', 'S', '[', ']', '{', '}']);

  /* ================================================================ LEVEL */

  const COLS = 88, ROWS = 15;
  const GROUND = 13;
  const FLAG_COL = 77;
  const HQ_COL = 81;
  let map, spawns;

  function buildLevel() {
    map = Array.from({ length: ROWS }, () => Array(COLS).fill('.'));
    spawns = { enemies: [], coins: [] };
    const set = (x, y, c) => { map[y][x] = c; };
    const gaps = [[39, 40], [57, 59]];
    for (let x = 0; x < COLS; x++) {
      if (gaps.some(([a, b]) => x >= a && x <= b)) continue;
      set(x, GROUND, 'G'); set(x, GROUND + 1, 'G');
    }
    const pipe = (x, h) => {
      set(x, GROUND - h, '['); set(x + 1, GROUND - h, ']');
      for (let y = GROUND - h + 1; y < GROUND; y++) { set(x, y, '{'); set(x + 1, y, '}'); }
    };

    // Opening: a coin block, then a row with the Dashboard
    set(10, 9, '?');
    set(15, 9, 'B'); set(16, 9, 'D'); set(17, 9, 'B'); set(18, 9, '?'); set(19, 9, 'B');
    set(17, 5, '?');

    pipe(24, 2);
    pipe(33, 3);

    // Visibility gap #1 with a coin arc
    spawns.coins.push([38, 9], [39, 8], [40, 8], [41, 9]);

    // Brick shelf with the Automation bolt
    for (let x = 44; x <= 48; x++) set(x, 9, 'B');
    set(46, 9, 'A');
    for (let x = 44; x <= 48; x++) spawns.coins.push([x, 6]);

    set(52, 9, '?'); set(53, 9, 'B'); set(54, 9, '?');

    // Staircase up to the finish
    for (let i = 0; i < 4; i++) for (let h = 0; h <= i; h++) set(64 + i, GROUND - 1 - h, 'S');
    for (let h = 0; h < 4; h++) set(68, GROUND - 1 - h, 'S');

    set(FLAG_COL, GROUND - 1, 'S');

    spawns.enemies.push(
      ['clock', 21], ['clock', 29], ['clock', 31],
      ['invoice', 47], ['invoice', 50], ['clock', 53],
      ['invoice', 61], ['clock', 72], ['invoice', 74],
    );
  }

  const tileAt = (c, r) => (r < 0 || r >= ROWS ? '.' : (c < 0 || c >= COLS ? 'S' : map[r][c]));
  const solidAt = (c, r) => SOLID.has(tileAt(c, r));

  /* ================================================================ STATE */

  const keys = { left: false, right: false, jump: false, run: false };
  let prevJump = false;

  let state = 'title';      // title | play | paused | dying | win | gameover
  let tick = 0;
  let score = 0, coins = 0, lives = 3, time = 200, timeTick = 0;
  let camX = 0;
  let player, enemies, items, particles, popups, bumps;
  let deathCause = '', stateTimer = 0, winPhase = 0, flagY = 0, bonusShown = 0;

  function resetLevel() {
    buildLevel();
    player = {
      x: 3 * T, y: (GROUND - 1) * T + 1, w: 10, h: 15,
      vx: 0, vy: 0, onGround: false, facing: 1,
      powered: false, growT: 0, star: 0, hurt: 0, anim: 0,
    };
    enemies = spawns.enemies.map(([type, col]) => ({
      type, x: col * T, y: (GROUND - 1) * T + 2, w: 14, h: 14,
      vx: type === 'invoice' ? -1 : -0.5, vy: 0,
      alive: true, active: false, squash: 0, flip: false, anim: 0,
    }));
    items = spawns.coins.map(([c, r]) => ({ type: 'coin', x: c * T + 3, y: r * T + 2, w: 10, h: 11, static: true }));
    particles = []; popups = []; bumps = [];
    camX = 0; time = 200; timeTick = 0;
    flagY = 3 * T + 4; winPhase = 0; bonusShown = 0;
  }

  function newGame() {
    score = 0; coins = 0; lives = 3;
    resetLevel();
    state = 'play';
  }

  /* ================================================================ PHYSICS */

  // Positions can be fractional (gravity), so the far edge of a box is
  // x + w (exclusive). Subtracting a tiny EPS finds the last tile it truly
  // overlaps. Using "- 1" instead let a body standing on the ground sink
  // 0.6px without being detected every other frame, which flipped it
  // between standing and falling 30 times a second (visible jitter).
  const EPS = 0.001;

  function moveX(e) {
    e.x += e.vx;
    const top = Math.floor(e.y / T), bot = Math.floor((e.y + e.h - EPS) / T);
    if (e.vx > 0) {
      const col = Math.floor((e.x + e.w - EPS) / T);
      for (let r = top; r <= bot; r++) if (solidAt(col, r)) { e.x = col * T - e.w; return true; }
    } else if (e.vx < 0) {
      const col = Math.floor(e.x / T);
      for (let r = top; r <= bot; r++) if (solidAt(col, r)) { e.x = (col + 1) * T; return true; }
    }
    return false;
  }

  // Returns the tile hit by the head (or null)
  function moveY(e) {
    e.y += e.vy;
    e.onGround = false;
    const left = Math.floor(e.x / T), right = Math.floor((e.x + e.w - EPS) / T);
    if (e.vy > 0) {
      const row = Math.floor((e.y + e.h - EPS) / T);
      for (let c = left; c <= right; c++) {
        if (solidAt(c, row)) { e.y = row * T - e.h; e.vy = 0; e.onGround = true; return null; }
      }
    } else if (e.vy < 0) {
      const row = Math.floor(e.y / T);
      const hits = [];
      for (let c = left; c <= right; c++) if (solidAt(c, row)) hits.push(c);
      if (hits.length) {
        e.y = (row + 1) * T; e.vy = 0;
        const mid = Math.floor((e.x + e.w / 2) / T);
        return { col: hits.includes(mid) ? mid : hits[0], row };
      }
    }
    return null;
  }

  const overlap = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;

  function popup(text, x, y) { popups.push({ text, x, y, t: 50 }); }

  function bumpTile(col, row) {
    const t = tileAt(col, row);
    const bx = col * T, by = row * T;
    if (t === '?' || t === 'D' || t === 'A') {
      map[row][col] = 'U';
      bumps.push({ col, row, t: 10 });
      if (t === '?') {
        coins++; score += 200;
        items.push({ type: 'popcoin', x: bx + 3, y: by - 12, w: 10, h: 11, vy: -4, t: 28 });
      } else {
        items.push({
          type: t === 'D' ? 'dash' : 'bolt', x: bx, y: by, w: 16, h: t === 'D' ? 14 : 12,
          vx: 0, vy: 0, emerge: 16, onGround: false,
        });
      }
    } else if (t === 'B') {
      if (player.powered) {
        map[row][col] = '.';
        score += 50;
        for (let i = 0; i < 4; i++) {
          particles.push({ x: bx + (i % 2) * 8, y: by + (i < 2 ? 0 : 8), vx: (i % 2 ? 1.2 : -1.2), vy: i < 2 ? -5 : -3.5, t: 60 });
        }
      } else {
        bumps.push({ col, row, t: 10 });
      }
    }
    // Knock out enemies standing on a bumped block
    for (const e of enemies) {
      if (e.alive && e.active && Math.abs((e.y + e.h) - by) < 2 && e.x + e.w > bx && e.x < bx + T) killEnemy(e, true);
    }
  }

  function killEnemy(e, flip) {
    e.alive = false;
    score += 100;
    popup('100', e.x, e.y - 8);
    if (flip) { e.flip = true; e.vy = -3.5; e.vx = player.x < e.x ? 1 : -1; }
    else e.squash = 30;
  }

  // Clarity = big. Growing keeps the feet where they are.
  function setBig(p, big) {
    if (big === p.powered) return;
    p.y += big ? SMALL_H - BIG_H : BIG_H - SMALL_H;
    p.h = big ? BIG_H : SMALL_H;
    p.powered = big;
    p.growT = 36; // brief freeze while flicking between sizes
  }

  function hurtPlayer(cause) {
    if (player.star > 0 || player.hurt > 0 || state !== 'play') return;
    if (player.powered) {
      setBig(player, false);
      player.hurt = 120;
      popup('OUCH', player.x - 4, player.y - 10);
    } else {
      die(cause);
    }
  }

  function die(cause) {
    state = 'dying';
    deathCause = cause;
    stateTimer = 150;
    player.vy = -6;
    player.vx = 0;
  }

  /* ================================================================ UPDATE */

  function update() {
    tick++;
    const jumpPressed = keys.jump && !prevJump;
    prevJump = keys.jump;

    if (state === 'play') updatePlay(jumpPressed);
    else if (state === 'dying') updateDying();
    else if (state === 'win') updateWin();

    // Always-running bits
    for (const b of bumps) b.t--;
    bumps = bumps.filter(b => b.t > 0);
    for (const p of popups) { p.t--; p.y -= 0.5; }
    popups = popups.filter(p => p.t > 0);
    for (const p of particles) { p.x += p.vx; p.vy += 0.35; p.y += p.vy; p.t--; }
    particles = particles.filter(p => p.t > 0 && p.y < H + 16);
  }

  function updatePlay(jumpPressed) {
    const p = player;
    // Growing/shrinking: the world pauses for a moment, like the original
    if (p.growT > 0) { p.growT--; return; }

    // Direct control: move only while a direction is held, stop the
    // moment it's released (on the ground and in the air). Whole-pixel
    // speeds keep movement perfectly even on screen.
    const speed = keys.run ? 2 : 1;
    if (keys.left && !keys.right) { p.vx = -speed; p.facing = -1; }
    else if (keys.right && !keys.left) { p.vx = speed; p.facing = 1; }
    else p.vx = 0;

    if (jumpPressed && p.onGround) {
      p.vy = keys.run ? -6 : -5.6;
      p.onGround = false;
    }
    p.vy += keys.jump && p.vy < 0 ? 0.26 : 0.6;
    if (p.vy > 5) p.vy = 5;

    moveX(p);
    if (p.x < camX) { p.x = camX; p.vx = Math.max(0, p.vx); }
    const head = moveY(p);
    if (head) bumpTile(head.col, head.row);

    p.anim += Math.abs(p.vx) * 0.12;
    if (p.star > 0) p.star--;
    if (p.hurt > 0) p.hurt--;

    // Camera: forward only, like the original
    camX = Math.max(camX, Math.min(p.x - 100, COLS * T - W));

    // Visibility gap
    if (p.y > H) { die('LOST IN A VISIBILITY GAP'); return; }

    // Timer
    if (++timeTick >= 24) {
      timeTick = 0; time--;
      if (time <= 0) { die('OUT OF TIME'); return; }
    }

    updateItems();
    updateEnemies();

    // Flagpole
    // Touching the pole or its base block counts
    if (p.x + p.w >= FLAG_COL * T - 1) {
      state = 'win';
      winPhase = 0;
      const heightBonus = Math.max(100, Math.round((GROUND * T - (p.y + p.h)) / 16) * 400);
      score += heightBonus;
      popup(String(heightBonus), FLAG_COL * T + 10, p.y);
      p.x = FLAG_COL * T + 2;
      p.vx = 0; p.vy = 0;
    }
  }

  function updateItems() {
    const p = player;
    for (const it of items) {
      if (it.dead) continue;
      if (it.type === 'popcoin') {
        it.y += it.vy; it.vy += 0.3; it.t--;
        if (it.t <= 0) { it.dead = true; popup('200', it.x, it.y); }
        continue;
      }
      if (it.emerge > 0) {
        it.y -= 1; it.emerge--;
        if (it.emerge === 0) it.vx = 1; // slide right once fully out
        continue;
      }
      if (!it.static) {
        it.vy += 0.3; if (it.vy > 4) it.vy = 4;
        if (moveX(it)) it.vx *= -1;
        moveY(it);
        if (it.y > H) it.dead = true;
      }
      if (overlap(p, it)) {
        it.dead = true;
        if (it.type === 'coin') { coins++; score += 200; }
        else if (it.type === 'dash') { setBig(p, true); score += 1000; popup('CLARITY!', it.x - 12, it.y - 8); }
        else if (it.type === 'bolt') { p.star = 480; score += 1000; popup('AUTOMATED!', it.x - 20, it.y - 8); }
      }
    }
    items = items.filter(i => !i.dead);
  }

  function updateEnemies() {
    const p = player;
    for (const e of enemies) {
      if (!e.active) {
        if (e.x < camX + W + 8) e.active = true; else continue;
      }
      if (e.squash > 0) { e.squash--; continue; }
      if (!e.alive) {
        if (e.flip) { e.vy += 0.3; e.y += e.vy; e.x += e.vx; }
        continue;
      }
      e.vy += 0.4; if (e.vy > 5) e.vy = 5;
      if (moveX(e)) e.vx *= -1;
      moveY(e);
      e.anim += 0.08;
      if (e.y > H) { e.alive = false; continue; }

      if (overlap(p, e)) {
        if (p.star > 0) {
          killEnemy(e, true);
        } else if (p.vy > 0 && (p.y + p.h) - e.y < 8) {
          killEnemy(e, false);
          p.vy = keys.jump ? -5.5 : -3.5;
        } else {
          hurtPlayer(e.type === 'clock' ? 'OVERTIME GOT YOU' : 'ROGUE INVOICE!');
        }
      }
    }
    enemies = enemies.filter(e => e.alive || e.squash > 0 || (e.flip && e.y < H + 16));
  }

  function updateDying() {
    const p = player;
    if (stateTimer < 130) { p.vy += 0.35; p.y += p.vy; }
    if (--stateTimer <= 0) {
      lives--;
      if (lives > 0) { resetLevel(); state = 'play'; }
      else { state = 'gameover'; }
    }
  }

  function updateWin() {
    const p = player;
    const groundY = (GROUND - 1) * T + 1;
    if (winPhase === 0) {
      // Slide down the pole with the flag
      p.y = Math.min(p.y + 2, groundY);
      flagY = Math.min(flagY + 2, (GROUND - 2) * T);
      if (p.y >= groundY && flagY >= (GROUND - 2) * T) { winPhase = 1; p.x += 8; }
    } else if (winPhase === 1) {
      // Walk into HQ
      p.vx = 1; p.facing = 1; p.anim += 0.12;
      p.x += p.vx;
      p.vy += 0.6; moveY(p);
      if (p.x >= HQ_COL * T + 24) { winPhase = 2; stateTimer = 0; }
    } else if (winPhase === 2) {
      // Tally remaining time
      if (time > 0 && tick % 2 === 0) { time = Math.max(0, time - 2); score += 100; bonusShown += 100; }
      if (time === 0) { winPhase = 3; }
    }
  }

  /* ================================================================ RENDER */

  // The camera is snapped to a whole pixel and every position is rounded
  // the same way, so tiles and sprites always move together.
  let cam = 0;
  const ix = e => Math.round(e.x) - cam;
  const iy = e => Math.round(e.y);

  function text(str, x, y, col = C.white, align = 'left') {
    ctx.font = FONT;
    ctx.textAlign = align;
    ctx.textBaseline = 'top';
    ctx.fillStyle = C.black;
    ctx.fillText(str, x + 1, y + 1);
    ctx.fillStyle = col;
    ctx.fillText(str, x, y);
  }

  function drawBackground() {
    ctx.fillStyle = C.sky;
    ctx.fillRect(0, 0, W, H);

    const groundY = GROUND * T;

    // Hills
    for (const hx of [0, 48 * 16, 96 * 16]) {
      for (const [ox, r] of [[16, 40], [200, 24], [420, 40], [640, 24]]) {
        const x = hx + ox - cam;
        if (x < -r * 2 || x > W + r * 2) continue;
        ctx.fillStyle = C.green;
        ctx.beginPath();
        ctx.moveTo(x - r * 1.6, groundY);
        ctx.quadraticCurveTo(x, groundY - r * 2.2, x + r * 1.6, groundY);
        ctx.fill();
        ctx.fillStyle = C.greenDark;
        ctx.fillRect(x - 6, groundY - r * 0.9, 2, 6);
        ctx.fillRect(x + 4, groundY - r * 0.7, 2, 6);
      }
    }

    // Clouds (parallax)
    for (let i = 0; i < 8; i++) {
      const x = ((i * 190 + 40) - Math.round(cam * 0.5)) % (W + 400) - 60;
      const y = 24 + (i % 3) * 18;
      cloud(x, y);
    }

    // Bushes
    for (const bx of [6, 22, 42, 71]) bush(bx * T - cam, groundY);

    // Billboards with the three areas the site covers
    board(7, 'SALES');
    board(35, 'PURCHASING');
    board(61, 'PAYROLL');

    // HQ building
    const hx = HQ_COL * T - cam;
    if (hx < W + 80) {
      const top = groundY - 80;
      ctx.fillStyle = C.brickDark; ctx.fillRect(hx - 1, top - 1, 66, 81);
      ctx.fillStyle = C.brick; ctx.fillRect(hx, top, 64, 80);
      ctx.fillStyle = C.lens;
      for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) {
        if (r === 2 && (c === 1 || c === 2)) continue;
        ctx.fillRect(hx + 6 + c * 15, top + 8 + r * 20, 8, 10);
      }
      ctx.fillStyle = C.black; ctx.fillRect(hx + 24, groundY - 22, 16, 22);
      ctx.fillStyle = C.gold; ctx.fillRect(hx + 18, top - 12, 28, 11);
      text('HQ', hx + 32, top - 10, C.brickDark, 'center');
    }
  }

  function cloud(x, y) {
    ctx.fillStyle = C.white;
    ctx.fillRect(x + 8, y, 24, 8);
    ctx.fillRect(x, y + 6, 48, 10);
    ctx.fillRect(x + 20, y - 6, 14, 8);
  }

  function bush(x, groundY) {
    if (x < -64 || x > W + 16) return;
    ctx.fillStyle = C.greenLight;
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.arc(x + 8 + i * 12, groundY - 4, 9, Math.PI, 0);
      ctx.fill();
    }
    ctx.fillStyle = C.green;
    ctx.fillRect(x, groundY - 4, 48, 4);
  }

  function board(col, label) {
    const x = col * T - cam;
    if (x < -120 || x > W + 20) return;
    ctx.font = FONT;
    const w = ctx.measureText(label).width + 10;
    const groundY = GROUND * T;
    ctx.fillStyle = C.brickDark;
    ctx.fillRect(x + w / 2 - 1, groundY - 26, 3, 26);
    ctx.fillStyle = C.black;
    ctx.fillRect(x - 1, groundY - 45, w + 2, 20);
    ctx.fillStyle = C.white;
    ctx.fillRect(x, groundY - 44, w, 18);
    ctx.fillStyle = C.black;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(label, x + 5, groundY - 39);
  }

  function drawTiles() {
    const c0 = Math.floor(cam / T), c1 = Math.min(COLS - 1, c0 + Math.ceil(W / T) + 1);
    for (let r = 0; r < ROWS; r++) {
      for (let c = c0; c <= c1; c++) {
        const t = map[r][c];
        if (t === '.') continue;
        const bump = bumps.find(b => b.col === c && b.row === r);
        const oy = bump ? -Math.round(Math.sin((bump.t / 10) * Math.PI) * 5) : 0;
        ctx.drawImage(TILE[t], Math.round(c * T - cam), r * T + oy);
      }
    }

    // Flagpole
    const fx = FLAG_COL * T - cam + 7;
    if (fx > -20 && fx < W + 20) {
      ctx.fillStyle = C.greenLight;
      ctx.fillRect(fx, 3 * T, 2, (GROUND - 4) * T);
      ctx.fillStyle = C.green;
      ctx.beginPath(); ctx.arc(fx + 1, 3 * T - 3, 4, 0, Math.PI * 2); ctx.fill();
      // Flag: white with a green tick
      ctx.fillStyle = C.white;
      ctx.beginPath();
      ctx.moveTo(fx, flagY); ctx.lineTo(fx - 16, flagY + 7); ctx.lineTo(fx, flagY + 14); ctx.fill();
      ctx.fillStyle = C.green;
      ctx.fillRect(fx - 9, flagY + 6, 2, 3);
      ctx.fillRect(fx - 7, flagY + 8, 2, 2);
      ctx.fillRect(fx - 5, flagY + 4, 2, 4);
    }
  }

  function drawItems(behind) {
    for (const it of items) {
      const emerging = it.emerge > 0;
      if (emerging !== behind) continue;
      const x = ix(it), y = iy(it);
      if (x < -20 || x > W + 20) continue;
      if (it.type === 'coin' || it.type === 'popcoin') {
        ctx.drawImage(COIN, x, y); // static — no spin
      } else if (it.type === 'dash') {
        ctx.drawImage(DASHBOARD, x, y);
      } else if (it.type === 'bolt') {
        ctx.drawImage(BOLT, x, y);
      }
    }
  }

  function drawEnemies() {
    for (const e of enemies) {
      if (!e.active) continue;
      const set = e.type === 'clock' ? CLOCK : INVOICE;
      const img = set[Math.floor(e.anim) % 2];
      const x = ix(e) - 1, y = iy(e) - 2;
      if (e.squash > 0) {
        ctx.drawImage(img, x, y + 10, 16, 6);
      } else if (e.flip) {
        ctx.save();
        ctx.translate(x, y + 16); ctx.scale(1, -1);
        ctx.drawImage(img, 0, 0);
        ctx.restore();
      } else {
        ctx.drawImage(img, x, y);
      }
    }
  }

  function drawPlayer() {
    const p = player;
    if (p.hurt > 0 && Math.floor(tick / 3) % 2) return;
    let pal = 'normal';
    if (p.star > 0) pal = ['star1', 'star2', 'star3'][Math.floor(tick / 4) % 3];
    let frame = 'stand';
    if (state === 'dying' || !p.onGround) frame = 'jump';
    else if (Math.abs(p.vx) > 0.1) frame = Math.floor(p.anim) % 2 ? 'run1' : 'run2';
    if (state === 'win' && winPhase === 0) frame = 'jump';
    if (state === 'win' && winPhase >= 2) return; // inside HQ
    // While growing/shrinking, flick between the two sizes
    const big = p.growT > 0 ? (Math.floor(p.growT / 6) % 2 === 0) === p.powered : p.powered;
    const f = (big ? PLAYER_BIG : PLAYER)[character][pal][frame];
    const yOff = big === p.powered ? 0 : (big ? SMALL_H - BIG_H : BIG_H - SMALL_H);
    ctx.drawImage(p.facing > 0 ? f.r : f.l, ix(p) - 3, iy(p) - 1 + yOff);
  }

  function drawParticles() {
    ctx.fillStyle = C.brick;
    for (const pt of particles) {
      ctx.fillRect(Math.round(pt.x - cam), Math.round(pt.y), 6, 6);
      ctx.fillStyle = C.black;
      ctx.fillRect(Math.round(pt.x - cam) + 5, Math.round(pt.y), 1, 6);
      ctx.fillStyle = C.brick;
    }
    for (const pu of popups) text(pu.text, Math.round(pu.x - cam), Math.round(pu.y), C.white);
  }

  function drawHUD() {
    text(playerName, 16, 10);
    text(String(score).padStart(6, '0'), 16, 20);
    ctx.drawImage(COIN, 84, 19);
    text('x' + String(coins).padStart(2, '0'), 96, 20);
    text('WORLD', 144, 10);
    text(' 1-1', 144, 20);
    text('TIME', 208, 10);
    text(state === 'title' ? '' : String(Math.max(0, time)).padStart(3, ' '), 208, 20);
  }

  // Character select: the whole cast in a row
  const SELECT_GAP = 26;
  const SELECT_X = {};
  ROSTER.forEach((id, i) => { SELECT_X[id] = Math.round(W / 2 - (ROSTER.length * SELECT_GAP) / 2 + i * SELECT_GAP + (SELECT_GAP - 16) / 2); });

  function panel(y, h) {
    ctx.fillStyle = C.black;
    ctx.fillRect(16, y, W - 32, h);
    ctx.fillStyle = C.white;
    ctx.fillRect(18, y + 2, W - 36, 2);
    ctx.fillRect(18, y + h - 4, W - 36, 2);
    ctx.fillRect(18, y + 2, 2, h - 4);
    ctx.fillRect(W - 20, y + 2, 2, h - 4);
  }

  function drawOverlay() {
    if (state === 'title') {
      panel(30, 196);
      text('SUPER 3SHEETS', W / 2, 40, C.gold, 'center');
      text('WORLD 1-1: MONTH END', W / 2, 54, C.white, 'center');
      ctx.drawImage(COIN, 30, 72);             text('DATA POINTS', 50, 74);
      ctx.drawImage(DASHBOARD, 27, 87);        text('CLARITY: GROW BIG', 50, 90);
      ctx.drawImage(BOLT, 27, 104);            text('AUTOMATION', 50, 106);
      ctx.drawImage(CLOCK[0], 27, 118);        text('OVERTIME', 50, 122);
      ctx.drawImage(INVOICE[0], 27, 134);      text('ROGUE INVOICE', 50, 138);
      // Character select
      text('CHOOSE', W / 2, 158, C.white, 'center');
      for (const id of ROSTER) {
        const x = SELECT_X[id];
        const chosen = id === character;
        if (chosen) {
          ctx.fillStyle = C.gold;
          ctx.fillRect(x - 4, 170, 24, 24);
          ctx.fillStyle = C.black;
          ctx.fillRect(x - 2, 172, 20, 20);
        }
        ctx.drawImage(PLAYER[id].normal.stand.r, x, 174);
      }
      text('<', SELECT_X[ROSTER[0]] - 14, 178, C.white);
      text('>', SELECT_X[ROSTER[ROSTER.length - 1]] + 20, 178, C.white);
      if (Math.floor(tick / 30) % 2 === 0) text('PRESS START', W / 2, 206, C.gold, 'center');
    } else if (state === 'paused') {
      panel(92, 48);
      text('PAUSED', W / 2, 104, C.gold, 'center');
      text('CLICK TO RESUME', W / 2, 118, C.white, 'center');
    } else if (state === 'dying' && stateTimer < 110) {
      panel(92, 48);
      text(deathCause, W / 2, 104, C.gold, 'center');
      text('LIVES x ' + Math.max(0, lives - 1), W / 2, 118, C.white, 'center');
    } else if (state === 'gameover') {
      panel(80, 72);
      text('GAME OVER', W / 2, 94, C.red, 'center');
      text('THE BOOKS DID', W / 2, 110, C.white, 'center');
      text('NOT BALANCE', W / 2, 120, C.white, 'center');
      if (Math.floor(tick / 30) % 2 === 0) text('PRESS START', W / 2, 136, C.gold, 'center');
    } else if (state === 'win' && winPhase >= 2) {
      panel(64, 92);
      text('REPORT PUBLISHED!', W / 2, 78, C.gold, 'center');
      text('TIME BONUS ' + bonusShown, W / 2, 96, C.white, 'center');
      text('SCORE ' + String(score).padStart(6, '0'), W / 2, 110, C.white, 'center');
      if (winPhase === 3 && Math.floor(tick / 30) % 2 === 0) text('PRESS START', W / 2, 132, C.greenLight, 'center');
    }
  }

  function render() {
    cam = Math.round(camX);
    drawBackground();
    drawItems(true);
    drawTiles();
    drawItems(false);
    drawEnemies();
    if (state !== 'title') drawPlayer();
    drawParticles();
    drawHUD();
    drawOverlay();
    view.imageSmoothingEnabled = false;
    view.drawImage(buffer, 0, 0, canvas.width, canvas.height);
  }

  /* ================================================================ INPUT */

  const KEYMAP = {
    ArrowLeft: 'left', KeyA: 'left',
    ArrowRight: 'right', KeyD: 'right',
    ArrowUp: 'jump', KeyW: 'jump', Space: 'jump', KeyZ: 'jump',
    KeyX: 'run', ShiftLeft: 'run', ShiftRight: 'run',
  };

  function pressStart() {
    if (state === 'title' || state === 'gameover' || (state === 'win' && winPhase === 3)) {
      newGame();
      prevJump = true; // don't jump on the frame we start
    } else if (state === 'paused') {
      state = 'play';
    }
  }

  // Keys are read at the window level so the arrow keys work even when
  // the canvas itself doesn't have focus. On the standalone page the game
  // always owns the keyboard; on the site it does while it has focus, or
  // while a game is in progress and on screen (so the page can still be
  // scrolled with the keyboard before you start).
  const standalone = canvas.dataset.fit === 'screen';
  let inView = true;

  function typingElsewhere() {
    const el = document.activeElement;
    return !!el && el !== canvas && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName));
  }

  function ownsKeys() {
    if (typingElsewhere()) return false;
    return standalone || document.activeElement === canvas ||
      ((state === 'play' || state === 'paused') && inView);
  }

  window.addEventListener('keydown', e => {
    if (!ownsKeys()) return;
    const k = KEYMAP[e.code];
    if (k || e.code === 'Enter' || e.code === 'KeyP' || e.code === 'Escape') e.preventDefault();
    if (e.repeat && !k) return;
    if (state === 'title' && (k === 'left' || k === 'right')) { if (!e.repeat) cycleCharacter(k === 'left' ? -1 : 1); return; }
    if (e.code === 'Enter' || (e.code === 'Space' && state !== 'play' && state !== 'paused')) { pressStart(); return; }
    if (e.code === 'KeyP' || e.code === 'Escape') {
      if (state === 'play') { releaseKeys(); state = 'paused'; } else if (state === 'paused') state = 'play';
      return;
    }
    if (k) {
      if (state === 'paused') state = 'play'; // any game key resumes
      keys[k] = true;
    }
  });

  window.addEventListener('keyup', e => {
    const k = KEYMAP[e.code];
    if (k) { if (ownsKeys()) e.preventDefault(); keys[k] = false; }
  });

  canvas.addEventListener('pointerdown', e => {
    canvas.focus({ preventScroll: true });
    if (state === 'title') {
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) * (W / rect.width);
      const y = (e.clientY - rect.top) * (H / rect.height);
      if (y > 164 && y < 198) {
        for (const [id, sx] of Object.entries(SELECT_X)) {
          if (x > sx - 4 && x < sx + 20) { setCharacter(id); return; }
        }
      }
    }
    pressStart();
  });

  const wrap = canvas.closest('.game-wrap') || canvas.parentElement;

  if (nameInput) {
    nameInput.value = playerName === 'PLAYER' ? '' : playerName;
    nameInput.addEventListener('input', () => {
      const clean = cleanName(nameInput.value);
      if (nameInput.value.toUpperCase() !== clean) nameInput.value = clean;
      playerName = clean || 'PLAYER';
      try { localStorage.setItem('s3-name', clean); } catch (e) { /* ignore */ }
    });
    // Enter in the name box starts the game
    nameInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        canvas.focus({ preventScroll: true });
        pressStart();
      }
    });
  }

  function releaseKeys() { for (const k in keys) keys[k] = false; }

  canvas.addEventListener('blur', () => {
    if (standalone) return;
    setTimeout(() => {
      if (wrap.contains(document.activeElement)) return;
      releaseKeys();
      if (state === 'play') state = 'paused';
    }, 0);
  });

  // When embedded in the site's pop-up, the page asks the game to pause
  // as the pop-up closes.
  window.addEventListener('message', e => {
    if (e.origin === location.origin && e.data === 's3:pause' && state === 'play') { releaseKeys(); state = 'paused'; }
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden && state === 'play') { releaseKeys(); state = 'paused'; }
  });

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      for (const en of entries) {
        inView = en.isIntersecting;
        if (!inView && state === 'play') { releaseKeys(); state = 'paused'; }
      }
    }, { threshold: 0.25 }).observe(canvas);
  }

  // Touch buttons
  wrap.querySelectorAll('[data-key]').forEach(btn => {
    const k = btn.dataset.key;
    const on = e => {
      e.preventDefault();
      if (state === 'title' && (k === 'left' || k === 'right')) { cycleCharacter(k === 'left' ? -1 : 1); return; }
      if (state !== 'play') pressStart();
      keys[k] = true;
      btn.classList.add('is-down');
    };
    const off = e => { e.preventDefault(); keys[k] = false; btn.classList.remove('is-down'); };
    btn.addEventListener('pointerdown', on);
    btn.addEventListener('pointerup', off);
    btn.addEventListener('pointerleave', off);
    btn.addEventListener('pointercancel', off);
    btn.addEventListener('contextmenu', e => e.preventDefault());
  });

  /* ================================================================ SIZE */

  // Scale the canvas by a whole number of *device* pixels so every game
  // pixel is the same size on screen (no shimmer on moving sprites).
  function fit() {
    const dpr = window.devicePixelRatio || 1;
    const border = 8; // 4px CSS border each side
    const availW = Math.max(W, wrap.clientWidth - border);
    let scale = Math.floor((availW * dpr) / W);
    // Standalone page: also fit the viewport height, leaving room for
    // the touch buttons / help line underneath.
    if (canvas.dataset.fit === 'screen') {
      const reserved = parseInt(canvas.dataset.reserve || '0', 10) + border;
      scale = Math.min(scale, Math.floor(((window.innerHeight - reserved) * dpr) / H));
    }
    scale = Math.max(1, scale);
    if (canvas.width !== W * scale) {
      canvas.width = W * scale;
      canvas.height = H * scale;
    }
    canvas.style.width = (W * scale) / dpr + 'px';
    canvas.style.height = (H * scale) / dpr + 'px';
  }

  fit();
  if ('ResizeObserver' in window) new ResizeObserver(fit).observe(wrap);
  window.addEventListener('resize', fit);

  /* ================================================================ LOOP */

  resetLevel();

  const STEP = 1000 / 60;
  let last = performance.now(), acc = 0;

  function frame(now) {
    let dt = Math.min(100, now - last);
    last = now;
    // rAF timestamps wobble by a fraction of a millisecond; without this a
    // 60Hz screen occasionally runs 0 or 2 steps in a frame, which reads as
    // stutter. Snap near-60Hz frames to exactly one step.
    if (Math.abs(dt - STEP) < 2) dt = STEP;
    acc += dt;
    while (acc >= STEP) {
      if (state !== 'paused') update(); else tick++;
      acc -= STEP;
    }
    render();
    requestAnimationFrame(frame);
  }

  const start = () => requestAnimationFrame(t => { last = t; frame(t); });
  if (document.fonts && document.fonts.load) {
    document.fonts.load(FONT).then(start, start);
  } else {
    start();
  }
})();
