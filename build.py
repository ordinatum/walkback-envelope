#!/usr/bin/env python3
"""Собирает самодостаточный dist/walkback.html: inline-ит physics.mjs внутрь.

Челлендж требует один файл без сборки, поэтому dist/walkback.html — это
то, что отдаётся жюри. physics.mjs остаётся отдельным для разработки и тестов.

Подстановка делается str.replace, НЕ re.sub: содержимое physics.mjs идёт
как replacement-шаблон, и любой бэкслеш в нём regex переинтерпретировал бы.
"""
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parent
src = (root / "index.html").read_text(encoding="utf-8")
phys = (root / "physics.mjs").read_text(encoding="utf-8")

# убираем export-ы — всё живёт в одной области видимости
phys_inline = re.sub(r"^export\s+", "", phys, flags=re.M)

# находим строку импорта целиком, какой бы перенос строк в ней ни был
m = re.search(r"import\s*\{[^}]*\}\s*\n?\s*from\s*'\./physics\.mjs';", src)
if not m:
    sys.exit("ОШИБКА: в index.html не найден импорт ./physics.mjs")

replacement = "/* ── physics.mjs (inline) ── */\n" + phys_inline + "\n/* ── /physics.mjs ── */"
out = src.replace(m.group(0), replacement)

if out == src:
    sys.exit("ОШИБКА: подстановка не сработала")
if "from './physics.mjs'" in out:
    sys.exit("ОШИБКА: в собранном файле остался импорт physics.mjs")
if re.search(r"^export\s", out, flags=re.M):
    sys.exit("ОШИБКА: в собранном файле остался export")

dist = root / "dist"
dist.mkdir(exist_ok=True)
target = dist / "walkback.html"
target.write_text(out, encoding="utf-8")
print(f"dist/walkback.html  {len(out)} chars  (physics {len(phys_inline)})")
