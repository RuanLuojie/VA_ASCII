"""
把圖轉成高清 ASCII 圖（PNG）。
每一格拿真實字形的點陣圖去比對原圖那一塊，選最像的字；不是只看那一塊的平均亮度，
所以線條的方向、轉角、粗細都對得上。輸出一律存 PNG：JPG 會讓文字邊緣出現雜點。
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSansMono-Bold.ttf")
CELL_W, CELL_H = 6, 12  # 比對用的每格像素；DejaVu Sans Mono 的字寬:行高約 1:2


def get_args():
    parser = argparse.ArgumentParser("Image to high-definition ASCII (PNG)")
    parser.add_argument("input", help="輸入圖片")
    parser.add_argument("-o", "--output", default=None, help="輸出 PNG；預設放在輸入檔旁邊，檔名加 _ascii")
    parser.add_argument("--cols", type=int, default=90, help="每行幾個字，越大越細")
    parser.add_argument("--scale", type=int, default=4, help="輸出放大倍數；每格 = 6*scale x 12*scale 像素")
    parser.add_argument("--bg", choices=["auto", "dark", "light"], default="auto",
                        help="輸入圖的底色；淺底圖會先反相，讓圖形用密的字")
    parser.add_argument("--low", type=int, default=None, help="低於此亮度（0-255）視為背景；預設自動")
    parser.add_argument("--high", type=int, default=None, help="高於此亮度（0-255）視為最亮；預設自動")
    parser.add_argument("--crop", action="store_true", help="裁掉圖形四周的空白")
    parser.add_argument("--chars", default=None, help="只用這些字元（空白一定會加進去）；預設全部可見 ASCII")
    parser.add_argument("--txt", action="store_true", help="另外輸出同名 .txt")
    return parser.parse_args()


def main(opt):
    # 1. 輸出檔名與格式
    output = opt.output
    if output is None:
        output = os.path.splitext(opt.input)[0] + "_ascii.png"
    if os.path.splitext(output)[1].lower() != ".png":
        raise SystemExit("輸出只能是 .png（JPG 會讓文字邊緣出現雜點）：" + output)

    # 2. 讀圖，轉灰階
    gray = np.array(Image.open(opt.input).convert("L"), dtype=np.float32)

    # 3. 底色：中位數亮度高於 127 視為淺底；淺底反相，讓「圖形 = 亮」
    bg = opt.bg
    if bg == "auto":
        bg = "light" if np.median(gray) > 127 else "dark"
    if bg == "light":
        gray = 255 - gray

    # 4. 拉對比：背景壓到 0、最亮拉到 1
    #    low 預設 = 背景亮度（中位數）加 4 倍雜訊幅度，但不超過 high 的 1/4，避免照片的暗部被壓掉
    median = float(np.median(gray))
    mad = float(np.median(np.abs(gray - median)))
    high = float(opt.high) if opt.high is not None else float(np.percentile(gray, 99.5))
    low = float(opt.low) if opt.low is not None else min(median + 4 * mad, high / 4)
    if high <= low:
        raise SystemExit("high（%.0f）必須大於 low（%.0f）" % (high, low))
    ink = np.clip((gray - low) / (high - low), 0, 1)

    # 5. 裁邊：保留有圖形的範圍，四周留圖寬高的 2%
    if opt.crop:
        ys, xs = np.where(ink > 0.25)
        if len(ys) == 0:
            raise SystemExit("找不到圖形可裁；試著調低 --low")
        margin = int(round(0.02 * max(ink.shape)))
        ink = ink[max(ys.min() - margin, 0):ys.max() + margin + 1, max(xs.min() - margin, 0):xs.max() + margin + 1]

    # 6. 縮成「欄數 x 列數」格，每格 6x12 像素（取區域平均）
    cols = opt.cols
    rows = max(1, int(round(ink.shape[0] / ink.shape[1] * cols * CELL_W / CELL_H)))
    target = np.array(Image.fromarray(ink).resize((cols * CELL_W, rows * CELL_H), Image.BOX), dtype=np.float32)

    # 7. 每個字元畫在自己的格子裡（不靠整行排版，所以不會對不準），再縮成 6x12 供比對
    scale = opt.scale
    chars = sorted(set(opt.chars) | {" "}) if opt.chars else [chr(i) for i in range(32, 127)]
    font = ImageFont.truetype(FONT, size=10 * scale)
    big = np.zeros((len(chars), CELL_H * scale, CELL_W * scale), dtype=np.uint8)
    small = np.zeros((len(chars), CELL_H * CELL_W), dtype=np.float32)
    for i, c in enumerate(chars):
        canvas = Image.new("L", (CELL_W * scale, CELL_H * scale), 0)
        ImageDraw.Draw(canvas).text((0, 0), c, fill=255, font=font)
        big[i] = np.array(canvas)
        small[i] = np.array(canvas.resize((CELL_W, CELL_H), Image.BOX), dtype=np.float32).ravel() / 255

    # 8. 每一格選「跟原圖那一塊差最小」的字
    patches = target.reshape(rows, CELL_H, cols, CELL_W).transpose(0, 2, 1, 3).reshape(rows * cols, CELL_H * CELL_W)
    distance = (small ** 2).sum(1)[None, :] - 2 * patches @ small.T  # 省略每格都一樣的 patch**2
    picked = distance.argmin(1).reshape(rows, cols)

    # 9. 貼出高清圖，存 PNG（白字黑底）
    out = big[picked].transpose(0, 2, 1, 3).reshape(rows * CELL_H * scale, cols * CELL_W * scale)
    Image.fromarray(out).save(output)
    if opt.txt:
        text = "\n".join("".join(chars[k] for k in row).rstrip() for row in picked) + "\n"
        with open(os.path.splitext(output)[0] + ".txt", "w", encoding="utf-8") as f:
            f.write(text)

    print("底色 %s，low=%.0f high=%.0f，%d 欄 x %d 列，輸出 %s（%d x %d）"
          % (bg, low, high, cols, rows, output, out.shape[1], out.shape[0]))


if __name__ == "__main__":
    main(get_args())
