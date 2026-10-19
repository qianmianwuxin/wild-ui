# 荒野求食 · 作品库（works-v1）
# 数据来自 Bangumi 番组计划（bgm.tv）每周导出，只取名称、年份、类型、标签与主要角色名。
# 用法：works(媒介骰, 地区骰, 年代骰, 题材骰)；年代填 0 表示不限年代。chars(作品编号) 列出这部作品的主要角色。
import json, gzip, os, math, random, urllib.request
_R = random.SystemRandom()
_URL = "https://raw.githubusercontent.com/qianmianwuxin/wild-ui/main/works-v1.json.gz"
_P = "/tmp/works-v1.json.gz"
_M = {1: "动画与漫画", 2: "游戏", 3: "小说", 4: "电影与剧集", 5: "神话传说与民间故事", 6: "古典文学"}
_D = {1: "中国（含港澳台）", 2: "日本", 3: "韩国", 4: "欧洲", 5: "北美", 6: "其他地区"}
_E = {0: "不限", 1: "1980 年前", 2: "1980–1994", 3: "1995–2004", 4: "2005–2012", 5: "2013–2018", 6: "2019 年后"}
_G = {1: "奇幻", 2: "科幻", 3: "东方幻想", 4: "冒险", 5: "末世与废土", 6: "神话志怪", 7: "历史", 8: "其他"}
_DB = None
def _load():
    global _DB
    if _DB is None:
        for _ in range(2):
            try:
                if not os.path.exists(_P):
                    urllib.request.urlretrieve(_URL, _P)
                _DB = json.load(gzip.open(_P, "rt", encoding="utf-8"))
                break
            except (OSError, ValueError, EOFError):
                if os.path.exists(_P):
                    os.remove(_P)
        if _DB is None:
            raise OSError("作品库下载失败")
    return _DB
def _era(y):
    return 1 if y < 1980 else 2 if y <= 1994 else 3 if y <= 2004 else 4 if y <= 2012 else 5 if y <= 2018 else 6
def _same(a, b):
    a, b = a[1], b[1]
    return a[:4] == b[:4] or a in b or b in a
def _pick(rows, n):
    rows, out = list(rows), []
    while rows and len(out) < n:
        w = [math.sqrt(r[7]) for r in rows]
        x = _R.uniform(0, sum(w))
        for i, wi in enumerate(w):
            x -= wi
            if x <= 0:
                break
        r = rows.pop(i)
        if not any(_same(r, o) for o in out):
            out.append(r)
    return out
def works(m, r, e, g, n=12, least=8):
    if m not in (1, 2, 3, 4):
        print(f"作品库：{_M.get(m, m)}不在作品库里，照原来的办法自己列")
        return
    db = _load()
    def hit(eras, gs, rs):
        return [w for w in db["works"] if w[4] == m and set(w[5]) & rs and (not eras or _era(w[3]) in eras) and set(w[6]) & gs]
    eras = {e} if e else set()
    gs, rs, path = {g}, {r}, []
    rows = hit(eras, gs, rs)
    k = 1
    while e and len(rows) < least and len(eras) < 6:
        eras = {x for x in range(e - k, e + k + 1) if 1 <= x <= 6}
        rows = hit(eras, gs, rs)
        k += 1
    if e and len(eras) > 1:
        path.append("年代放宽到" + ("不限" if len(eras) == 6 else "、".join(_E[x] for x in sorted(eras))))
    if len(rows) < least:
        gs = set(_G); rows = hit(eras, gs, rs); path.append("题材放宽到不限")
    if len(rows) < least:
        rs = set(_D); rows = hit(eras, gs, rs); path.append("地区放宽到不限")
    print(f"作品库：{_M[m]}｜{_D[r]}｜{_E[e]}｜{_G[g]}；这一格共 {len(rows)} 部" + ("；" + "，".join(path) if path else ""))
    for i, w in enumerate(_pick(rows, n), 1):
        orig = f"，原名 {w[2]}" if w[2] else ""
        print(f"{i}. {w[1]}（{w[3]} 年{orig}）〔{w[0]}〕")
def chars(sid, n=12):
    cs = list(_load()["chars"].get(str(sid), []))
    _R.shuffle(cs)
    print(f"作品库里〔{sid}〕的主要角色（次序已打乱）：" + ("、".join(cs[:n]) if cs else "没有收录，自己列"))
