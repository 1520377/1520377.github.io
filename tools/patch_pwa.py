# -*- coding: utf-8 -*-
# 给单页 app 补上 manifest / 图标 / service worker，让 Android Chrome 以独立窗口安装
import os, struct, zlib, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (18, 16, 13)
GOLD = (217, 171, 85)
GOLD2 = (240, 205, 132)
SHADOW = (184, 144, 31)


def px_color(u, v):
    m, r = 0.05, 0.17
    x0, x1, y0, y1 = m, 1 - m, m, 1 - m
    if u < x0 or u > x1 or v < y0 or v > y1:
        return None
    dx = max(x0 + r - u, 0.0, u - (x1 - r))
    dy = max(y0 + r - v, 0.0, v - (y1 - r))
    if dx * dx + dy * dy > r * r:
        return None
    if 0.40 <= v <= 0.645:
        t = (v - 0.40) / 0.245
        hw = 0.155 + 0.075 * t
        if abs(u - 0.5) <= hw:
            if v > 0.615:
                return SHADOW
            return GOLD2 if t < 0.16 else GOLD
    du = (u - 0.5) / 0.158
    dv = (v - 0.40) / 0.058
    if du * du + dv * dv <= 1.0:
        return GOLD2
    return BG


def render(size, ss=3):
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            acc = [0, 0, 0, 0]
            for sy in range(ss):
                for sx in range(ss):
                    u = (x + (sx + 0.5) / ss) / size
                    v = (y + (sy + 0.5) / ss) / size
                    c = px_color(u, v)
                    if c is None:
                        continue
                    acc[0] += c[0]
                    acc[1] += c[1]
                    acc[2] += c[2]
                    acc[3] += 1
            n = acc[3]
            if n == 0:
                row.append((0, 0, 0, 0))
            else:
                row.append((acc[0] // n, acc[1] // n, acc[2] // n, 255 * n // (ss * ss)))
        rows.append(row)
    return rows


def write_png(path, rows):
    size = len(rows)
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in rows)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)

    data = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


MANIFEST = {
    "name": "金衡 · 金价与资产管家",
    "short_name": "金衡",
    "id": "/",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#12100D",
    "theme_color": "#12100D",
    "lang": "zh-CN",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}

SW_JS = (
    'self.addEventListener("install", function () { self.skipWaiting(); });\n'
    'self.addEventListener("activate", function (e) { e.waitUntil(self.clients.claim()); });\n'
    'self.addEventListener("fetch", function () {});\n'
)

HEAD_BLOCK = (
    '<meta name="theme-color" content="#12100D">\n'
    '<link rel="manifest" href="manifest.json">\n'
    '<link rel="apple-touch-icon" href="icon-192.png">\n'
)

BODY_BLOCK = (
    '<script>if("serviceWorker" in navigator && location.protocol === "https:"){' \n    
)


def main():
    idx = os.path.join(ROOT, "index.html")
    with open(idx, "r", encoding="utf-8") as f:
        html = f.read()

    if 'rel="manifest"' in html:
        print("html already patched")
    else:
        if "</head>" not in html and "<body" not in html:
            raise SystemExit("no head/body marker, abort")
        anchor = "</head>" if "</head>" in html else "<body"
        html = html.replace(anchor, HEAD_BLOCK + anchor, 1)
        sw = ('<script>if("serviceWorker" in navigator && location.protocol === "https:"){'
              'addEventListener("load",function(){navigator.serviceWorker.register("sw.js",{scope:"./"})'
              '.catch(function(){});});}</script>\n')
        if "</body>" in html:
            html = html.replace("</body>", sw + "</body>", 1)
        else:
            html = html.replace("</html>", sw + "</html>", 1)
        with open(idx, "w", encoding="utf-8") as f:
            f.write(html)
        print("html patched")

    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(MANIFEST, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT, "sw.js"), "w", encoding="utf-8") as f:
        f.write(SW_JS)

    for size in (192, 512):
        rows = render(size)
        write_png(os.path.join(ROOT, "icon-%d.png" % size), rows)
        print("icon-%d.png written" % size)

    print("index.html bytes:", os.path.getsize(idx))


if __name__ == "__main__":
    main()
