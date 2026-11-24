# Ascii

把圖片轉成高清 ASCII 圖（PNG，白字黑底），給想要線條和轉角都對得準的人用。

## 第一次：建映像檔

在專案根目錄（`D:\Private_project\Ascii`）執行：

```powershell
package\Image\Build.bat Ascii
```

要先開著 Docker Desktop。只有第一次，或改了 `src\Ascii` 的程式之後才要再建。

## 每次：轉一張圖

把圖放進 `data\`，在專案根目錄執行（輸出會出現在同一個資料夾）：

```powershell
docker run --rm -v "${PWD}\data:/data" ascii /data/input.png -o /data/output.png --cols 90 --crop
```

要比較像線條畫的樣子，只用線條類字元：

```powershell
docker run --rm -v "${PWD}\data:/data" ascii /data/input.png -o /data/output.png --cols 90 --crop --chars "/\|_-()[]{}<>^'.,:;!"
```

## 參數

| 參數 | 意思 | 預設 |
|---|---|---|
| 第一個 | 輸入圖片，路徑要寫 `/data/檔名` | 必填 |
| `-o` | 輸出 PNG，只能是 `.png` | 輸入檔名加 `_ascii.png` |
| `--cols` | 每行幾個字，越大越細，檔案也越大 | 90 |
| `--scale` | 輸出放大倍數，越大越高清 | 4 |
| `--crop` | 裁掉圖形四周的空白 | 不裁 |
| `--chars` | 只用這些字元 | 全部可見 ASCII |
| `--bg` | 輸入圖底色 `dark` 或 `light` | 自動判斷 |
| `--low`、`--high` | 背景與最亮的亮度（0–255），背景有雜點時調高 `--low` | 自動 |
| `--txt` | 另外輸出同名 `.txt` | 不輸出 |

## 注意

- 深底亮線的圖和淺底暗圖形的圖都直接丟，自動判斷底色；判斷錯了用 `--bg` 指定。
- 照片這類沒有單純背景的圖，把 `--low` 設成 0。
- 輸出只存 PNG：JPG 會讓文字邊緣出現雜點。
