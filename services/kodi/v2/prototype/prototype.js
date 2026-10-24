/* Local-only layout simulation: no requests, credentials or playback APIs. */
(() => {
  const root = document.getElementById('aster');
  const data = [
    ['Pop, Electronic & Hip-Hop',4308],['Jazz, Blues, R&B & Soul',4365],
    ['Rock & Alternative',3919],['Country & Folk',3782],['Christmas',585],
    ['Classical',174],['Other / unclassified',8]
  ];
  let page = 'Genres', genre = null, visible = data, lastGrid = 0, preferredColumn = 0;
  let returnFocus = null;
  let modelFocus = false;
  const grid = document.getElementById('grid'), search = document.getElementById('search');
  const rail = document.getElementById('rail'), modal = document.getElementById('preview-dialog');
  function all(area) { return [...root.querySelectorAll(`[data-area="${area}"]`)]; }
  function focus(area, index = 0) { const nodes = all(area); (nodes[Math.min(index,nodes.length-1)] || all('nav')[4]).focus(); }
  function setHero(row) {
    document.getElementById('hero-title').textContent = row[0];
    document.getElementById('hero-copy').textContent = `${row[1].toLocaleString()} tracks in this genre. Your library, without the clutter.`;
  }
  function show(title, copy) {
    returnFocus = document.activeElement;
    document.getElementById('dialog-title').textContent = title;
    document.getElementById('dialog-copy').textContent = copy;
    modal.showModal(); document.getElementById('dialog-close').focus();
  }
  function close() { modal.close(); if (returnFocus?.isConnected) returnFocus.focus(); }
  function render() {
    grid.replaceChildren();
    const query = search.value.trim().toLocaleLowerCase();
    visible = data.filter(row => row[0].toLocaleLowerCase().includes(query));
    document.getElementById('grid-count').textContent = `${visible.length} categories`;
    document.getElementById('grid-heading').textContent = 'Browse genres';
    document.getElementById('empty').hidden = visible.length > 0;
    visible.forEach((row,i) => {
      const tile = document.createElement('button');
      tile.className = 'tile'; tile.dataset.area = 'grid'; tile.dataset.index = i;
      tile.setAttribute('aria-label',`${row[0]}, ${row[1].toLocaleString()} tracks`);
      const art = document.createElement('span'); art.className = 'tile-art';
      const img = document.createElement('img'); img.src = '../../skin.asterhome/media/23-music-album.png'; img.alt = '';
      art.append(img);
      const label = document.createElement('span'); label.className = 'tile-label'; label.textContent = row[0];
      const count = document.createElement('span'); count.className = 'tile-count'; count.textContent = `${row[1].toLocaleString()} tracks`;
      tile.append(art,label,count); grid.append(tile);
      tile.addEventListener('focus',() => { lastGrid = i; if (!modelFocus) preferredColumn = i % 4; setHero(row); });
      tile.addEventListener('click',() => {
        genre = row[0];
        show(genre,`${row[1].toLocaleString()} track memberships. The genre detail will offer Albums, Artists and Songs with Play / Shuffle. This is a local layout preview; no media is opened.`);
      });
    });
    lastGrid = Math.min(lastGrid,Math.max(visible.length-1,0));
    if (visible.length) setHero(visible[lastGrid]);
  }
  function resize() {
    const scale = document.getElementById('viewport').clientWidth / 1920;
    root.style.transform = `scale(${scale})`;
    document.getElementById('viewport').style.height = `${1080*scale}px`;
  }
  root.addEventListener('focusin',event => {
    rail.classList.toggle('expanded',event.target.dataset.area === 'rail');
  });
  root.addEventListener('keydown', event => {
    const target = document.activeElement, area = target.dataset.area;
    if (modal.open) {
      if (event.key === 'Escape' || event.key === 'Backspace') { event.preventDefault(); close(); }
      return;
    }
    if (event.key === 'Escape' || event.key === 'Backspace') {
      if (target === search && event.key === 'Backspace') return;
      event.preventDefault();
      if (area === 'rail') focus('grid',lastGrid);
      else if (search.value) { search.value = ''; render(); focus('grid',lastGrid); }
      else focus('rail',2);
      return;
    }
    if (!event.key.startsWith('Arrow')) return;
    if (target === search && ['ArrowLeft','ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const direction = event.key.slice(5).toLowerCase();
    const nodes = all(area), index = nodes.indexOf(target);
    if (area === 'grid') {
      const next = AsterFocus.gridStep(index,direction,visible.length,4,preferredColumn);
      preferredColumn = next.column;
      modelFocus = true;
      focus(next.area,next.area === 'rail' ? 2 : next.area === 'grid' ? next.index : next.area === 'nav' ? 4 : 0);
      modelFocus = false;
    } else if (area === 'rail') {
      if (direction === 'right') focus('grid',lastGrid);
      if (direction === 'up') focus('rail',Math.max(0,index-1));
      if (direction === 'down') focus('rail',Math.min(nodes.length-1,index+1));
    } else if (area === 'nav') {
      if (direction === 'left') index ? focus('nav',index-1) : focus('rail',2);
      if (direction === 'right') focus('nav',Math.min(4,index+1));
      if (direction === 'down') focus('hero',0);
    } else if (area === 'hero') {
      if (direction === 'down') focus('grid',lastGrid);
      if (direction === 'up') focus('nav',4);
      if (direction === 'left') index ? focus('hero',0) : focus('rail',2);
      if (direction === 'right') focus('hero',1);
    } else if (area === 'filters') {
      if (direction === 'left') focus('grid',lastGrid);
      if (direction === 'up') index ? focus('filters',index-1) : focus('nav',4);
      if (direction === 'down') focus('filters',Math.min(nodes.length-1,index+1));
    }
  });
  all('nav').forEach(button => button.addEventListener('click',() => {
    if (button.dataset.page === 'Genres') { page = 'Genres'; search.value = ''; render(); focus('grid',0); }
    else show(button.dataset.page,`The existing ${button.dataset.page.toLowerCase()} destination is retained. This M1 preview is limited to the new Genres layout and focus behavior.`);
  }));
  all('rail').forEach(button => button.addEventListener('click',() => {
    if (button.dataset.index === '2') focus('grid',lastGrid);
    else show(button.getAttribute('aria-label'), 'Other Aster sections are unchanged. This local prototype never navigates or controls a Kodi client.');
  }));
  document.getElementById('browse').addEventListener('click',() => focus('grid',lastGrid));
  document.getElementById('shuffle-all').addEventListener('click',() => show('Shuffle all · no holiday music', '16,348 eligible tracks. 765 excluded through track or album holiday classifications. This preview does not clear a queue, start playback, or change a saved playlist.'));
  document.getElementById('dialog-close').addEventListener('click',close);
  modal.addEventListener('cancel',event => { event.preventDefault(); close(); });
  search.addEventListener('input',render);
  document.getElementById('clear').addEventListener('click',() => { search.value = ''; render(); focus('grid',0); });
  window.addEventListener('resize',resize);
  render(); resize(); focus('grid',0);
  window.AsterPrototype = {getState:() => ({page,genre,lastGrid,preferredColumn,count:visible.length})};
})();
