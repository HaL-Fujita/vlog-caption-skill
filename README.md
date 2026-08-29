# Vlog caption skill

Hermes skill for editing vertical talking-head Vlogs with large Japanese captions, chapter emphasis, pause trimming, SE hits, and Shorts-ready chapter splits.

## Files

- `SKILL.md` — reusable Hermes skill instructions.
- `scripts/caption_overlay_template.py` — Pillow overlay template using pixel-width wrapping to avoid caption overflow.

## Install locally

Copy this directory into a Hermes skills directory, for example:

```bash
mkdir -p ~/.hermes/skills/media/vlog-caption-editor
cp SKILL.md ~/.hermes/skills/media/vlog-caption-editor/SKILL.md
cp -R scripts ~/.hermes/skills/media/vlog-caption-editor/
```

Start a new Hermes session before expecting the skill loader to see it.

## Privacy

Do not commit source videos, transcripts, screenshots, rendered exports, Drive URLs, OAuth tokens, or client-specific assets.
