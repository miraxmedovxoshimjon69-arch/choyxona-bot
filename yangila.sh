#!/bin/sh
# Menyu, narx va rasmlarni GitHub'ga yuklaydi (Mini App shu yerdan ochiladi).
cd "$(dirname "$0")" || exit 1
git add -A
git commit -m "Menyu yangilandi" || echo "(yangi o'zgarish yo'q)"
git push
