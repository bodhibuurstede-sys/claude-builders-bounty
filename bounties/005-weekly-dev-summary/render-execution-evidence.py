#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

log_path = Path("n8n-execution.log")
text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else "execution log unavailable"
lines = ["n8n real-instance smoke test"] + text.splitlines()[-35:]

font = ImageFont.load_default()
wrapped = []
for line in lines:
    wrapped.extend(textwrap.wrap(line, width=110, replace_whitespace=False) or [""])
line_h = 16
width = 1000
height = 36 + line_h * len(wrapped)
img = Image.new("RGB", (width, max(height, 260)), "white")
draw = ImageDraw.Draw(img)
y = 18
for line in wrapped:
    draw.text((18, y), line, fill="black", font=font)
    y += line_h
img.save("execution-evidence.png")
print("wrote execution-evidence.png")
