// Run in the Légifrance page with the built-in browser's javascript_tool (after `navigate`).
// Builds window.__lf: the full text of the page where every <table> is replaced, IN PLACE, by a markdown table
// (Légifrance hides tables behind "Afficher le tableau": a plain text extraction loses rates and thresholds).
// Then read it in slices with further javascript_tool calls:  window.__lf.slice(0, 40000), (40000, 80000)…
// (a fetch from the page to another address is blocked by the page's CSP).
(() => {
  const root = document.querySelector('main') || document.body;
  const clone = root.cloneNode(true);
  // Drop UI chrome that pollutes the text.
  clone.querySelectorAll('script, style, nav, header, footer, button, [aria-hidden="true"]').forEach((e) => e.remove());
  let tables = 0;
  clone.querySelectorAll('table').forEach((t) => {
    const rows = [...t.rows].map((r) => [...r.cells].map((c) => c.innerText.replace(/\s+/g, ' ').trim().replace(/\|/g, '/')));
    if (!rows.length) {
      return;
    }
    const width = Math.max(...rows.map((r) => r.length));
    const line = (r) => '| ' + r.concat(Array(width - r.length).fill('')).join(' | ') + ' |';
    const md = [line(rows[0]), '|' + ' --- |'.repeat(width), ...rows.slice(1).map(line)].join('\n');
    const pre = document.createElement('pre');
    pre.textContent = '\n' + md + '\n';
    t.replaceWith(pre);
    tables++;
  });
  // innerText needs the node attached to lay out line breaks.
  clone.style.position = 'absolute';
  clone.style.left = '-99999px';
  document.body.appendChild(clone);
  let text = clone.innerText;
  clone.remove();
  text = text.replace(/Afficher le tableau\n?/g, '').replace(/\n{3,}/g, '\n\n');
  window.__lf = text;
  const articles = (text.match(/^Article\s+\S+/gm) || []).length;
  return { chars: text.length, tables, articles, slices: Math.ceil(text.length / 40000) };
})();
