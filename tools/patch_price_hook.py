# -*- coding: utf-8 -*-
# 维护首页行情区：盘中价（东财上金所 AU9999 实时）+ 收盘价 + 金店挂牌价（price.json）
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "JHPRICE-HOOK"
HEAD = "<script>\n/* JHPRICE-HOOK */"
TAIL = "</script>"
ANCHOR = '<div id="pDelta"></div>'
BOX = '<div id="jhQuote"></div>'

STYLE = """<style>
#jhQuote{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:12.5px;line-height:1.6;color:var(--mute2)}
#jhQuote>span{display:inline-flex;align-items:baseline;gap:5px}
#jhQuote em{font-style:normal;color:var(--mute2)}
#jhQuote b{font-weight:600;font-size:16px;color:var(--text);font-variant-numeric:tabular-nums}
#jhQuote>span:first-child b{color:var(--gold)}
</style>
"""

SNIPPET = STYLE + """
<script>
/* JHPRICE-HOOK */
(function () {
  var LIVE_URL = "https://push2.eastmoney.com/api/qt/stock/get?secid=118.AU9999&fields=f43,f59,f86&ut=fa5fd1943c7b386f172d6893dbfba10b";
  var closeInfo = null, liveInfo = null, busy = false, sig = "";

  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  function bj(sec) { return new Date(sec * 1000 + 8 * 3600 * 1000); }
  function hhmm(sec) { var d = bj(sec); return pad(d.getUTCHours()) + ":" + pad(d.getUTCMinutes()); }
  function todayStr() {
    var d = bj(Math.floor(Date.now() / 1000));
    return d.getUTCFullYear() + "-" + pad(d.getUTCMonth() + 1) + "-" + pad(d.getUTCDate());
  }
  function f2(v) { return (Math.round(v * 100) / 100).toFixed(2); }
  function f0(v) { var n = Math.round(v * 10) / 10; return (n % 1 === 0) ? String(n) : n.toFixed(1); }
  function mmdd(s) { return s ? s.slice(5) : ""; }
  function typing() {
    var a = document.activeElement;
    return !!a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName);
  }
  function rerender() {
    var s = state.basePrice + "|" + state.baseDate + "|" +
      (HIST.length ? HIST[HIST.length - 1].d + "|" + HIST[HIST.length - 1].c : "");
    if (s === sig) return;
    sig = s;
    if (!typing() && typeof saveLocal === "function") { saveLocal(); }
    if (!typing() && typeof renderAll === "function") { renderAll(); }
  }

  function paint() {
    var box = document.getElementById("jhQuote");
    if (box) {
      var html = "";
      if (liveInfo && liveInfo.fresh) {
        html += '<span><em>盘中</em><b>' + f2(liveInfo.p) + '</b><em>' + hhmm(liveInfo.t) + '</em></span>';
      }
      if (closeInfo) {
        html += '<span><em>收盘</em><b>' + f2(closeInfo.p) + '</b><em>' + mmdd(closeInfo.d) + '</em></span>';
        if (closeInfo.jew && closeInfo.jew.price) {
          html += '<span><em>金店</em><b>' + f0(closeInfo.jew.price) + '</b><em>' +
            (closeInfo.jew.brand || "") + (closeInfo.jew.date ? ' ' + mmdd(closeInfo.jew.date) : '') + '</em></span>';
        }
      }
      box.innerHTML = html;
    }
    var pd = document.getElementById("priceDate");
    if (pd && !(state.manual > 0)) {
      if (liveInfo && liveInfo.fresh) { pd.textContent = "盘中 · " + hhmm(liveInfo.t); }
      else if (closeInfo) { pd.textContent = closeInfo.d + " 收盘"; }
    }
  }

  function applyClose(d) {
    if (!d || !d.date || !d.price) return;
    closeInfo = { d: d.date, p: d.price, jew: d.jew || null };
    if (d.hist && d.hist.length >= 5) {
      var cur = HIST.length ? HIST[HIST.length - 1].d : "";
      if (!cur || d.hist[d.hist.length - 1].d > cur) {
        HIST.length = 0;
        for (var i = 0; i < d.hist.length; i++) { HIST.push({ d: d.hist[i].d, c: d.hist[i].c }); }
      }
    }
    var fresh = liveInfo && liveInfo.fresh;
    if (!fresh && !(state.manual > 0) && (!state.baseDate || d.date > state.baseDate)) {
      state.basePrice = d.price;
      state.baseDate = d.date;
    }
    rerender();
    paint();
  }

  function applyLive(d) {
    if (!d || !d.data || typeof d.data.f43 !== "number") return;
    var scale = Math.pow(10, d.data.f59 || 2);
    var p = d.data.f43 / scale;
    var t = d.data.f86 || 0;
    if (!(p > 0) || !t) return;
    liveInfo = { p: p, t: t, fresh: (Date.now() / 1000 - t) < 1800 };
    if (liveInfo.fresh && !(state.manual > 0)) {
      var today = todayStr();
      if (!HIST.length || HIST[HIST.length - 1].d !== today) { HIST.push({ d: today, c: p }); }
      else { HIST[HIST.length - 1].c = p; }
      state.basePrice = p;
      state.baseDate = today;
      rerender();
    }
    paint();
  }

  function pull() {
    if (busy) return;
    busy = true;
    var done = function () { busy = false; };
    try {
      fetch("price.json?t=" + Date.now(), { cache: "no-store" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { try { applyClose(d); } catch (e) {} })
        .then(function () {
          return fetch(LIVE_URL + "&_=" + Date.now(), { cache: "no-store" })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (d) { try { applyLive(d); } catch (e) {} });
        })
        .catch(function () {})
        .then(done);
    } catch (e) { done(); }
  }

  if (document.readyState === "complete") { setTimeout(pull, 150); }
  else { window.addEventListener("load", function () { setTimeout(pull, 150); }); }
  setInterval(pull, 60000);
  document.addEventListener("visibilitychange", function () { if (!document.hidden) { pull(); } });
})();
</script>
"""


def main():
    idx = os.path.join(ROOT, "index.html")
    html = open(idx, "r", encoding="utf-8").read()

    i = html.find(HEAD)
    if i >= 0:
        j = html.find(TAIL, i)
        if j < 0:
            raise SystemExit("hook open tag without close tag")
        j += len(TAIL)
        html = html[:i] + html[j:]

    html = html.replace(BOX, "")

    if html.count(ANCHOR) != 1:
        raise SystemExit("anchor not unique: %d" % html.count(ANCHOR))
    html = html.replace(ANCHOR, ANCHOR + "\n      " + BOX, 1)

    if "</body>" not in html:
        raise SystemExit("no </body>")
    html = html.replace("</body>", SNIPPET + "</body>", 1)

    open(idx, "w", encoding="utf-8").write(html)
    print("ok | bytes:", os.path.getsize(idx), "| markers:", html.count(MARK), "| box:", html.count(BOX))


if __name__ == "__main__":
    main()
