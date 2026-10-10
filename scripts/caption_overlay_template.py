import math
import sys
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    import budoux  # type: ignore
except Exception:  # BudouX is optional; fallback keeps the template portable.
    budoux = None

W, H, FPS = 1080, 1920, 30
FONT_PATH = '/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc'
# Komachi's default accent: sakura pink (#FFB7C5). Keep normal captions white.
EMPHASIS_COLOR = (255, 183, 197, 255)
# Accept legacy events while rendering all emphasis in the selected accent.
EMPHASIS_STYLES = {'emphasis', 'pink', 'yellow'}

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

font_caption = ImageFont.truetype(FONT_PATH, 58)
font_caption_emphasis = ImageFont.truetype(FONT_PATH, 70)
font_title = ImageFont.truetype(FONT_PATH, 116)
font_label = ImageFont.truetype(FONT_PATH, 52)

PROHIBITED_LINE_START = set('、。，．・：；？！゛゜ヽヾゝゞ々ーぁぃぅぇぉっゃゅょァィゥェォッャュョ）〕］｝〉》」』】〙〗〟’”)]}>,.!?:;')
PROHIBITED_LINE_END = set('（〔［｛〈《「『【〘〖〝‘“([{<')
PARTICLE_BREAKERS = ('から','まで','より','ほど','だけ','こそ','でも','では','には','とは','って','なら','ので','のに','けど','が','を','に','へ','で','と','は','も','や','ね','よ')
VERB_END_BREAKERS = ('です','ます','でした','ました','ません','だった','だ','する','した','して','れる','られる','たい','ない','なる','ある','いる','できる')
BAD_LINE_END_PHRASES = ('もっと','その','この','あの','そう','どう','何も')

def _looks_ascii(ch):
    return ch.isascii() and (ch.isalnum() or ch in "'&@#%+")

def _script(ch):
    code = ord(ch)
    if _looks_ascii(ch): return 'ascii'
    if 0x3040 <= code <= 0x309F: return 'hiragana'
    if 0x30A0 <= code <= 0x30FF: return 'katakana'
    if 0x4E00 <= code <= 0x9FFF: return 'kanji'
    return 'other'

def phrase_units(text):
    """Return natural Japanese line-break units.

    Prefer BudouX when installed. It approximates Chrome's Japanese phrase line
    breaking. Fallback uses lightweight bunsetsu-ish rules: punctuation,
    particles/auxiliary endings, and script switches. Both paths are followed
    by kinsoku guards in `wrap_text_px`.
    """
    if budoux is not None:
        try:
            parser = budoux.load_default_japanese_parser()
            units = [u for u in parser.parse(text) if u]
            if units:
                return units
        except Exception:
            pass

    units = []
    start = 0
    prev_script = None
    for i, ch in enumerate(text):
        cur = text[start:i + 1]
        script = _script(ch)
        next_ch = text[i + 1] if i + 1 < len(text) else ''
        next_script = _script(next_ch) if next_ch else None
        should_break = False
        if ch in '。！？、・ ':
            should_break = True
        elif any(cur.endswith(p) for p in PARTICLE_BREAKERS + VERB_END_BREAKERS):
            should_break = True
        elif prev_script and next_script and script != next_script and 'ascii' in (script, next_script) and next_ch not in PROHIBITED_LINE_START:
            # Useful for JP/ASCII transitions, e.g. WSOPの / 2026年.
            should_break = True
        if should_break and next_ch and next_ch not in PROHIBITED_LINE_START and ch not in PROHIBITED_LINE_END:
            units.append(text[start:i + 1])
            start = i + 1
        prev_script = script
    if start < len(text):
        units.append(text[start:])
    return units

def _fix_kinsoku(lines):
    """Move prohibited line-start/end characters across boundaries."""
    lines = [line for line in lines if line]
    changed = True
    while changed:
        changed = False
        for i in range(1, len(lines)):
            while lines[i] and lines[i][0] in PROHIBITED_LINE_START:
                lines[i - 1] += lines[i][0]
                lines[i] = lines[i][1:]
                changed = True
            while lines[i - 1] and lines[i - 1][-1] in PROHIBITED_LINE_END:
                lines[i] = lines[i - 1][-1] + lines[i]
                lines[i - 1] = lines[i - 1][:-1]
                changed = True
            for phrase in BAD_LINE_END_PHRASES:
                if lines[i - 1].endswith(phrase) and len(lines[i - 1]) > len(phrase):
                    lines[i] = phrase + lines[i]
                    lines[i - 1] = lines[i - 1][:-len(phrase)]
                    changed = True
                    break
    return [line for line in lines if line]

def wrap_text_px(draw, text, font, max_width=900, stroke_width=10):
    """Wrap by phrase + rendered pixel width, including stroke.

    Character-count wrapping is unsafe for large Japanese captions with thick
    outlines. We first split at natural phrase boundaries, then measure pixels,
    then apply kinsoku guards so punctuation/small kana do not start a line.
    """
    units = phrase_units(text)

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
    fixed = _fix_kinsoku(fixed)
    final = []
    for line in fixed:
        bb = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        if bb[2] - bb[0] <= max_width:
            final.append(line)
            continue
        cur = ''
        for ch in line:
            test = cur + ch
            bb = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_width)
            if cur and (bb[2] - bb[0]) > max_width:
                moved = ''
                for phrase in BAD_LINE_END_PHRASES:
                    if cur.endswith(phrase) and len(cur) > len(phrase):
                        cur = cur[:-len(phrase)]
                        moved = phrase
                        break
                final.append(cur)
                cur = moved + ch
            else:
                cur = test
        if cur:
            final.append(cur)
    return _fix_kinsoku(final)

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
                draw_centered(draw, [title.title], font_title, 245, EMPHASIS_COLOR, stroke=12)
                draw_centered(draw, [title.label], font_label, 370, (255, 255, 255, 255), stroke=7)
            if caption:
                emphasized = caption.color in EMPHASIS_STYLES
                font = font_caption_emphasis if emphasized else font_caption
                fill = EMPHASIS_COLOR if emphasized else (255, 255, 255, 255)
                stroke = 10 if emphasized else 8
                max_width = 860 if emphasized else 900
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
        emphasized = event.color in EMPHASIS_STYLES
        font = font_caption_emphasis if emphasized else font_caption
        stroke = 10 if emphasized else 8
        max_width = 860 if emphasized else 900
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
