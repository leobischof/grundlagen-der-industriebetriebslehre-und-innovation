"""One local workflow: name audio, render PDFs, cached transcription/alignment, build reader."""
from . import audio_sync, build_interactive, chapter_audio, render_pdf


def run(pages=None,dry_run: bool = False,force: bool = False) -> int:
    if not dry_run:
        chapter_audio.rename()
    for stage in (render_pdf,audio_sync,build_interactive):
        result = stage.run(pages=pages,dry_run=dry_run,force=force)
        if result:
            return result
    return 0
