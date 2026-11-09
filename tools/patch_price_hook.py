# -*- coding: utf-8 -*-
# 在 index.html 末尾插入运行时钩子：打开页面先拉 price.json，取到就用最新收盘价
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "JHPRICE-HOOK"

SNIPPET = """
<script>
/* JHPRICE-HOOK */
(function () {
  function apply(d) {
    try {
      if (!d || !d.date || !d.price || !window.HIST || !window.state) return;
      var paid = (state.manual && state.manual > 0);
      var h = (d.hist && d.hist.length > 4) ? d.hist : null;
      if (h) {
        var cur = HIST.length ? HIST[HIST.length - 1].d : "";
        if (!cur || h[h.length - 1].d > cur) {
          HIST.length = 0;
          for (var i = 0; i < h.length; i++) { HIST.push({ d: h[i].d, c: h[i].c }); }
        }
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


def main():
    idx = os.path.join(ROOT, "index.html")
    with open(idx, "r", encoding="utf-8") as f:
        html = f.read()

    if MARK in html:
        print("hook already present")
        return
    if "</body>" not in html:
        raise SystemExit("no </body> marker, abort")

    html = html.replace("</body>", SNIPPET + "</body>", 1)
    with open(idx, "w", encoding="utf-8") as f:
        f.write(html)
    print("hook inserted, index.html bytes:", os.path.getsize(idx))


if __name__ == "__main__":
    main()
