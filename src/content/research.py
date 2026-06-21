import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
from ddgs import DDGS
import feedparser

from config.settings import settings


@dataclass
class ResearchResult:
    topic: str
    summary: str
    key_points: List[str]
    source_urls: List[str]
    relevance_score: float
    timestamp: datetime


class ResearchAgent:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.ddgs = DDGS()

    async def search_web(self, query: str, max_results: int = 8) -> List[Dict[str, Any]]:
        try:
            results = await asyncio.to_thread(self.ddgs.text, query, max_results=max_results)
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                for r in (results or [])
            ]
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            return []

    async def fetch_rss_feeds(self, feed_urls: List[str]) -> List[Dict[str, Any]]:
        all_entries = []
        for url in feed_urls:
            try:
                feed = await asyncio.to_thread(feedparser.parse, url)
                for entry in feed.entries[:5]:
                    all_entries.append({
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "summary": entry.get("summary", "")[:500],
                        "published": entry.get("published", ""),
                        "source": feed.feed.get("title", url),
                    })
            except Exception as e:
                print(f"RSS fetch error for {url}: {e}")
        return all_entries

    async def research_topic(self, topic: str) -> ResearchResult:
        queries = [
            f"{topic} latest developments 2026",
            f"{topic} practical implications developers 2026",
            f"{topic} vs alternatives comparison 2026",
        ]

        all_results = []
        for q in queries:
            results = await self.search_web(q, max_results=6)
            all_results.extend(results)
            await asyncio.sleep(0.5)

        unique_results = {r["url"]: r for r in all_results if r["url"]}.values()
        top_results = list(unique_results)[:10]

        summary = self._synthesize_summary(topic, list(top_results))
        key_points = self._extract_key_points(list(top_results))
        source_urls = [r["url"] for r in top_results]
        relevance_score = self._calculate_relevance(topic, list(top_results))

        return ResearchResult(
            topic=topic,
            summary=summary,
            key_points=key_points,
            source_urls=source_urls,
            relevance_score=relevance_score,
            timestamp=datetime.now(timezone.utc),
        )

    def _synthesize_summary(self, topic: str, results: List[Dict]) -> str:
        snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
        combined = " ".join(snippets[:5])
        return combined[:800] if combined else f"No detailed summary available for {topic}."

    def _extract_key_points(self, results: List[Dict]) -> List[str]:
        points = []
        for r in results[:7]:
            snippet = r.get("snippet", "")
            if snippet and len(snippet) > 50:
                points.append(snippet[:200])
        return points[:5]

    def _calculate_relevance(self, topic: str, results: List[Dict]) -> float:
        if not results:
            return 0.0
        topic_words = set(topic.lower().split())
        score = 0.0
        for r in results:
            text = (r.get("title", "") + " " + r.get("snippet", "")).lower()
            matches = sum(1 for w in topic_words if w in text)
            score += matches / max(len(topic_words), 1)
        return min(score / len(results), 1.0)

    async def get_trending_topics(self) -> List[str]:
        base_topics = [
            "AI coding agents pricing 2026",
            "agentic AI frameworks 2026",
            "LLM inference optimization 2026",
            "Kubernetes AI workloads 2026",
            "MLOps platforms 2026",
            "vector databases comparison 2026",
            "RAG evaluation frameworks 2026",
            "open source LLM fine-tuning 2026",
            "AI safety alignment 2026",
            "quant finance AI applications 2026",
        ]
        return base_topics

    async def close(self):
        await self.client.aclose()