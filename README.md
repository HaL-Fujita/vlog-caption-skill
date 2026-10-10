# Vlog caption skill

Hermes skill for editing vertical talking-head Vlogs with large Japanese captions, chapter emphasis, pause trimming, SE hits, and Shorts-ready chapter splits.

小町の TikTok 動画編集用スキル・作業メモとしてカスタマイズしています。通常字幕は白、強調・章タイトルは桜色ピンク (`#FFB7C5`)。指定 BGM は声を優先した控えめな音量で使います。詳しい編集方針は [SKILL.md](SKILL.md)、ゆずひめの2本で使った設定・環境・受け渡しの記録は [小町の編集メモ](docs/komachi-editing-notes.md) を参照してください。

## Files

- `SKILL.md` — reusable Hermes skill instructions.
- `docs/komachi-editing-notes.md` — 小町・ゆずひめの試作設定、再開手順、スマホへの納品で確認したこと。
- `scripts/caption_overlay_template.py` — Pillow overlay template using BudouX-style phrase wrapping, kinsoku guards, and pixel-width checks to avoid awkward line breaks and caption overflow.
- `requirements.txt` — Pillow + optional BudouX dependency list.

## Install locally

Copy this directory into a Hermes skills directory, for example:

```bash
mkdir -p ~/.hermes/skills/media/vlog-caption-editor
cp SKILL.md ~/.hermes/skills/media/vlog-caption-editor/SKILL.md
cp -R scripts ~/.hermes/skills/media/vlog-caption-editor/
cp -R docs ~/.hermes/skills/media/vlog-caption-editor/
```

Start a new Hermes session before expecting the skill loader to see it.

## Privacy

Do not commit source videos, transcripts, screenshots, rendered exports, Drive URLs, temporary download URLs, OAuth tokens, or client-specific assets. Keep per-video files and delivery manifests outside this repository; record reusable settings and workflow notes here.
