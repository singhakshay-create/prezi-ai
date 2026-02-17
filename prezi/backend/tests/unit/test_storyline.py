"""Tests for StorylineGenerator agent."""

import json
import pytest

from app.agents.storyline import StorylineGenerator
from app.models import Storyline
from tests.conftest import MockLLMProvider


class TestStorylineGenerate:
    """Tests for StorylineGenerator.generate()."""

    async def test_generate_short(self, sample_storyline_json):
        """length='short' → prompt mentions '2-3' hypotheses."""
        llm = MockLLMProvider(response=sample_storyline_json)
        gen = StorylineGenerator(llm)
        await gen.generate("Cloud adoption strategy for enterprise clients", "short")

        prompt = llm.calls[0]["prompt"]
        assert "2-3" in prompt

    async def test_generate_medium(self, sample_storyline_json):
        """length='medium' → prompt mentions '3-5' hypotheses."""
        llm = MockLLMProvider(response=sample_storyline_json)
        gen = StorylineGenerator(llm)
        await gen.generate("Cloud adoption strategy for enterprise clients", "medium")

        prompt = llm.calls[0]["prompt"]
        assert "3-5" in prompt

    async def test_generate_long(self, sample_storyline_json):
        """length='long' → prompt mentions '5-8' hypotheses."""
        llm = MockLLMProvider(response=sample_storyline_json)
        gen = StorylineGenerator(llm)
        await gen.generate("Cloud adoption strategy for enterprise clients", "long")

        prompt = llm.calls[0]["prompt"]
        assert "5-8" in prompt

    async def test_parses_clean_json(self, sample_storyline_json):
        """Clean JSON response → valid Storyline object."""
        llm = MockLLMProvider(response=sample_storyline_json)
        gen = StorylineGenerator(llm)
        result = await gen.generate("Cloud adoption strategy for enterprise clients", "short")

        assert isinstance(result, Storyline)
        assert result.scqa.situation.startswith("The global")
        assert len(result.hypotheses) == 3

    async def test_parses_json_in_markdown_block(self, sample_storyline_json):
        """```json {...} ``` wrapping → parses correctly."""
        wrapped = f"```json\n{sample_storyline_json}\n```"
        llm = MockLLMProvider(response=wrapped)
        gen = StorylineGenerator(llm)
        result = await gen.generate("Cloud adoption strategy for enterprise clients", "short")

        assert isinstance(result, Storyline)
        assert len(result.hypotheses) == 3

    async def test_parses_generic_code_block(self, sample_storyline_json):
        """``` {...} ``` wrapping → parses correctly."""
        wrapped = f"```\n{sample_storyline_json}\n```"
        llm = MockLLMProvider(response=wrapped)
        gen = StorylineGenerator(llm)
        result = await gen.generate("Cloud adoption strategy for enterprise clients", "short")

        assert isinstance(result, Storyline)

    async def test_raises_on_invalid_json(self):
        """LLM returns garbage text → ValueError."""
        llm = MockLLMProvider(response="This is not JSON at all")
        gen = StorylineGenerator(llm)

        with pytest.raises(ValueError, match="Failed to parse"):
            await gen.generate("Cloud adoption strategy for enterprise clients", "short")

    async def test_raises_on_missing_scqa(self):
        """JSON missing 'scqa' key → ValueError."""
        bad_json = json.dumps({"governing_thought": "x", "key_line": "y", "hypotheses": []})
        llm = MockLLMProvider(response=bad_json)
        gen = StorylineGenerator(llm)

        with pytest.raises(ValueError, match="Failed to parse"):
            await gen.generate("Cloud adoption strategy for enterprise clients", "short")

    async def test_system_prompt_content(self, sample_storyline_json):
        """Verify mock LLM received system prompt with key consulting terms."""
        llm = MockLLMProvider(response=sample_storyline_json)
        gen = StorylineGenerator(llm)
        await gen.generate("Cloud adoption strategy for enterprise clients", "short")

        system = llm.calls[0]["system"]
        assert "McKinsey" in system
        assert "SCQA" in system
        assert "MECE" in system
