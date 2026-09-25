/*
  launcher.js — a warp pipe on the brick footer that opens Super 3Sheets
  (game.html) in a pop-up over the site. Closing the pop-up pauses the game.
*/

(() => {
  'use strict';

  const footer = document.querySelector('.site-footer');
  if (!footer || typeof HTMLDialogElement === 'undefined') return;

  /* ------------------------------------------------------------ pop-up */

  const dlg = document.createElement('dialog');
  dlg.className = 'game-dialog';
  dlg.setAttribute('aria-label', 'Super 3Sheets');
  dlg.innerHTML = `
    <div class="game-dialog__bar">
      <span>SUPER 3SHEETS</span>
      <button type="button" class="game-dialog__close" aria-label="Close game">X</button>
    </div>
    <iframe title="Super 3Sheets game"></iframe>`;
  document.body.appendChild(dlg);

  const frame = dlg.querySelector('iframe');

  function focusGame() {
    try {
      frame.contentWindow.focus();
      const c = frame.contentDocument.getElementById('game-canvas');
      if (c) c.focus({ preventScroll: true });
    } catch (e) { /* not loaded yet */ }
  }

  frame.addEventListener('load', focusGame);

  function openGame() {
    if (!frame.getAttribute('src')) frame.src = 'game.html'; // load on first use only
    if (!dlg.open) dlg.showModal();
    document.documentElement.classList.add('game-open');
    setTimeout(focusGame, 30);
  }

  function closeGame() { if (dlg.open) dlg.close(); }

  dlg.addEventListener('close', () => {
    document.documentElement.classList.remove('game-open');
    try { frame.contentWindow.postMessage('s3:pause', location.origin); } catch (e) { /* ignore */ }
  });

  dlg.querySelector('.game-dialog__close').addEventListener('click', closeGame);
  dlg.addEventListener('click', e => { if (e.target === dlg) closeGame(); }); // backdrop

  /* ------------------------------------------------------------ warp pipe */

  const pipe = document.createElement('button');
  pipe.type = 'button';
  pipe.className = 'game-pipe';
  pipe.setAttribute('aria-label', 'Enter the warp pipe: play Super 3Sheets');
  pipe.innerHTML = '<span class="game-pipe__label">BONUS STAGE</span><span class="game-pipe__lip">PLAY</span><span class="game-pipe__body"></span>';
  pipe.addEventListener('click', openGame);
  footer.appendChild(pipe);
})();
