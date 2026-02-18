"""Tests for the screenshot (PPTX → PNG) module."""

import os
import pytest

from app.agents.screenshot import render_slides_to_images, cleanup_screenshots


class TestDependencies:
    """Regression: ensure all runtime dependencies are importable and declared in requirements.txt."""

    def test_fitz_importable(self):
        """pymupdf (fitz) must be importable — absence caused ModuleNotFoundError at startup."""
        import fitz  # noqa: F401

    def test_pymupdf_in_requirements(self):
        """pymupdf must be listed in requirements.txt so it is installed in every fresh venv."""
        req_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "requirements.txt"
        )
        with open(os.path.abspath(req_path)) as f:
            contents = f.read().lower()
        assert "pymupdf" in contents, "pymupdf is missing from requirements.txt"


class TestRenderSlidesToImages:

    def test_returns_one_png_per_slide(self, sample_pptx_path):
        """Short deck (6 slides) → exactly 6 PNG paths returned."""
        png_paths, temp_dir = render_slides_to_images(sample_pptx_path)
        try:
            assert len(png_paths) == 6
        finally:
            cleanup_screenshots(temp_dir)

    def test_all_files_exist(self, sample_pptx_path):
        """Every returned path points to a real, non-empty PNG file."""
        png_paths, temp_dir = render_slides_to_images(sample_pptx_path)
        try:
            for path in png_paths:
                assert os.path.isfile(path), f"Missing: {path}"
                assert os.path.getsize(path) > 0, f"Empty file: {path}"
        finally:
            cleanup_screenshots(temp_dir)

    def test_files_are_sorted_in_order(self, sample_pptx_path):
        """PNG paths are sorted so slide_000.png comes before slide_001.png."""
        png_paths, temp_dir = render_slides_to_images(sample_pptx_path)
        try:
            basenames = [os.path.basename(p) for p in png_paths]
            assert basenames == sorted(basenames)
        finally:
            cleanup_screenshots(temp_dir)

    def test_cleanup_removes_temp_dir(self, sample_pptx_path):
        """cleanup_screenshots removes the temp directory."""
        _, temp_dir = render_slides_to_images(sample_pptx_path)
        assert os.path.isdir(temp_dir)
        cleanup_screenshots(temp_dir)
        assert not os.path.exists(temp_dir)

    def test_invalid_path_raises_runtime_error(self):
        """Non-existent PPTX raises RuntimeError (LibreOffice fails)."""
        with pytest.raises(RuntimeError):
            render_slides_to_images("/tmp/does_not_exist_xyz.pptx")
