# -*- coding: utf-8 -*-
# 抓取上海金 Au99.99 日线收盘价，生成 price.json 供页面打开时读取
import os, re, json, urllib.request, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://vip.stock.finance.sina.com.cn/q/view/vGold_History.php?breed=AU9999"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"}
KEEP = 22


def fetch_html():
    req = urllib.request.Request(URL, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    return raw.decode("gbk", "replace")


def parse(html):
    seen = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) < 6 or not re.match(r"^\d{4}-\d{2}-\d{2}$", cells[0]):
            continue
        try:
            seen[cells[0]] = float(cells[5].replace(",", ""))
        except ValueError:
            continue
    items = [{"d": k, "c": v} for k, v in sorted(seen.items())]
    return items[-KEEP:]


def main():
    hist = parse(fetch_html())
    if len(hist) < 5:
        raise SystemExit("parse failed: only %d rows" % len(hist))

    data = {
        "date": hist[-1]["d"],
        "price": hist[-1]["c"],
        "hist": hist,
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    path = os.path.join(ROOT, "price.json")
    old = None
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                old = json.load(f)
        except Exception:
            old = None

    if old and old.get("date") == data["date"] and old.get("price") == data["price"] \
            and len(old.get("hist") or []) == len(hist):
        print("unchanged: %s %.2f" % (data["date"], data["price"]))
        return

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("updated: %s %.2f (rows %d)" % (data["date"], data["price"], len(hist)))


if __name__ == "__main__":
    main()
