"""Tests for Claude, OpenAI, and Gemini LLM providers (mock-based)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# ClaudeProvider
# ---------------------------------------------------------------------------

class TestClaudeProvider:

    def test_raises_without_key(self):
        with patch("app.providers.llm.claude.settings") as ms:
            ms.ANTHROPIC_API_KEY = None
            from app.providers.llm.claude import ClaudeProvider
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                ClaudeProvider()

    async def test_generate_returns_text(self):
        with patch("app.providers.llm.claude.settings") as ms:
            ms.ANTHROPIC_API_KEY = "test-key"
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content[0].text = "Generated response"
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            with patch("app.providers.llm.claude.AsyncAnthropic", return_value=mock_client):
                from app.providers.llm.claude import ClaudeProvider
                provider = ClaudeProvider()
                result = await provider.generate("hello")

        assert result == "Generated response"

    async def test_generate_passes_system_prompt(self):
        with patch("app.providers.llm.claude.settings") as ms:
            ms.ANTHROPIC_API_KEY = "test-key"
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content[0].text = "ok"
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            with patch("app.providers.llm.claude.AsyncAnthropic", return_value=mock_client):
                from app.providers.llm.claude import ClaudeProvider
                provider = ClaudeProvider()
                await provider.generate("prompt", system="You are an expert.")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "You are an expert."

    async def test_generate_respects_max_tokens(self):
        with patch("app.providers.llm.claude.settings") as ms:
            ms.ANTHROPIC_API_KEY = "test-key"
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content[0].text = "ok"
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            with patch("app.providers.llm.claude.AsyncAnthropic", return_value=mock_client):
                from app.providers.llm.claude import ClaudeProvider
                provider = ClaudeProvider()
                await provider.generate("prompt", max_tokens=8000)

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["max_tokens"] == 8000

    async def test_generate_with_vision_skips_missing_files(self, tmp_path):
        """generate_with_vision skips image paths that don't exist."""
        with patch("app.providers.llm.claude.settings") as ms:
            ms.ANTHROPIC_API_KEY = "test-key"
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content[0].text = "vision result"
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            with patch("app.providers.llm.claude.AsyncAnthropic", return_value=mock_client):
                from app.providers.llm.claude import ClaudeProvider
                provider = ClaudeProvider()
                result = await provider.generate_with_vision(
                    "describe this", ["/nonexistent/path.png"]
                )

        assert result == "vision result"
        # Content should only have the text block (image skipped)
        content_sent = mock_client.messages.create.call_args[1]["messages"][0]["content"]
        assert len(content_sent) == 1
        assert content_sent[0]["type"] == "text"

    def test_supports_vision(self):
        with patch("app.providers.llm.claude.settings") as ms:
            ms.ANTHROPIC_API_KEY = "test-key"
            with patch("app.providers.llm.claude.AsyncAnthropic"):
                from app.providers.llm.claude import ClaudeProvider
                provider = ClaudeProvider()
        assert provider.supports_vision() is True

    def test_get_model_name(self):
        with patch("app.providers.llm.claude.settings") as ms:
            ms.ANTHROPIC_API_KEY = "test-key"
            with patch("app.providers.llm.claude.AsyncAnthropic"):
                from app.providers.llm.claude import ClaudeProvider
                provider = ClaudeProvider()
        assert "Claude" in provider.get_model_name()


# ---------------------------------------------------------------------------
# OpenAIProvider
# ---------------------------------------------------------------------------

class TestOpenAIProvider:

    def test_raises_without_key(self):
        with patch("app.providers.llm.openai.settings") as ms:
            ms.OPENAI_API_KEY = None
            from app.providers.llm.openai import OpenAIProvider
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                OpenAIProvider()

    async def test_generate_returns_text(self):
        with patch("app.providers.llm.openai.settings") as ms:
            ms.OPENAI_API_KEY = "test-key"
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "OpenAI response"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            with patch("app.providers.llm.openai.AsyncOpenAI", return_value=mock_client):
                from app.providers.llm.openai import OpenAIProvider
                provider = OpenAIProvider()
                result = await provider.generate("hello")

        assert result == "OpenAI response"

    async def test_generate_includes_system_message(self):
        with patch("app.providers.llm.openai.settings") as ms:
            ms.OPENAI_API_KEY = "test-key"
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "ok"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            with patch("app.providers.llm.openai.AsyncOpenAI", return_value=mock_client):
                from app.providers.llm.openai import OpenAIProvider
                provider = OpenAIProvider()
                await provider.generate("user prompt", system="system text")

        messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert messages[0] == {"role": "system", "content": "system text"}
        assert messages[1]["role"] == "user"

    async def test_generate_without_system(self):
        with patch("app.providers.llm.openai.settings") as ms:
            ms.OPENAI_API_KEY = "test-key"
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "ok"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            with patch("app.providers.llm.openai.AsyncOpenAI", return_value=mock_client):
                from app.providers.llm.openai import OpenAIProvider
                provider = OpenAIProvider()
                await provider.generate("user prompt")

        messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_get_model_name(self):
        with patch("app.providers.llm.openai.settings") as ms:
            ms.OPENAI_API_KEY = "test-key"
            with patch("app.providers.llm.openai.AsyncOpenAI"):
                from app.providers.llm.openai import OpenAIProvider
                provider = OpenAIProvider()
        assert "OpenAI" in provider.get_model_name()

    def test_supports_vision(self):
        with patch("app.providers.llm.openai.settings") as ms:
            ms.OPENAI_API_KEY = "test-key"
            with patch("app.providers.llm.openai.AsyncOpenAI"):
                from app.providers.llm.openai import OpenAIProvider
                provider = OpenAIProvider()
        assert provider.supports_vision() is True


# ---------------------------------------------------------------------------
# GeminiProvider
# ---------------------------------------------------------------------------

class TestGeminiProvider:

    def test_raises_without_key(self):
        with patch("app.providers.llm.gemini.settings") as ms:
            ms.GOOGLE_API_KEY = None
            from app.providers.llm.gemini import GeminiProvider
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                GeminiProvider()

    async def test_generate_returns_text(self):
        """GeminiProvider.generate() calls the underlying model and returns text."""
        mock_genai = MagicMock()
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.GenerationConfig.return_value = MagicMock()

        with patch("app.providers.llm.gemini.settings") as ms:
            ms.GOOGLE_API_KEY = "test-key"
            with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
                from importlib import reload
                import app.providers.llm.gemini as gemini_mod
                # Patch the internal genai reference directly on the module
                original_genai = gemini_mod.GeminiProvider.__init__
                def patched_init(self, model="gemini-3-flash-preview"):
                    ms.GOOGLE_API_KEY = "test-key"
                    self._genai = mock_genai
                    self.model_name = model
                    mock_genai.configure(api_key="test-key")
                with patch.object(gemini_mod.GeminiProvider, "__init__", patched_init):
                    provider = gemini_mod.GeminiProvider()
                    result = await provider.generate("hello")

        assert result == "Gemini response"

    def test_get_model_name(self):
        """GeminiProvider.get_model_name() includes 'Gemini'."""
        mock_genai = MagicMock()
        with patch("app.providers.llm.gemini.settings") as ms:
            ms.GOOGLE_API_KEY = "test-key"
            import app.providers.llm.gemini as gemini_mod
            def patched_init(self, model="gemini-3-flash-preview"):
                self._genai = mock_genai
                self.model_name = model
            with patch.object(gemini_mod.GeminiProvider, "__init__", patched_init):
                provider = gemini_mod.GeminiProvider()
        assert "Gemini" in provider.get_model_name()
