# 荒野求食 · 作品库的构建脚本（works-v3）
# 用法：python3 build-works-v3.py dump-XXXX.zip myth.json classic.json
#   dump 从 https://github.com/bangumi/Archive/releases/tag/archive 下载（最新地址见该仓库 aux/latest.json）
#   myth.json、classic.json 是另编的神话传说与民间故事、古典文学清单，放在仓库的 worksdata 文件夹
#   输出 works-v3.json.gz，放到 wild-ui 仓库的 main 分支根目录；游戏脚本只下载它、自己读，不执行下载来的代码
# 数据来自 Bangumi 番组计划（bgm.tv）每周导出；只取名称、年份、类型、标签与主要角色名。
import json, re, gzip, collections, sys, zipfile, io
Z = zipfile.ZipFile(sys.argv[1])
def lines(name):
    with Z.open(name) as f:
        for line in io.TextIOWrapper(f, encoding="utf-8"):
            yield json.loads(line)
REG = {
 'CN': ['中国','国产','华语','香港','台湾','中国大陆','国漫','国创','大陆','港剧','台剧','国剧','内地','中国动画','国产动画','国产游戏','国产剧','华语剧','网络小说','起点','晋江'],
 'JP': ['日本','日剧','日漫','轻小说','日本动画','日系'],
 'KR': ['韩国','韩剧','韩漫'],
 'EU': ['英国','法国','德国','意大利','西班牙','俄罗斯','苏联','波兰','瑞典','挪威','丹麦','芬兰','荷兰','比利时','捷克','爱尔兰','欧洲','乌克兰','奥地利','瑞士','葡萄牙','匈牙利','希腊'],
 'NA': ['美国','加拿大','好莱坞','美剧','美漫','DC漫画','漫威','Marvel'],
 'OT': ['印度','泰国','巴西','澳大利亚','新西兰','墨西哥','阿根廷','越南','印尼','印度尼西亚','菲律宾','马来西亚','新加坡','伊朗','土耳其','以色列','埃及','南非','智利','哥伦比亚'],
}
BOTH_WEST = ['欧美','西方','欧美剧','美英']
GEN = {
 1: ['奇幻','魔法','异世界','西幻','剑与魔法','Fantasy','魔幻','奇幻冒险','DND','跑团'],
 2: ['科幻','SF','机战','赛博朋克','太空','宇宙','星际','机甲','太空歌剧','硬科幻','时间旅行'],
 3: ['玄幻','仙侠','武侠','修仙','东方幻想','修真','东方玄幻','古风奇幻','国风奇幻'],
 4: ['冒险','探险','生存','求生','荒野','野外','航海','寻宝'],
 5: ['末世','末日','废土','丧尸','后启示录','僵尸','灾难','末日题材','核战'],
 6: ['神话','妖怪','志怪','神明','民俗','鬼怪','怪谈','神鬼','聊斋','山海经','克苏鲁'],
 7: ['历史','古装','战国','三国','时代剧','大河剧','历史剧','二战','幕末','宫廷','架空历史'],
}
def regions(mt, tags):
    s=set(mt)|set(tags[:15])
    out=set()
    for k,ws in REG.items():
        if any(w in s for w in ws): out.add(k)
    if any(w in s for w in BOTH_WEST) and not ({'EU','NA'}&out): out|={'EU','NA'}
    return out
def genres(mt, tags):
    s=set(mt)|set(tags[:20])
    out={g for g,ws in GEN.items() if any(w in s for w in ws)}
    return out or {8}
def era(y):
    try: y=int(y)
    except: return None
    if y<1980: return 1
    if y<=1994: return 2
    if y<=2004: return 3
    if y<=2012: return 4
    if y<=2018: return 5
    return 6

def media(s):
    t, p = s["type"], s.get("platform")
    if t == 2: return "A"
    if t == 1 and p == 1001: return "A"
    if t == 4 and p in (4001, 0): return "G"
    if t == 1 and p == 1002: return "N"
    if t == 6 and p in (1, 2, 3, 6001, 6002, 0): return "F"
    return None
kana = re.compile("[\u3040-\u30ff]"); hang = re.compile("[\uac00-\ud7af]")
def signals(s):
    ib, nm, sig = s.get("infobox") or "", s.get("name") or "", set()
    if kana.search(nm): sig.add("kana")
    if hang.search(nm): sig.add("hangul")
    if "円" in ib or "税込" in ib or "税別" in ib or "税抜" in ib: sig.add("yen")
    if "NT$" in ib: sig.add("ntd")
    if "￦" in ib or "원" in ib: sig.add("krw")
    if "人民币" in ib or "RMB" in ib or "元" in ib.split("售价")[-1][:60]: sig.add("rmb")
    m = re.search(r"\|国家/地区=\s*([^\r\n|]+)", ib) or re.search(r"\|(?:国家|地区|制片国家/地区)=\s*([^\r\n|]+)", ib)
    if m: sig.add("C:" + m.group(1).strip())
    return sig
rows, extra = [], {}
for s in lines("subject.jsonlines"):
    m = media(s)
    if not m or s.get("nsfw"): continue
    mt = s.get("meta_tags") or []
    if "R18" in mt: continue
    fav = s.get("favorite") or {}
    pop = fav.get("done", 0) + fav.get("doing", 0) + fav.get("on_hold", 0) + fav.get("wish", 0)
    tags = [t["name"] for t in (s.get("tags") or [])]
    rows.append((s["id"], m, s.get("name"), s.get("name_cn"), (s.get("date") or "")[:4], mt, tags, pop, s.get("score"), s.get("type"), s.get("platform")))
    extra[s["id"]] = signals(s)
TH = {'A': 500, 'N': 100, 'G': 120, 'F': 80}
MCODE = {'A': 1, 'G': 2, 'N': 3, 'F': 4}
ADULT = {'R18', '18禁', '里番', '成人', 'H', '工口', 'エロゲ', '拔作', '黄油', 'NTR', '凌辱'}
CMAP = [('中国', 1), ('香港', 1), ('台湾', 1), ('臺灣', 1), ('中國', 1), ('日本', 2), ('韩国', 3), ('韓國', 3),
        ('美国', 5), ('USA', 5), ('United States', 5), ('加拿大', 5), ('英国', 4), ('UK', 4), ('英國', 4), ('法国', 4),
        ('德国', 4), ('意大利', 4), ('西班牙', 4), ('俄罗斯', 4), ('苏联', 4), ('波兰', 4), ('瑞典', 4), ('爱尔兰', 4),
        ('澳大利亚', 6), ('新西兰', 6), ('印度', 6), ('泰国', 6), ('巴西', 6), ('墨西哥', 6)]
RCODE = {'CN': 1, 'JP': 2, 'KR': 3, 'EU': 4, 'NA': 5, 'OT': 6}
def region(r, sig):
    out = set()
    for s in sig:
        if s.startswith('C:'):
            for k, v in CMAP:
                if k in s: out.add(v)
    if out: return out
    s = set(r[5]) | set(r[6][:15])
    for k, ws in REG.items():
        if any(w in s for w in ws): out.add(RCODE[k])
    if not out and any(w in s for w in BOTH_WEST): out |= {4, 5}
    if out: return out
    if 'kana' in sig or 'yen' in sig: return {2}
    if 'hangul' in sig or 'krw' in sig: return {3}
    if 'rmb' in sig or 'ntd' in sig: return {1}
    if {'Galgame', 'galgame', 'GAL'} & s: return {2}  # 没有别的线索的美少女游戏，几乎都是日本的
    return set()
def genres(r):
    s = set(r[5]) | set(r[6][:20])
    out = {g for g, ws in GEN.items() if any(w in s for w in ws)}
    return out or {8}
VOL = re.compile(r'[\(（]\s*\d+\s*[\)）]|\s\d+\s*$|第\s*[0-9一二三四五六七八九十百]+\s*[卷册部巻]|[Vv]ol\.?\s*\d+|\d+巻|[上中下]卷?$')
works = []
for r in rows:
    if r[7] < TH[r[1]]: continue
    if r[9] == 2 and r[10] not in (1, 3, 5): continue
    if r[9] == 1 and (VOL.search(r[2] or '') or VOL.search(r[3] or '')): continue
    if ADULT & (set(r[5]) | set(r[6][:20])): continue
    rg = region(r, extra.get(r[0], set()))
    if not rg: continue
    e = era(r[4])
    if not e: continue
    name_cn = (r[3] or '').strip(); name = (r[2] or '').strip()
    works.append([r[0], name_cn or name, name if name_cn and name != name_cn else '', int(r[4]), MCODE[r[1]],
                  sorted(rg), sorted(genres(r)), r[7]])
ids = {w[0] for w in works}
print('works', len(works), collections.Counter(w[4] for w in works))
# characters
rel = collections.defaultdict(list)
for x in lines('subject-characters.jsonlines'):
        if x['subject_id'] in ids and x.get('type') in (1, 2):
            rel[x['subject_id']].append((x['type'], x.get('order', 0), x['character_id']))
need = {c for v in rel.values() for _, _, c in v}
cname = {}
zh = re.compile(r'\|简体中文名=\s*([^\r\n|]+)')
for x in lines('character.jsonlines'):
        if x['id'] in need and x.get('role') == 1:
            m = zh.search(x.get('infobox') or '')
            cname[x['id']] = (m.group(1).strip() if m and m.group(1).strip() else x['name']).strip()
chars = {}
for sid, v in rel.items():
    v.sort(); seen = []; 
    for _, _, c in v:
        n = cname.get(c)
        if n and n not in seen: seen.append(n)
        if len(seen) >= 12: break
    if seen: chars[str(sid)] = seen
print('with chars', len(chars))

# ── 后半段：并入神话、古典，按格预先放宽、带权重 ──
import math, os
myth = json.load(open(sys.argv[2], encoding='utf-8'))
classic = json.load(open(sys.argv[3], encoding='utf-8'))
M = {1: "动画与漫画", 2: "游戏", 3: "小说", 4: "电影与剧集", 5: "神话传说与民间故事", 6: "古典文学"}
Dn = {1: "中国（含港澳台）", 2: "日本", 3: "韩国", 4: "欧洲", 5: "北美", 6: "其他地区"}
E = {0: "不限", 1: "1980 年前", 2: "1980–1994", 3: "1995–2004", 4: "2005–2012", 5: "2013–2018", 6: "2019 年后"}
G = {1: "奇幻", 2: "科幻", 3: "东方幻想", 4: "冒险", 5: "末世与废土", 6: "神话志怪", 7: "历史", 8: "其他"}
# 统一成 [编号, 显示名, 年份, 媒介, 地区, 题材, 权重]
rows3 = []
for w in works:
    orig = f"，原名 {w[2]}" if w[2] else ""
    rows3.append([w[0], f"{w[1]}（{w[3]} 年{orig}）", w[3], w[4], w[5], w[6], math.sqrt(w[7])])
def yr(y): return f"约公元前 {-y} 年" if y < 0 else f"约 {y} 年"
for base, m, lst in [(9000001, 5, myth), (9100001, 6, classic)]:
    for k, x in enumerate(lst):
        sid = base + k
        orig = f"，原名 {x['orig']}" if x['orig'] else ""
        disp = f"{x['name']}（{yr(x['year'])}{orig}）" if m == 6 else (f"{x['name']}（原名 {x['orig']}）" if x['orig'] else x['name'])
        rows3.append([sid, disp, x['year'], m, x['regions'], x['themes'], math.sqrt(x['weight'])])
        chars[str(sid)] = x['chars']
CAP = 400; used, cells = {}, {}
def hit(m, eras, gs, rs):
    return [i for i, w in enumerate(rows3) if w[3] == m and set(w[4]) & rs and (not eras or era(w[2]) in eras) and set(w[5]) & gs]
for m in M:
    for r in Dn:
        for e in (range(7) if m <= 4 else [0]):
            for g in G:
                eras = {e} if e else set(); gs, rs, path = {g}, {r}, []
                res = hit(m, eras, gs, rs); k = 1
                while e and len(res) < 8 and len(eras) < 6:
                    eras = {x for x in range(e - k, e + k + 1) if 1 <= x <= 6}; res = hit(m, eras, gs, rs); k += 1
                if e and len(eras) > 1:
                    path.append("年代放宽到" + ("不限" if len(eras) == 6 else "、".join(E[x] for x in sorted(eras))))
                if len(res) < 8: gs = set(G); res = hit(m, eras, gs, rs); path.append("题材放宽到不限")
                # 地区不放宽：规则里道具来源不离开这个地区，开局和 Tips 也是最后才放宽地区，作品库不替 DM 跳到别的地区
                head = f"作品库：{M[m]}｜{Dn[r]}｜{E[e]}｜{G[g]}；这一格共 {len(res)} 部" + ("；" + "，".join(path) if path else "")
                if len(res) < 8: head += "；作品库里这个地区的作品不够，照规则在这一格里自己补" if res else "；作品库里这个地区没有这一类作品，照规则在这一格里自己列"
                res = sorted(res, key=lambda i: -rows3[i][6])[:CAP]
                idx = []
                for i in res:
                    if i not in used: used[i] = len(used)
                    idx.append(used[i])
                cells[f"{m}{r}{e}{g}"] = [head, idx]
inv = sorted(used, key=used.get)
w3 = [[rows3[i][0], rows3[i][1], round(rows3[i][6], 1)] for i in inv]
keep = {str(rows3[i][0]) for i in inv}
out = {"v": 3, "src": "Bangumi 番组计划（bgm.tv）每周导出 " + sys.argv[1].split('/')[-1] + "（媒介 1–4，只取名称、年份、类型、标签与主要角色名）；神话传说与民间故事、古典文学为另编清单（媒介 5–6）",
       "w": w3, "c": cells, "ch": {k: v for k, v in chars.items() if k in keep}}
s = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
with gzip.open('works-v3.json.gz', 'wt', encoding='utf-8', compresslevel=9) as f: f.write(s)
print(len(w3), len(cells), len(s), os.path.getsize('works-v3.json.gz'))
