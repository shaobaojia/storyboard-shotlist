/**
 * Restore prompt column visibility state from localStorage.
 * Drop this in the page's <script> block after the tab persistence init.
 * 
 * Works together with the toggle button's onclick which saves state:
 *   localStorage.setItem('hidePrompt', h);
 */
(function(){
  var hide = localStorage.getItem('hidePrompt');
  if (hide === 'true') {
    document.querySelectorAll('.beat-section table').forEach(function(tb){
      tb.classList.add('hide-c11');
    });
    var btn = document.getElementById('toggle-prompt');
    if (btn) btn.textContent = '显示提示词';
  }
})();
