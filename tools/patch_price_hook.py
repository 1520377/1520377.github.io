# -*- coding: utf-8 -*-
# 在 index.html 末尾插入运行时钩子：打开页面先拉 price.json，取到就用最新收盘价
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "JHPRICE-HOOK"

SNIPPET = """
<script>
/* JHPRICE-HOOK */
(function () {
  function apply(d) {
    try {
      if (!d || !d.date || !d.price || !window.HIST || !window.state) return;
      var h = (d.hist && d.hist.length >= 5) ? d.hist : null;
      if (!h) return;
      var paid = (state.manual && state.manual > 0);
      var cur = HIST.length ? HIST[HIST.length - 1].d : "";
      if (!cur || h[h.length - 1].d > cur) {
        HIST.length = 0;
        for (var i = 0; i < h.length; i++) { HIST.push({ d: h[i].d, c: h[i].c }); }
      }
      if (!paid && (!state.baseDate || d.date > state.baseDate)) {
        state.basePrice = d.price;
        state.baseDate = d.date;
      }
      if (typeof saveLocal === "function") { saveLocal(); }
      if (typeof renderAll === "function") { renderAll(); }
    } catch (e) {}
  }
  function run() {
    try {
      fetch("price.json?t=" + Date.now(), { cache: "no-store" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(apply)
        .catch(function () {});
    } catch (e) {}
  }
  if (document.readyState === "complete") { setTimeout(run, 200); }
  else { window.addEventListener("load", function () { setTimeout(run, 200); }); }
})();
</script>
"""

BLOCK = re.compile(r<script>\n/\* JHPRICE-HOOK \*/.*?<\/script>\n", re.S)


def main():
    idx = os.path.join(ROOT, "index.html")
    with open(idx, "r", encoding="utf-8") as f:
        html = f.read()

    if MARK in html:
        new_html, n = BLOCK.subn(SNIPPET, html, count=1)
        if n != 1:
            raise SystemExit("hook marker present but block not matched")
        html = new_html
        print("hook updated")
    else:
        if "</body>" not in html:
            raise SystemExit("no </body> marker, abort")
        html = html.replace("</body>", SNIPPET + "</body>", 1)
        print("hook inserted")

    with open(idx, "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html bytes:", os.path.getsize(idx))


if __name__ == "__main__":
    main()
