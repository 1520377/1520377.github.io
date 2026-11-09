# -*- coding: utf-8 -*-
# 每日生成 price.json：上金所 Au99.99 收盘与近期日线 + 金店挂牌价
import os, re, json, urllib.request, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOSE_URL = "http://vip.stock.finance.sina.com.cn/q/view/vGold_History.php?breed=AU9999"
JEW_URL = "https://www.huangjinjiage.cn/"
BRANDS = ("内地周大福", "内地老凤祥")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"}
KEEP = 22


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def decode(raw):
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def rows(html):
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        yield cells


def parse_close(html):
    seen = {}
    for cells in rows(html):
        if len(cells) < 6 or not re.match(r"^\d{4}-\d{2}-\d{2}$", cells[0]):
            continue
        try:
            seen[cells[0]] = float(cells[5].replace(",", ""))
        except ValueError:
            continue
    return [{"d": k, "c": v} for k, v in sorted(seen.items())][-KEEP:]


def norm_date(s):
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s or "")
    if not m:
        return ""
    return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))


def parse_jew(html):
    quote_date = ""
    m = re.search(r'class="daTime"[^>]*>([0-9]{4}-[0-9]{1,2}-[0-9]{1,2})<', html)
    if m:
        quote_date = norm_date(m.group(1))
    for cells in rows(html):
        if not cells or cells[0] not in BRANDS:
            continue
        for c in cells[1:]:
            v = c.replace(",", "")
            if re.match(r"^[0-9]+(?:\.[0-9]+)?$", v):
                p = float(v)
                if 500 <= p <= 3000:
                    return {"brand": cells[0].replace("内地", ""), "price": p, "date": quote_date}
    return None


def main():
    close = parse_close(decode(fetch(CLOSE_URL)))
    if len(close) < 5:
        raise SystemExit("close parse failed: %d rows" % len(close))

    jew = None
    try:
        jew = parse_jew(decode(fetch(JEW_URL, 20)))
    except Exception as e:
        print("jew fetch failed:", type(e).__name__)

    path = os.path.join(ROOT, "price.json")
    old = None
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                old = json.load(f)
        except Exception:
            old = None

    if jew is None and old and old.get("jew"):
        jew = old["jew"]
        print("jew kept from previous file")

    data = {
        "date": close[-1]["d"],
        "price": close[-1]["c"],
        "hist": close,
        "jew": jew,
        "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    same = (old and old.get("date") == data["date"] and old.get("price") == data["price"]
            and len(old.get("hist") or []) == len(close)
            and (old.get("jew") or {}).get("price") == (jew or {}).get("price"))
    if same:
        print("unchanged: %s %.2f" % (data["date"], data["price"]))
        return

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("updated: close %s %.2f | jew %s" % (data["date"], data["price"], jew))


if __name__ == "__main__":
    main()
