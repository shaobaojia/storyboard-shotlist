/**
 * Tab state persistence via localStorage.
 * Drop this before </body> in the film-level container HTML.
 *
 * Remembers: last scene tab, last sub-tab per scene, prompt visibility toggle.
 * Falls back to default on first visit or when JS is disabled.
 */
(function(){
  // ── Scene-level tabs ──
  var sceneRadios = document.querySelectorAll('[name=scene]');
  var savedScene = localStorage.getItem('lastScene');
  if (savedScene) {
    var el = document.getElementById(savedScene);
    if (el) el.checked = true;
  }
  sceneRadios.forEach(function(r){
    r.addEventListener('change', function(){
      localStorage.setItem('lastScene', r.id);
    });
  });

  // ── Sub-tabs (name=sub-*) ──
  var allSubGroups = document.querySelectorAll('[name^=sub-]');
  var seenGroups = {};
  allSubGroups.forEach(function(r){
    var g = r.name;
    if (seenGroups[g]) return;
    seenGroups[g] = true;
    var sceneId = g.replace('sub-', '');
    var savedSub = localStorage.getItem('lastSub-' + sceneId);
    if (savedSub) {
      var el = document.getElementById(savedSub);
      if (el) el.checked = true;
    }
    document.querySelectorAll('[name="' + g + '"]').forEach(function(sr){
      sr.addEventListener('change', function(){
        localStorage.setItem('lastSub-' + sceneId, sr.id);
      });
    });
  });

  // ── Prompt column visibility toggle ──
  var hide = localStorage.getItem('hidePrompt');
  if (hide === 'true') {
    document.querySelectorAll('.beat-section table').forEach(function(tb){
      tb.classList.add('hide-c11');
    });
    var btn = document.getElementById('toggle-prompt');
    if (btn) btn.textContent = '显示提示词';
  }
})();
