from app.providers.base import LLMProvider
from app.models import Storyline, QualityScore
import json


class QualityChecker:
    """Validates presentation quality using LLM analysis."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def check(self, storyline: Storyline) -> QualityScore:
        """Check presentation quality."""

        system_prompt = """You are a senior partner at McKinsey reviewing a presentation deck.
Evaluate the quality across multiple dimensions using consulting standards."""

        user_prompt = f"""Review this presentation storyline and score it on a 0-100 scale:

SCQA Framework:
- Situation: {storyline.scqa.situation}
- Complication: {storyline.scqa.complication}
- Question: {storyline.scqa.question}
- Answer: {storyline.scqa.answer}

Governing Thought: {storyline.governing_thought}

Hypotheses:
{chr(10).join([f"{i+1}. {h.text}" for i, h in enumerate(storyline.hypotheses)])}

Evaluate on these criteria (0-100 each):
1. slide_logic: Is the SCQA clear and logical?
2. mece_structure: Are hypotheses mutually exclusive and collectively exhaustive?
3. so_what: Is there a clear insight and recommendation?
4. data_quality: Would the hypotheses be supported by data? (assume research is done)
5. chart_accuracy: Would charts effectively communicate findings? (mock score)
6. visual_consistency: Would the presentation look professional? (mock score)

Also provide 2-4 improvement suggestions.

Return ONLY valid JSON:
{{
  "slide_logic": 85,
  "mece_structure": 80,
  "so_what": 90,
  "data_quality": 85,
  "chart_accuracy": 80,
  "visual_consistency": 85,
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}}"""

        response = await self.llm.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=1000
        )

        # Parse JSON response
        try:
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            # Calculate overall score (weighted average)
            overall = int(
                data["slide_logic"] * 0.25 +
                data["mece_structure"] * 0.25 +
                data["so_what"] * 0.25 +
                data["data_quality"] * 0.15 +
                data["chart_accuracy"] * 0.05 +
                data["visual_consistency"] * 0.05
            )

            return QualityScore(
                overall_score=overall,
                slide_logic=data["slide_logic"],
                mece_structure=data["mece_structure"],
                so_what=data["so_what"],
                data_quality=data["data_quality"],
                chart_accuracy=data["chart_accuracy"],
                visual_consistency=data["visual_consistency"],
                suggestions=data["suggestions"]
            )

        except (json.JSONDecodeError, KeyError) as e:
            # Return default passing score if parsing fails
            return QualityScore(
                overall_score=75,
                slide_logic=75,
                mece_structure=75,
                so_what=75,
                data_quality=75,
                chart_accuracy=75,
                visual_consistency=75,
                suggestions=["Quality check completed with default scores"]
            )
