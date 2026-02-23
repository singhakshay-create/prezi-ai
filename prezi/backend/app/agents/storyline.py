from app.providers.base import LLMProvider
from app.models import Storyline, SCQAFramework, Hypothesis
from typing import Literal
import json
import re


class StorylineGenerator:
    """Generates consulting storylines using SCQA framework."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate(self, topic: str, length: Literal["short", "medium", "long"], expanded_brief: str = "") -> Storyline:
        """Generate SCQA storyline with hypotheses."""

        # Determine number of hypotheses based on length
        hypothesis_counts = {
            "short": "2-3",
            "medium": "3-5",
            "long": "5-8"
        }
        num_hypotheses = hypothesis_counts[length]

        system_prompt = """You are an expert management consultant from McKinsey, BCG, or Bain.
Your task is to create a structured storyline using the Pyramid Principle and SCQA framework.

Key principles:
- Pyramid Principle: Start with the answer, then provide supporting arguments
- SCQA: Situation (context), Complication (problem), Question (key question), Answer (recommendation)
- MECE: Hypotheses must be Mutually Exclusive and Collectively Exhaustive
- Hypothesis-driven: Each hypothesis should be testable with data

Action title rules (MANDATORY):
- Every title = complete sentence with verb + specific number
- BAD: "Cloud Market Analysis" / "Sensitivity Analysis" / "Market Segmentation"
- GOOD: "Hybrid cloud grows 3× faster, capturing 45% of new enterprise spend"
- GOOD: "Market size and pricing power drive 70% of value variance"
- The So What test: a partner reads ONLY the titles and understands the full argument
- Chart categories must use real named entities, never "Factor 1", "Segment A", "BU-A"
- chart_hint values must be realistic, research-backed numbers for the specific topic

WRITING STANDARDS (MANDATORY):
- Pyramid principle: lead with conclusion/so-what FIRST, evidence below
- Active voice only: "Companies achieve" not "Results are achieved"
- Quantify everything: include % changes, $ amounts, timeframes
- Bold key terms in output using **term** syntax: **15% revenue growth**, **Q3 2025**
- Eliminate hedge words: never use "somewhat," "possibly," "might," "suggests"
- Strong verbs only: "drives," "delivers," "generates," "captures," "achieves"
- Bullet structure:
    - Main bullet: bold primary finding with quantified impact using **term** syntax
    - Sub-bullets (3-5): specific data points, benchmarks, evidence, risks, timelines
    - Maximum 2 levels of indentation
- Every hypothesis title must answer "so what?" — state the finding definitively
- Forbidden: passive voice, vague qualitative statements, conclusions without data"""

        brief_section = ""
        if expanded_brief:
            brief_section = f"""
RESEARCH BRIEF (use as context for all hypotheses and titles):
{expanded_brief}

Based on the above, create a consulting storyline for: {topic}
"""

        user_prompt = f"""Create a consulting storyline for this business topic:
{brief_section}
Topic: {topic}
Deck Length: {length} ({num_hypotheses} hypotheses)

Generate a structured JSON response with:
1. SCQA Framework with action titles and supporting bullets
2. Governing Thought (one-sentence key message)
3. Key Line (supporting argument for the answer)
4. Hypotheses ({num_hypotheses} testable hypotheses) with action titles and chart hints
5. Recommendation items (3–5 specific numbered actions)

Each hypothesis should:
- Be specific and testable
- Follow MECE principle (mutually exclusive, collectively exhaustive)
- Support the overall answer
- Include a clear testable claim
- Have an action_title that states the finding as fact with a specific number

Return ONLY valid JSON in this exact format:
{{
  "scqa": {{
    "situation": "Current state and context...",
    "situation_title": "6–10 word action title with a specific market stat",
    "situation_bullets": ["**$600B** cloud market grows at **20% CAGR** through 2027 — Gartner 2024 (bold key metrics with **term**)"],
    "complication": "The problem or challenge...",
    "complication_title": "6–10 word action title stating the problem as a finding",
    "complication_bullets": ["**31%** of enterprises missed migration timelines — McKinsey 2024 (bold key numbers with **term**)"],
    "question": "The key question to answer...",
    "answer": "The recommended answer/action..."
  }},
  "governing_thought": "One sentence key message",
  "key_line": "Main supporting argument",
  "recommendation_items": ["Action 1: **verb** + specific outcome with **number** + timeline", "Action 2: **verb** + specific outcome + timeline"],
  "hypotheses": [
    {{
      "id": 1,
      "text": "Hypothesis statement",
      "testable_claim": "Specific claim that can be validated with data",
      "action_title": "Finding as fact with specific number",
      "chart_hint": {{"type": "bar", "categories": ["real category names"], "values": [72, 35, 58], "metric": "axis label with units"}}
    }}
  ],
  "slide_data": {{
    "bar_chart": {{
      "action_title": "6-10 word finding with specific number about market leadership",
      "categories": ["named real entities, not Factor 1"],
      "values": [35, 25, 20, 20],
      "metric": "Market Share (%)"
    }},
    "waterfall": {{
      "action_title": "Strategy delivers $Xm NPV through three levers",
      "categories": ["Current State", "Driver 1 name", "Driver 2 name", "Driver 3 name", "New State"],
      "values": [100, -30, -20, -10, 60],
      "metric": "Cost / Value ($M)"
    }},
    "pie": {{
      "action_title": "Enterprise segment represents X% of addressable market",
      "categories": ["named segment 1", "named segment 2", "named segment 3"],
      "values": [55, 30, 15],
      "metric": "Market Share (%)"
    }},
    "tornado": {{
      "action_title": "Market size and pricing are the most sensitive variables",
      "factors": ["named factor 1", "named factor 2", "named factor 3", "named factor 4", "named factor 5"],
      "upside": [40, 25, 15, 10, 8],
      "downside": [-30, -20, -18, -12, -10]
    }}
  }}
}}"""

        max_tokens = {"short": 20000, "medium": 30000, "long": 40000}[length]
        response = await self.llm.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=max_tokens
        )

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            # Strip invalid '+' prefix from positive numbers (e.g. +5 → 5, +2.1 → 2.1).
            # The LLM sometimes writes waterfall deltas as +5, which is not valid JSON.
            json_str = re.sub(r'(?<=[,\[:\s])\+(?=\d)', '', json_str)

            data = json.loads(json_str)

            # Extract SCQA fields safely
            scqa_data = data["scqa"]
            storyline = Storyline(
                scqa=SCQAFramework(
                    situation=scqa_data["situation"],
                    complication=scqa_data["complication"],
                    question=scqa_data["question"],
                    answer=scqa_data["answer"],
                    situation_title=scqa_data.get("situation_title"),
                    complication_title=scqa_data.get("complication_title"),
                    situation_bullets=scqa_data.get("situation_bullets"),
                    complication_bullets=scqa_data.get("complication_bullets"),
                ),
                governing_thought=data["governing_thought"],
                key_line=data["key_line"],
                hypotheses=[
                    Hypothesis(
                        id=h["id"],
                        text=h["text"],
                        testable_claim=h["testable_claim"],
                        action_title=h.get("action_title"),
                        chart_hint=h.get("chart_hint"),
                    )
                    for h in data["hypotheses"]
                ],
                recommendation_items=data.get("recommendation_items"),
                slide_data=data.get("slide_data"),
            )

            return storyline

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse LLM response into storyline: {e}\nResponse: {response}")
