import importlib.util
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('caption_overlay_template', ROOT / 'scripts' / 'caption_overlay_template.py')
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_japanese_wrap_respects_width_and_kinsoku():
    image = Image.new('RGBA', (mod.W, mod.H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    text = '僕自身もずっとそうやって生きてきました。吃音があり、人前で話すのが苦手でした。'
    lines = mod.wrap_text_px(draw, text, mod.font_caption, max_width=650, stroke_width=8)
    assert len(lines) >= 2
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=mod.font_caption, stroke_width=8)
        assert bb[2] - bb[0] <= 980
        assert line[0] not in mod.PROHIBITED_LINE_START
        assert line[-1] not in mod.PROHIBITED_LINE_END

def test_phrase_units_prefers_particles_and_endings():
    units = mod.phrase_units('もっと強くなりたい。もっと知りたい。昨日の自分より成長したい。')
    joined = '|'.join(units)
    assert 'たい。' in joined
    assert ''.join(units) == 'もっと強くなりたい。もっと知りたい。昨日の自分より成長したい。'

def test_ascii_transition_is_break_opportunity():
    units = mod.phrase_units('WSOPのブレスレットを目指してほしい。')
    assert ''.join(units) == 'WSOPのブレスレットを目指してほしい。'
    assert any('WSOP' in unit for unit in units)
