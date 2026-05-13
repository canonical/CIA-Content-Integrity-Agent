"""
LLMClient: OpenRouter client for LLM-powered reasoning.
"""

import json
import logging
import os
import re

import requests

from utils.url_similarity import get_path_segments, jaccard_similarity

logger = logging.getLogger(__name__)

# Cap fallback confidence to avoid overstating certainty without LLM
_FALLBACK_CONFIDENCE_MULTIPLIER = 0.5
_FALLBACK_CONFIDENCE_CAP = 0.5


class LLMClient:
    """Client for OpenRouter API with deterministic fallback."""

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or "openai/gpt-4o-mini"

    def _fallback_suggest(self, broken_url: str, candidate_urls: list) -> dict:
        if not candidate_urls:
            return {
                "suggested_url": None,
                "confidence": 0.0,
                "reasoning": "No candidates available for fallback matching.",
                "user_facing_explanation": "No LLM available. No candidates to suggest.",
            }

        broken_segments = get_path_segments(broken_url)
        best_url = None
        best_score = 0.0

        for url in candidate_urls:
            candidate_segments = get_path_segments(url)
            score = jaccard_similarity(broken_segments, candidate_segments)
            if score > best_score:
                best_score = score
                best_url = url

        capped = min(best_score * _FALLBACK_CONFIDENCE_MULTIPLIER, _FALLBACK_CONFIDENCE_CAP)
        return {
            "suggested_url": best_url,
            "confidence": capped,
            "reasoning": f"Jaccard similarity fallback score: {best_score:.3f}",
            "user_facing_explanation": "No LLM available. Fallback suggestion based on URL similarity.",
        }

    def _parse_json_response(self, raw: str) -> dict:
        text = raw.strip()
        fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
        match = fence_pattern.search(text)
        if match:
            text = match.group(1).strip()

        try:
            parsed = json.loads(text)
            return {
                "suggested_url": parsed.get("suggested_url"),
                "confidence": float(parsed.get("confidence", 0.0)),
                "reasoning": parsed.get("reasoning", ""),
                "user_facing_explanation": parsed.get("user_facing_explanation", ""),
            }
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "suggested_url": None,
                "confidence": 0.0,
                "reasoning": f"JSON parse error: {e}",
                "user_facing_explanation": "Failed to parse LLM response.",
            }

    def suggest_fix(self, broken_url: str, source_page: str, page_context: str,
                    candidate_urls: list) -> dict:
        if not self.api_key:
            return self._fallback_suggest(broken_url, candidate_urls)

        system_msg = (
            'You are a Content Integrity Assistant. Respond in strict JSON: '
            '{"suggested_url": "..." or null, "confidence": 0.0-1.0, '
            '"reasoning": "...", "user_facing_explanation": "..."}'
        )
        user_msg = (
            f"Broken URL: {broken_url}\n"
            f"Source page: {source_page}\n"
            f"Page context: {page_context}\n"
            f"Candidates: {', '.join(candidate_urls) if candidate_urls else 'none'}\n"
            "What is the most likely correct replacement?"
        )

        try:
            response = requests.post(
                self.OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://canonical.com",
                    "X-Title": "Content Integrity Agent",
                },
                json={
                    "model": self.model,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_json_response(content)
        except Exception as e:
            logger.warning("OpenRouter API call failed, using fallback: %s", e)
            return self._fallback_suggest(broken_url, candidate_urls)

    def draft_email(self, owner_name: str, failure_count: int, suggestions: list,
                    action: str) -> str:
        lines = [
            f"Hi {owner_name},",
            "",
            f"We found {failure_count} broken link(s) on pages you own.",
        ]

        if suggestions:
            lines.append("")
            lines.append("Suggested fixes:")
            for i, s in enumerate(suggestions, 1):
                if isinstance(s, dict):
                    url = s.get("suggested_url", "N/A")
                    explanation = s.get("user_facing_explanation", "")
                    lines.append(f"  {i}. {explanation} → {url}")
                else:
                    lines.append(f"  {i}. {s}")

        lines.append("")
        lines.append(f"Recommended action: {action}")
        lines.append("")
        lines.append("— Content Integrity Agent")

        return "\n".join(lines)
