from app.providers.base import LLMProvider
from app.models import Storyline, SCQAFramework, Hypothesis
from typing import Literal
import json


class StorylineGenerator:
    """Generates consulting storylines using SCQA framework."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate(self, topic: str, length: Literal["short", "medium", "long"]) -> Storyline:
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
- Hypothesis-driven: Each hypothesis should be testable with data"""

        user_prompt = f"""Create a consulting storyline for this business topic:

Topic: {topic}
Deck Length: {length} ({num_hypotheses} hypotheses)

Generate a structured JSON response with:
1. SCQA Framework (situation, complication, question, answer)
2. Governing Thought (one-sentence key message)
3. Key Line (supporting argument for the answer)
4. Hypotheses ({num_hypotheses} testable hypotheses)

Each hypothesis should:
- Be specific and testable
- Follow MECE principle (mutually exclusive, collectively exhaustive)
- Support the overall answer
- Include a clear testable claim

Return ONLY valid JSON in this exact format:
{{
  "scqa": {{
    "situation": "Current state and context...",
    "complication": "The problem or challenge...",
    "question": "The key question to answer...",
    "answer": "The recommended answer/action..."
  }},
  "governing_thought": "One sentence key message",
  "key_line": "Main supporting argument",
  "hypotheses": [
    {{
      "id": 1,
      "text": "Hypothesis statement",
      "testable_claim": "Specific claim that can be validated with data"
    }}
  ]
}}"""

        response = await self.llm.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=2000
        )

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            # Validate and create Storyline object
            storyline = Storyline(
                scqa=SCQAFramework(**data["scqa"]),
                governing_thought=data["governing_thought"],
                key_line=data["key_line"],
                hypotheses=[Hypothesis(**h) for h in data["hypotheses"]]
            )

            return storyline

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse LLM response into storyline: {e}\nResponse: {response}")
