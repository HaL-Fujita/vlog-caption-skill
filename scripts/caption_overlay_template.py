import math
import sys
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FONT_PATH = '/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc'

@dataclass(frozen=True)
class CaptionEvent:
    start: float
    end: float
    text: str
    color: str = 'white'

@dataclass(frozen=True)
class TitleEvent:
    start: float
    end: float
    title: str
    label: str = '4つの大切な条件'

# Replace these with mapped timestamps from edit_plan.json.
CAPTIONS = [
    CaptionEvent(0.0, 3.0, 'ここに話している内容のテロップを入れる'),
]
TITLES = [
    TitleEvent(0.0, 2.1, '向上心'),
]

font_caption = ImageFont.truetype(FONT_PATH, 64)
font_caption_yellow = ImageFont.truetype(FONT_PATH, 76)
font_title = ImageFont.truetype(FONT_PATH, 116)
font_label = ImageFont.truetype(FONT_PATH, 52)

def wrap_text_px(draw, text, font, max_width=900, stroke_width=10):
    """Wrap by rendered pixel width, including stroke.

    Character-count wrapping is unsafe for large Japanese captions with thick
    outlines. Always measure the rendered line before accepting it.
    """
    units = []
    buf = ''
    for ch in text:
        buf += ch
        if ch in '。、！？・ ':
            units.append(buf)
            buf = ''
    if buf:
        units.append(buf)

    lines = []
    cur = ''
    for unit in units:
        test = cur + unit
        bb = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_width)
        if cur and (bb[2] - bb[0]) > max_width:
            lines.append(cur)
            cur = unit
        else:
            cur = test
    if cur:
        lines.append(cur)

    fixed = []
    for line in lines:
        cur = ''
        for ch in line:
            test = cur + ch
            bb = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_width)
            if cur and (bb[2] - bb[0]) > max_width:
                fixed.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            fixed.append(cur)
    return fixed

def draw_centered(draw, lines, font, y, fill, stroke=8, spacing=8):
    bbs = [draw.textbbox((0, 0), line, font=font, stroke_width=stroke) for line in lines]
    heights = [bb[3] - bb[1] for bb in bbs]
    widths = [bb[2] - bb[0] for bb in bbs]
    top = y - (sum(heights) + spacing * (len(lines) - 1)) / 2
    for line, width, height in zip(lines, widths, heights):
        draw.text(((W - width) / 2, top), line, font=font, fill=fill,
                  stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        top += height + spacing

def active(events, t):
    for event in events:
        if event.start <= t < event.end:
            return event
    return None

def render_overlay(duration, out):
    nframes = math.ceil(duration * FPS)
    last_key = None
    last_bytes = None
    for i in range(nframes):
        t = i / FPS
        caption = active(CAPTIONS, t)
        title = active(TITLES, t)
        key = (caption, title)
        if key != last_key:
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            if title:
                draw_centered(draw, [title.title], font_title, 245, (255, 232, 0, 255), stroke=12)
                draw_centered(draw, [title.label], font_label, 370, (255, 255, 255, 255), stroke=7)
            if caption:
                font = font_caption_yellow if caption.color == 'yellow' else font_caption
                fill = (255, 232, 0, 255) if caption.color == 'yellow' else (255, 255, 255, 255)
                stroke = 10 if caption.color == 'yellow' else 8
                max_width = 860 if caption.color == 'yellow' else 900
                lines = wrap_text_px(draw, caption.text, font, max_width=max_width, stroke_width=stroke)
                draw_centered(draw, lines, font, 585 if title else 430, fill, stroke=stroke, spacing=10)
            last_bytes = img.tobytes()
            last_key = key
        if last_bytes is None:
            last_bytes = Image.new('RGBA', (W, H), (0, 0, 0, 0)).tobytes()
        out.write(last_bytes)
    out.flush()

def verify_no_overflow():
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    problems = []
    for event in CAPTIONS:
        font = font_caption_yellow if event.color == 'yellow' else font_caption
        stroke = 10 if event.color == 'yellow' else 8
        max_width = 860 if event.color == 'yellow' else 900
        for line in wrap_text_px(draw, event.text, font, max_width=max_width, stroke_width=stroke):
            bb = draw.textbbox((0, 0), line, font=font, stroke_width=stroke)
            if bb[2] - bb[0] > 980:
                problems.append((event.start, bb[2] - bb[0], line))
    return problems

if __name__ == '__main__':
    if '--verify' in sys.argv:
        problems = verify_no_overflow()
        print(f'overflow_problems {len(problems)}')
        for problem in problems:
            print(problem)
    else:
        duration = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
        render_overlay(duration, sys.stdout.buffer)
