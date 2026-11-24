# Ascii 的映像檔；只屬於 Ascii 的打包檔，建映像檔的程式在 package/Image
# 建置內容的位置（SOURCE）由 package/Image/Build.bat 從 product.json 的 source 帶進來
FROM python:3.11-slim
ARG SOURCE
WORKDIR /app
RUN pip install --no-cache-dir pillow numpy
COPY ${SOURCE} /app
ENTRYPOINT ["python", "ascii_art.py"]
