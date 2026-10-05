/*
  launcher.js — a little filing cabinet on the footer that opens The Fourth Sheet:
  The Month-End Run
  (game.html) in a pop-up over the site. Closing the pop-up pauses the game.
*/

(() => {
  'use strict';

  const footer = document.querySelector('.site-footer');
  if (!footer || typeof HTMLDialogElement === 'undefined') return;

  /* ------------------------------------------------------------ pop-up */

  const dlg = document.createElement('dialog');
  dlg.className = 'game-dialog';
  dlg.setAttribute('aria-label', 'The Fourth Sheet: The Month-End Run');
  dlg.innerHTML = `
    <div class="game-dialog__bar">
      <span>THE FOURTH SHEET: THE MONTH-END RUN</span>
      <button type="button" class="game-dialog__fs" hidden>FULL SCREEN</button>
      <button type="button" class="game-dialog__close" aria-label="Close game">X</button>
    </div>
    <iframe title="The Fourth Sheet: The Month-End Run"></iframe>`;
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

  function closeGame() {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    if (dlg.open) dlg.close();
  }

  // True full screen (hides the browser too) where the browser allows it
  const fsBtn = dlg.querySelector('.game-dialog__fs');
  if (dlg.requestFullscreen && document.fullscreenEnabled) {
    fsBtn.hidden = false;
    fsBtn.addEventListener('click', () => {
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
      else dlg.requestFullscreen().catch(() => {});
      setTimeout(focusGame, 100);
    });
    document.addEventListener('fullscreenchange', () => {
      fsBtn.textContent = document.fullscreenElement ? 'EXIT FULL SCREEN' : 'FULL SCREEN';
    });
  }

  dlg.addEventListener('close', () => {
    document.documentElement.classList.remove('game-open');
    try { frame.contentWindow.postMessage('s3:pause', location.origin); } catch (e) { /* ignore */ }
  });

  dlg.querySelector('.game-dialog__close').addEventListener('click', closeGame);
  dlg.addEventListener('click', e => { if (e.target === dlg) closeGame(); }); // backdrop

  /* ------------------------------------------------------------ filing cabinet */

  const pipe = document.createElement('button');
  pipe.type = 'button';
  pipe.className = 'game-pipe';
  pipe.setAttribute('aria-label', 'Open the filing cabinet: play The Fourth Sheet: The Month-End Run');
  pipe.innerHTML = '<span class="game-pipe__label">BONUS STAGE</span><span class="game-pipe__lip">PLAY</span><span class="game-pipe__body"><i></i><i></i></span>';
  pipe.addEventListener('click', openGame);
  footer.appendChild(pipe);
})();
