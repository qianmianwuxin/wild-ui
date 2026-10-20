# 荒野求食 · 海陆数据的构建脚本（land-v1）
# 用法：pip install global-land-mask numpy；python3 build-land.py
#   输出 land-v1.bin.gz，放到 wild-ui 仓库的 main 分支根目录；游戏的开局脚本只下载它、自己读，不用装程序包
# 格式：0.05° 一格，3600 行 × 7200 列，从北纬 90° 往南、从西经 180° 往东逐行排；每格取格子中心点判海陆，陆地记 1；
#   按行优先、高位在前压成位，再 gzip
import numpy as np, gzip
from global_land_mask import globe
RES = 0.05; H, W = int(180 / RES), int(360 / RES)
lat = 90 - (np.arange(H) + 0.5) * RES
lon = -180 + (np.arange(W) + 0.5) * RES
m = np.array([globe.is_land(np.full(W, lat[i]), lon) for i in range(H)], dtype=bool)
bits = np.packbits(m.reshape(-1))
with gzip.open('land-v1.bin.gz', 'wb', compresslevel=9) as f: f.write(bits.tobytes())
print(H, W, round(float(m.mean()), 4), len(bits))
