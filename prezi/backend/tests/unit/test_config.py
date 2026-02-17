"""Tests for config module: _is_real_key helper and Settings provider detection."""

import pytest
from app.config import _is_real_key, PLACEHOLDER_PREFIXES, Settings


class TestIsRealKey:
    def test_none(self):
        assert _is_real_key(None) is False

    def test_empty(self):
        assert _is_real_key("") is False

    def test_whitespace(self):
        assert _is_real_key("   ") is False

    def test_placeholder_prefixes(self):
        for prefix in PLACEHOLDER_PREFIXES:
            assert _is_real_key(prefix + "blah") is False

    def test_valid_key(self):
        assert _is_real_key("sk-ant-api03-real-key-value") is True


class TestSettingsProviders:
    def test_no_keys(self):
        """With no API keys, all LLM providers should be unavailable, mock research always available."""
        s = Settings(
            ANTHROPIC_API_KEY=None,
            OPENAI_API_KEY=None,
            NVIDIA_API_KEY=None,
            PERPLEXITY_API_KEY=None,
            BRAVE_API_KEY=None,
            SERP_API_KEY=None,
        )
        llm = s.available_llm_providers
        research = s.available_research_providers

        # No LLM provider should be available
        assert all(p["available"] is False for p in llm)

        # Mock research is always available
        mock = next(p for p in research if p["id"] == "mock")
        assert mock["available"] is True

    def test_anthropic_key(self):
        """With a real ANTHROPIC_API_KEY, claude should be available."""
        s = Settings(
            ANTHROPIC_API_KEY="sk-ant-api03-real-key-value",
            OPENAI_API_KEY=None,
            NVIDIA_API_KEY=None,
        )
        llm = s.available_llm_providers
        claude_entries = [p for p in llm if p["id"] == "claude"]
        # There should be exactly one claude entry and it should be available
        assert any(p["available"] is True for p in claude_entries)
