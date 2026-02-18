"""Tests for the ImageGenerator module."""

import io
import pytest

from app.agents.image_gen import ImageGenerator


class TestImageGeneratorNoKey:
    """ImageGenerator behaves gracefully when no API key is supplied."""

    def test_available_is_false_without_key(self):
        gen = ImageGenerator(openai_api_key=None)
        assert gen.available is False

    async def test_generate_returns_none_without_key(self):
        gen = ImageGenerator(openai_api_key=None)
        result = await gen.generate_image("A professional consulting slide illustration")
        assert result is None

    async def test_generate_returns_none_for_empty_key(self):
        gen = ImageGenerator(openai_api_key="")
        result = await gen.generate_image("Test prompt")
        assert result is None

    async def test_multiple_calls_all_return_none(self):
        gen = ImageGenerator(openai_api_key=None)
        for _ in range(3):
            result = await gen.generate_image("Any prompt")
            assert result is None


class TestImageGeneratorWithMockedClient:
    """ImageGenerator with a mocked OpenAI client."""

    async def test_generate_returns_bytesio_on_success(self, monkeypatch):
        """When the DALL-E call and HTTP download succeed, returns a BytesIO."""
        import types

        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        class FakeHTTPResponse:
            content = fake_png
            def raise_for_status(self): pass

        class FakeHTTPClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *_): pass
            async def get(self, url): return FakeHTTPResponse()

        class FakeImageData:
            url = "https://fake.cdn/image.png"

        class FakeImagesResponse:
            data = [FakeImageData()]

        class FakeImages:
            async def generate(self, **kwargs):
                return FakeImagesResponse()

        class FakeOpenAI:
            images = FakeImages()

        gen = ImageGenerator.__new__(ImageGenerator)
        gen._client = FakeOpenAI()
        gen._cache = {}
        gen._STYLE_SUFFIX = ImageGenerator._STYLE_SUFFIX

        monkeypatch.setattr("app.agents.image_gen.httpx", types.SimpleNamespace(
            AsyncClient=lambda timeout=None: FakeHTTPClient()
        ))

        result = await gen.generate_image("Cloud computing strategy")
        assert isinstance(result, io.BytesIO)
        result.seek(0)
        assert result.read() == fake_png

    async def test_generate_caches_result(self, monkeypatch):
        """Second call with identical prompt hits cache, no second HTTP call."""
        import types

        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        call_count = 0

        class FakeHTTPResponse:
            content = fake_png
            def raise_for_status(self): pass

        class FakeHTTPClient:
            async def __aenter__(self): return self
            async def __aexit__(self, *_): pass
            async def get(self, url):
                nonlocal call_count
                call_count += 1
                return FakeHTTPResponse()

        class FakeImageData:
            url = "https://fake.cdn/image.png"

        class FakeImagesResponse:
            data = [FakeImageData()]

        class FakeImages:
            async def generate(self, **kwargs):
                return FakeImagesResponse()

        class FakeOpenAI:
            images = FakeImages()

        gen = ImageGenerator.__new__(ImageGenerator)
        gen._client = FakeOpenAI()
        gen._cache = {}
        gen._STYLE_SUFFIX = ImageGenerator._STYLE_SUFFIX

        monkeypatch.setattr("app.agents.image_gen.httpx", types.SimpleNamespace(
            AsyncClient=lambda timeout=None: FakeHTTPClient()
        ))

        await gen.generate_image("same prompt")
        await gen.generate_image("same prompt")
        # Only one HTTP download despite two calls
        assert call_count == 1

    async def test_generate_returns_none_on_api_error(self):
        """If the DALL-E call raises, returns None gracefully."""
        class BrokenImages:
            async def generate(self, **kwargs):
                raise RuntimeError("API quota exceeded")

        class BrokenOpenAI:
            images = BrokenImages()

        gen = ImageGenerator.__new__(ImageGenerator)
        gen._client = BrokenOpenAI()
        gen._cache = {}
        gen._STYLE_SUFFIX = ImageGenerator._STYLE_SUFFIX

        result = await gen.generate_image("test")
        assert result is None
