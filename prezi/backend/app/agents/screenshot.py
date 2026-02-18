"""Render PPTX slides to PNG images via LibreOffice + pymupdf."""

import glob
import os
import shutil
import subprocess
import tempfile
from typing import List

import fitz  # pymupdf


def render_slides_to_images(pptx_path: str, dpi_scale: float = 1.5) -> tuple:
    """
    Convert every slide in a PPTX file to a PNG image.

    Returns (png_paths, temp_dir).  The caller is responsible for calling
    cleanup_screenshots(temp_dir) when done with the images.

    Args:
        pptx_path:  Absolute or relative path to the .pptx file.
        dpi_scale:  Zoom factor for pymupdf rendering (1.0 ≈ 96 dpi,
                    1.5 ≈ 144 dpi).  Default 1.5 gives ~1080×810 px per slide.

    Returns:
        (List[str], str) — (sorted PNG paths, temp directory path)

    Raises:
        RuntimeError if LibreOffice or pymupdf conversion fails.
    """
    outdir = tempfile.mkdtemp(prefix="prezi_shots_")
    abs_pptx = os.path.abspath(pptx_path)

    # Step 1: PPTX → PDF using LibreOffice headless
    result = subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, abs_pptx],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        shutil.rmtree(outdir, ignore_errors=True)
        raise RuntimeError(
            f"LibreOffice PDF conversion failed (rc={result.returncode}): "
            f"{result.stderr[:400]}"
        )

    pdf_files = glob.glob(os.path.join(outdir, "*.pdf"))
    if not pdf_files:
        shutil.rmtree(outdir, ignore_errors=True)
        raise RuntimeError("LibreOffice produced no PDF output.")

    pdf_path = pdf_files[0]

    # Step 2: PDF → per-slide PNGs using pymupdf
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(dpi_scale, dpi_scale)
    png_paths: List[str] = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        png_path = os.path.join(outdir, f"slide_{i:03d}.png")
        pix.save(png_path)
        png_paths.append(png_path)
    doc.close()

    return png_paths, outdir


def cleanup_screenshots(temp_dir: str) -> None:
    """Remove the temporary directory created by render_slides_to_images."""
    shutil.rmtree(temp_dir, ignore_errors=True)
