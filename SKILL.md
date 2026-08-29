---
name: vlog-caption-editor
description: Vlog captions with safe wrapping and chapter shorts.
version: 0.1.0
author: HaL-Fujita, Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [video, vlog, captions, ffmpeg, shorts, subtitles]
    related_skills: [ai-video-production-pipelines]
---

# Vlog caption editor

Use this skill when editing a talking-head Vlog or vertical short with large Japanese captions. It creates a 9:16 H.264/AAC/yuv420p export, trims long pauses, places captions above the speaker, emphasizes chapter headings, and leaves clean chapter splits for later Shorts.

## When to use

- A user provides a talking-head Vlog and a reference script.
- Captions should appear above the speaker, not at the bottom.
- Four or more chapters need emphasized title captions and matching SE hits.
- The final video may later be cut into chapter Shorts.
- Japanese captions use bold white/yellow text with thick black stroke.

Don't use for: complex multi-camera editorial work, heavy color grading, or manual CapCut finishing where deterministic ffmpeg output is not enough.

## Prerequisites

- `terminal` can run `ffmpeg` and `ffprobe`.
- `terminal` can run Python with Pillow installed.
- Recommended: install `budoux` for Japanese phrase line breaking. If unavailable, use the bundled bunsetsu-ish fallback plus kinsoku guards, then manually inspect line breaks.
- For ASR, use `whisper` if available, or any transcript source the user provides.
- On macOS, prefer Hiragino fonts such as `/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc`.

## Procedure

1. Inspect the source with `ffprobe`. Confirm duration, resolution, audio codec, and whether it is already 9:16.
2. Extract mono audio and run ASR. Save `transcript_raw.txt` and keep the user's script as the correction source.
3. Detect pauses with `silencedetect`. Cut only longer gaps, keeping about 0.18-0.25 seconds of natural pause so speech does not sound robotic.
4. Build an edit plan containing `cut_ranges`, `keep_intervals`, and chapter start times mapped from original time to edited time.
5. Render the base cut with ffmpeg concat filters. Preserve vertical framing; if the speaker is too small, scale slightly up and crop back to 1080x1920.
6. Add the same short SE on each chapter title start.
7. Generate caption overlays with Python/Pillow. Use phrase-aware wrapping, rendered pixel width, and kinsoku guards; do not split at arbitrary character counts.
8. Burn overlays onto the base cut and export H.264/AAC/yuv420p.
9. Create chapter Shorts using the mapped chapter timestamps.
10. Verify the final video with `ffprobe` and inspect representative frames around intro, each chapter title, and long captions.

## Caption rules

- Main captions: white, bold, thick black outline.
- Emphasis/title captions: yellow, bold, thicker black outline.
- Place captions above the speaker's head when possible.
- Never wrap Japanese captions by character count alone. Thick stroke and glyph width can overflow even when character count looks safe.
- Prefer BudouX phrase line breaking, then apply pixel-width wrapping. If BudouX is not installed, split on punctuation, particles, auxiliary verb endings, and JP/ASCII script transitions as a fallback.
- Apply kinsoku shori: punctuation, small kana, prolonged sound marks, and closing brackets must not start a line; opening brackets must not end a line.
- Avoid breaking immediately before particles/auxiliary endings when a nearby phrase boundary exists. Captions should read as short bunsetsu-like phrases.
- Avoid leaving setup words like「もっと」「その」「この」「そう」at the end of a line when the predicate starts the next line; move them forward to the next line.
- Use a pixel-width wrapper with a safe maximum width, usually 860-900 px for a 1080 px canvas. For thick outlined Japanese Vlog captions, start around 58 px white text and 70 px yellow emphasis text, then adjust visually.
- Verify overflow programmatically by measuring every rendered caption line's bounding box.
- Also spot-check exported frames visually. Programmatic width checks do not catch bad vertical placement or awkward overlap with the speaker.

## Quick reference

```bash
# Source inspection
ffprobe -v error -show_entries format=duration,size:stream=index,codec_type,codec_name,width,height,avg_frame_rate,channels,sample_rate -of json source.mp4

# Audio extraction for ASR / silence detection
ffmpeg -y -i source.mp4 -vn -ac 1 -ar 16000 audio.wav
ffmpeg -hide_banner -nostats -i audio.wav -af silencedetect=noise=-35dB:d=0.35 -f null - 2> silence.log

# Example final verification
ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt,color_range:format=duration,size -of json final.mp4
```

## Pitfalls

- ffmpeg builds without `ass` or `drawtext` cannot burn subtitles directly. Use Python/Pillow raw RGBA overlays and ffmpeg `overlay` instead.
- iPhone HEVC sources may be full-range `yuvj420p`; convert final output to `yuv420p` tv range for compatibility.
- Caption line breaks that look fine in text can overflow after adding thick black stroke.
- Morphologically awkward Japanese breaks are easy to miss in still-frame checks. Inspect the generated wrapped lines as text before rendering, especially around particles like「が/を/に/は/も」and endings like「です/ます/ない」.
- Updating a Drive deliverable should be verified by reading back `id`, `name`, `size`, `parents`, and `trashed`.
- Do not upload raw private video assets or transcripts to GitHub. Only commit reusable scripts and workflow docs.

## Verification checklist

- [ ] Final export is 1080x1920 or the requested vertical size.
- [ ] Final codec is H.264 with AAC audio.
- [ ] `pix_fmt` is `yuv420p`.
- [ ] Each chapter title has the same SE.
- [ ] Chapter timestamps are saved for later Shorts.
- [ ] Every rendered caption line fits within the safe pixel width.
- [ ] Representative frames show no left/right overflow.
- [ ] Captions sit above the speaker and do not cover the face unless unavoidable.
