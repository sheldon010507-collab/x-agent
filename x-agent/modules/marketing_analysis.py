"""Lightweight marketing analysis for research results.

This models a small subset of marketingskills as deterministic post-processing.
It does not create another agent or add external dependencies.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


MARKETING_SKILLS = [
    "product-marketing",
    "customer-research",
    "competitor-profiling",
    "content-strategy",
    "social",
    "copywriting",
    "marketing-psychology",
    "prospecting",
    "lead-magnets",
    "free-tools",
    "sales-enablement",
]


class MarketingAnalyzer:
    """Turn synthesized research evidence into publishable marketing insight."""

    def analyze(self, research_result: Dict[str, Any]) -> Dict[str, Any]:
        niche = research_result.get("niche") or "general"
        citations = self._citations(research_result.get("citations", []))
        platforms = self._platforms(research_result)

        if not citations:
            return {
                "enabled_skills": MARKETING_SKILLS,
                "target_audience": "Unknown audience",
                "positioning": "",
                "customer_research": {"pain_points": [], "voice_of_customer": []},
                "content_angles": [],
                "growth_opportunities": {"lead_magnets": [], "free_tools": []},
                "prospecting_signals": [],
                "sales_enablement": {"talking_points": [], "objections": []},
                "publisher_brief": "",
            }

        pain_points = self._pain_points(citations)
        voice = [c["text"] for c in citations[:3] if c["text"]]
        platforms_label = ", ".join(platforms) if platforms else "searched platforms"
        top_terms = self._top_terms(" ".join(c["text"] for c in citations))
        primary_term = top_terms[0] if top_terms else niche.replace("_", " ")

        return {
            "enabled_skills": MARKETING_SKILLS,
            "target_audience": f"People discussing {niche} across {platforms_label}",
            "positioning": (
                f"Frame {niche} around the repeated need for {primary_term}, "
                "with proof from recent platform conversations."
            ),
            "customer_research": {
                "pain_points": pain_points,
                "voice_of_customer": voice,
            },
            "content_angles": self._content_angles(niche, citations, top_terms),
            "growth_opportunities": {
                "lead_magnets": self._lead_magnets(niche, primary_term),
                "free_tools": self._free_tools(niche, primary_term),
            },
            "prospecting_signals": self._prospecting_signals(citations),
            "sales_enablement": self._sales_enablement(niche, pain_points, research_result),
            "publisher_brief": self._publisher_brief(niche, platforms_label, primary_term),
        }

    def _citations(self, raw: Iterable[Dict[str, Any]]) -> List[Dict[str, str]]:
        citations = []
        for item in raw or []:
            if not isinstance(item, dict):
                continue
            text = item.get("text") or item.get("title") or ""
            title = item.get("title") or text
            if not text and not title:
                continue
            citations.append(
                {
                    "platform": str(item.get("platform") or "unknown"),
                    "title": str(title).strip(),
                    "text": str(text).strip(),
                    "url": str(item.get("url") or ""),
                }
            )
        return citations

    def _platforms(self, research_result: Dict[str, Any]) -> List[str]:
        platforms = research_result.get("platforms") or research_result.get("platform_sources") or []
        if not isinstance(platforms, list):
            return []
        return [str(platform) for platform in platforms if platform]

    def _pain_points(self, citations: List[Dict[str, str]]) -> List[str]:
        return [
            f"{citation['platform']}: {self._shorten(citation['text'] or citation['title'], 120)}"
            for citation in citations[:5]
        ]

    def _content_angles(
        self, niche: str, citations: List[Dict[str, str]], top_terms: List[str]
    ) -> List[Dict[str, str]]:
        first = citations[0]
        terms = ", ".join(top_terms[:3]) if top_terms else niche.replace("_", " ")
        return [
            {
                "skill": "content-strategy",
                "angle": f"What people are asking about {niche} right now",
                "rationale": self._shorten(first["text"] or first["title"], 140),
            },
            {
                "skill": "social",
                "angle": f"Turn {terms} into a short platform-native thread",
                "rationale": "Use repeated language from recent discussions instead of generic claims.",
            },
            {
                "skill": "copywriting",
                "angle": f"Lead with the problem, then show the simplest {niche} workflow",
                "rationale": "Keeps the post useful before asking for attention or action.",
            },
        ]

    def _lead_magnets(self, niche: str, primary_term: str) -> List[str]:
        label = niche.replace("_", " ")
        return [
            f"{label} pain-point checklist focused on {primary_term}",
            f"Weekly {label} trend brief built from multi-platform evidence",
        ]

    def _free_tools(self, niche: str, primary_term: str) -> List[str]:
        label = niche.replace("_", " ")
        return [
            f"{label} opportunity scorer for {primary_term}",
            f"Simple monitor that tracks new {label} discussions across selected platforms",
        ]

    def _prospecting_signals(self, citations: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return [
            {
                "platform": citation["platform"],
                "signal": self._shorten(citation["title"] or citation["text"], 100),
                "source_url": citation["url"],
            }
            for citation in citations[:5]
        ]

    def _sales_enablement(
        self, niche: str, pain_points: List[str], research_result: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        risk_score = research_result.get("risk_score", 100)
        review_note = (
            "Keep claims conservative and ask for human review before publishing."
            if risk_score >= 50
            else "Use recent evidence as proof, but avoid unsupported performance claims."
        )
        lead_pain = pain_points[0] if pain_points else f"People need clarity around {niche}."
        return {
            "talking_points": [
                f"Open with the observed pain: {lead_pain}",
                "Show the evidence source before offering a recommendation.",
                review_note,
            ],
            "objections": [
                "Why trust this signal?",
                "Is this trend broad enough to act on?",
                "What is the simplest next step?",
            ],
        }

    def _publisher_brief(self, niche: str, platforms_label: str, primary_term: str) -> str:
        return (
            f"Draft posts about {niche} using evidence from {platforms_label}; "
            f"lead with {primary_term}, then offer one useful next step."
        )

    def _top_terms(self, text: str) -> List[str]:
        stop_words = {
            "about",
            "across",
            "after",
            "again",
            "best",
            "from",
            "have",
            "into",
            "less",
            "looking",
            "need",
            "simple",
            "that",
            "their",
            "there",
            "this",
            "tools",
            "want",
            "with",
            "without",
        }
        counts: Dict[str, int] = {}
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", text.lower()):
            if term in stop_words:
                continue
            counts[term] = counts.get(term, 0) + 1
        sorted_terms = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [term for term, _count in sorted_terms[:5]]

    def _shorten(self, text: str, max_len: int) -> str:
        normalized = " ".join((text or "").split())
        if len(normalized) <= max_len:
            return normalized
        return normalized[: max_len - 3].rstrip() + "..."
