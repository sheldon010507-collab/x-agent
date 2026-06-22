import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.marketing_analysis import MarketingAnalyzer


def test_analyze_turns_research_result_into_marketing_opportunities():
    analyzer = MarketingAnalyzer()
    result = analyzer.analyze(
        {
            "niche": "ai_tools",
            "summary": "Users are asking for cheaper AI workflow automation.",
            "risk_score": 35,
            "citations": [
                {
                    "platform": "reddit",
                    "title": "How do I automate customer research without paying $200/mo?",
                    "text": "Looking for a cheaper way to monitor Reddit and YouTube.",
                    "url": "https://reddit.com/r/example/post",
                },
                {
                    "platform": "youtube",
                    "title": "Best AI workflow tools for small teams",
                    "text": "Small teams want simple tools with less setup.",
                    "url": "https://youtube.com/watch?v=example",
                },
            ],
            "platforms": ["reddit", "youtube"],
        }
    )

    assert result["enabled_skills"] == [
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
    assert result["target_audience"] == "People discussing ai_tools across reddit, youtube"
    assert result["content_angles"]
    assert result["growth_opportunities"]["lead_magnets"]
    assert result["growth_opportunities"]["free_tools"]
    assert result["prospecting_signals"]
    assert result["sales_enablement"]["talking_points"]


def test_analyze_returns_empty_shape_without_research_evidence():
    analyzer = MarketingAnalyzer()
    result = analyzer.analyze({"niche": "general", "citations": [], "platforms": []})

    assert result["target_audience"] == "Unknown audience"
    assert result["content_angles"] == []
    assert result["growth_opportunities"]["lead_magnets"] == []
    assert result["growth_opportunities"]["free_tools"] == []
    assert result["prospecting_signals"] == []
