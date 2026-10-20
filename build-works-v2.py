# 从 works-v1.json.gz 生成 works-v2.json.gz：只有数据，按格预先放宽好，游戏里不再执行下载来的代码
import gzip, json, math
db = json.load(gzip.open('works-v1.json.gz', 'rt', encoding='utf-8'))
M = {1: "动画与漫画", 2: "游戏", 3: "小说", 4: "电影与剧集"}
Dn = {1: "中国（含港澳台）", 2: "日本", 3: "韩国", 4: "欧洲", 5: "北美", 6: "其他地区"}
E = {0: "不限", 1: "1980 年前", 2: "1980–1994", 3: "1995–2004", 4: "2005–2012", 5: "2013–2018", 6: "2019 年后"}
G = {1: "奇幻", 2: "科幻", 3: "东方幻想", 4: "冒险", 5: "末世与废土", 6: "神话志怪", 7: "历史", 8: "其他"}
era = lambda y: 1 if y < 1980 else 2 if y <= 1994 else 3 if y <= 2004 else 4 if y <= 2012 else 5 if y <= 2018 else 6
W = db['works']; CAP = 400
used, cells = {}, {}
def hit(m, eras, gs, rs):
    return [i for i, w in enumerate(W) if w[4] == m and set(w[5]) & rs and (not eras or era(w[3]) in eras) and set(w[6]) & gs]
for m in M:
    for r in Dn:
        for e in range(7):
            for g in G:
                eras = {e} if e else set(); gs, rs, path = {g}, {r}, []
                rows = hit(m, eras, gs, rs); k = 1
                while e and len(rows) < 8 and len(eras) < 6:
                    eras = {x for x in range(e - k, e + k + 1) if 1 <= x <= 6}; rows = hit(m, eras, gs, rs); k += 1
                if e and len(eras) > 1:
                    path.append("年代放宽到" + ("不限" if len(eras) == 6 else "、".join(E[x] for x in sorted(eras))))
                if len(rows) < 8: gs = set(G); rows = hit(m, eras, gs, rs); path.append("题材放宽到不限")
                if len(rows) < 8: rs = set(Dn); rows = hit(m, eras, gs, rs); path.append("地区放宽到不限")
                head = f"作品库：{M[m]}｜{Dn[r]}｜{E[e]}｜{G[g]}；这一格共 {len(rows)} 部" + ("；" + "，".join(path) if path else "")
                rows = sorted(rows, key=lambda i: -W[i][7])[:CAP]
                idx = []
                for i in rows:
                    if i not in used: used[i] = len(used)
                    idx.append(used[i])
                cells[f"{m}{r}{e}{g}"] = [head, idx]
inv = sorted(used, key=used.get)
w2 = []
for i in inv:
    w = W[i]; orig = f"，原名 {w[2]}" if w[2] else ""
    w2.append([w[0], f"{w[1]}（{w[3]} 年{orig}）", round(math.sqrt(w[7]), 1)])
out = {"v": 2, "src": db.get("src"), "w": w2, "c": cells, "ch": db["chars"]}
s = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
with gzip.open('works-v2.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f: f.write(s)
import os; print(len(w2), len(cells), len(s), os.path.getsize('works-v2.json.gz'))
