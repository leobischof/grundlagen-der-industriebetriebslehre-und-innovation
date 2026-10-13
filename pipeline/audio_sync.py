"""Local ASR + lexical PDF alignment. Suggestions, never claimed to be verified.

python -m pipeline.audio_sync --model tiny
Downloads an ASR model once; audio and transcripts stay local. Cached by audio hash/model.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

from . import chapter_audio, config, content_files
from .audio_topics import add_topic_context, annotation_digest, pdf_sections, untouched_generated

STOP = set("aber alle als also am an auch auf aus bei bis das dass dem den der des die doch ein eine einem einen einer eines er es fuer für hat hier ich im in ist ja kann man mit nach nicht noch nur oder schon sehr sich sie sind so um und uns vom von vor war was wenn werden wie wir wird wo zu zum zur über".split())


def words(text: str) -> Counter:
    return Counter(w for w in re.findall(r"[a-zäöüß]{3,}", text.lower()) if w not in STOP)


def align(segments: list[dict], blocks: list[dict], threshold: float = config.AUDIO_MATCH_THRESHOLD) -> list[dict]:
    """Independent windows: allows audio to change topic out of PDF order. Low scores omitted."""
    counts = [words(b["text"]) for b in blocks]
    df = Counter(w for c in counts for w in c)
    idf = {w: math.log((len(blocks) + 1) / (f + 1)) + 1 for w, f in df.items()}

    def vector(text_counts):
        raw = {w: (1 + math.log(c)) * idf[w] for w, c in text_counts.items() if w in idf}
        norm = math.sqrt(sum(v*v for v in raw.values())) or 1
        return {w: v / norm for w, v in raw.items()}

    vectors = [vector(c) for c in counts]
    windows = []
    for seg in segments:
        if not windows or seg["start"] - windows[-1]["start"] >= 18:
            windows.append(dict(start=seg["start"], end=seg["end"], text=seg["text"]))
        else:
            windows[-1]["end"] = seg["end"]
            windows[-1]["text"] += " " + seg["text"]
    annotations = []
    for window in windows:
        query = words(window["text"])
        v = vector(query)
        candidates = [(sum(v.get(w, 0)*value for w, value in bv.items()), i)
                      for i, bv in enumerate(vectors) if len(query.keys() & counts[i].keys()) >= 3]
        if not candidates:
            continue
        score, i = max(candidates)
        if score < threshold:
            continue
        b = blocks[i]
        # A caption alone is too small to explain a figure: use its curated/rendered bounds when available.
        annotations.append(dict(id=f"auto-{len(annotations)+1}", start=round(window["start"], 3),
                                end=round(window["end"], 3), page=b["page"], type="rect",
                                rect=b["rect"], pointer=True, label=b["text"][:110].strip(),
                                transcript=window["text"].strip(), target_text=b["text"][:500],
                                confidence=round(score, 3), status="unreviewed", origin="local-asr-lexical"))
    return annotations


def pdf_blocks(path: Path) -> list[dict]:
    import pymupdf
    result = []
    with pymupdf.open(path) as doc:
        for n, page in enumerate(doc, 1):
            width, height = page.rect.width, page.rect.height
            text_blocks = page.get_text("blocks")
            images = [r for image in page.get_images(full=True) for r in page.get_image_rects(image[0])]
            for x0, y0, x1, y1, text, _, kind in text_blocks:
                if kind != 0 or len(words(text)) < 4 or y0 < height*.06 or y0 > height*.92:
                    continue
                if re.search(r"Abbildung\s+\d+", text):
                    above = [r for r in images if 0 <= y0-r.y1 < height*.1]
                    if above:
                        r = max(above, key=lambda r: r.y1)
                        x0, y0, x1, y1 = min(x0,r.x0), min(y0,r.y0), max(x1,r.x1), max(y1,r.y1)
                result.append(dict(page=n, text=text, rect=[max(0,x0/width), max(0,y0/height),
                                                           min(1,(x1-x0)/width), min(1,(y1-y0)/height)]))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=config.ASR_MODEL, help="Whisper-Modell, z. B. tiny, base, small")
    parser.add_argument("--refresh-unreviewed",action="store_true",help="Nur nachweislich unveränderte automatische Timelines aktualisieren")
    parser.add_argument("--chapters", nargs="*", type=int, help="nur diese Kapitel")
    args = parser.parse_args(argv)
    recordings = chapter_audio.rename()
    chapters = {content_files.chapter_number(c.slug): c for c in content_files.discover(config.CONTENT)}
    config.TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    config.INTERACTIVE_CURATION.mkdir(parents=True, exist_ok=True)
    model = None
    for n, audio in recordings.items():
        if args.chapters and n not in args.chapters:
            continue
        chapter = chapters[n]
        pdf = config.BUILD / "pdf" / f"{chapter.export.stem}.pdf"
        if not pdf.exists():
            raise FileNotFoundError(f"{pdf.name} fehlt; zuerst python -m pipeline render-pdf")
        audio_hash, pdf_hash = chapter_audio.digest(audio), chapter_audio.digest(pdf)
        cache = config.TRANSCRIPTS / f"GIL-{n}-Transkript.json"
        data = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
        transcribed = data.get("audio_sha256") != audio_hash or data.get("model") != args.model
        if transcribed:
            if model is None:
                from faster_whisper import WhisperModel
                print(f"[sync] Lade lokales Whisper-Modell {args.model} (CPU/int8)", flush=True)
                model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=4)
            print(f"[sync] Kapitel {n}: transkribiere {audio.name}", flush=True)
            stream, info = model.transcribe(str(audio), language="de", beam_size=1, vad_filter=True,
                                            condition_on_previous_text=False)
            segments = []
            reported = -120
            for s in stream:
                segments.append(dict(start=s.start, end=s.end, text=s.text))
                if s.end - reported > 120:
                    print(f"[sync] Kapitel {n}: {s.end:.0f}/{info.duration:.0f} Sekunden", flush=True)
                    reported = s.end
            data = dict(audio_sha256=audio_hash, model=args.model, duration=info.duration, segments=segments)
            cache.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        annotations = add_topic_context(align(data["segments"],pdf_blocks(pdf)),pdf_sections(pdf),data["duration"])
        timeline = dict(version=1, chapter=n, audio_sha256=audio_hash, pdf_sha256=pdf_hash,
                        generator=f"faster-whisper/{args.model} + persistent topics + lexical matching", annotations=annotations,
                        generated_annotations_sha256=annotation_digest(annotations))
        out = config.INTERACTIVE_CURATION / f"GIL-{n}-Timeline.json"
        # Never overwrite the user's reviewed timeline. New candidates get a separate local file.
        if out.exists():
            previous = json.loads(out.read_text(encoding="utf-8"))
            if not args.refresh_unreviewed or not untouched_generated(previous):
                out = config.TRANSCRIPTS / f"GIL-{n}-Timeline-Vorschlag.json"
        out.write_text(json.dumps(timeline, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        if transcribed:
            from .ailog import append
            append(dict(stage="audio-alignment",model=f"faster-whisper/{args.model} (local CPU/int8)",
                        purpose=f"Lokale Transkription und PDF-Zuordnung Kapitel {n}",inputs=[str(audio),str(pdf)],
                        est_input_tokens=0,est_output_tokens=0,
                        result=f"{len(annotations)} ungeprüfte Vorschläge; ASR ohne Texttoken-Schätzung"))
        print(f"[sync] Kapitel {n}: {len(annotations)} ungeprüfte Vorschläge -> {out}", flush=True)
    return 0


def run(pages=None,dry_run: bool = False,force: bool = False) -> int:
    if dry_run:
        print("[sync-audio] würde Audios lokal transkribieren und unveränderte automatische Timelines aktualisieren")
        return 0
    return main(["--model",config.ASR_MODEL,"--refresh-unreviewed"])


if __name__ == "__main__":
    raise SystemExit(main())
