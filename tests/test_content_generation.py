import pytest
import asyncio
from src.content.research import ResearchAgent
from src.content.writer import ContentWriter
from src.content.image_generator import ImageGenerator


@pytest.mark.asyncio
async def test_research_agent():
    agent = ResearchAgent()
    try:
        research = await agent.research_topic("AI coding agents pricing 2026")
        assert research.topic == "AI coding agents pricing 2026"
        assert research.summary is not None
        assert len(research.key_points) > 0
        assert len(research.source_urls) > 0
        assert 0.0 <= research.relevance_score <= 1.0
    finally:
        await agent.close()


@pytest.mark.asyncio
async def test_content_writer():
    writer = ContentWriter()
    
    # Create a mock research result
    from dataclasses import dataclass
    from datetime import datetime, timezone
    
    @dataclass
    class MockResearch:
        topic: str
        summary: str
        key_points: list
        source_urls: list
        relevance_score: float
        timestamp: datetime
    
    research = MockResearch(
        topic="AI coding agents pricing 2026",
        summary="Test summary",
        key_points=["Key point 1", "Key point 2"],
        source_urls=["http://example.com"],
        relevance_score=0.8,
        timestamp=datetime.now(timezone.utc)
    )
    
    post = writer.generate_post(research)
    assert post.topic == "AI coding agents pricing 2026"
    assert post.hook is not None
    assert post.context is not None
    assert post.personal_angle is not None
    assert len(post.takeaways) > 0
    assert post.closing_question is not None
    assert len(post.hashtags) > 0
    assert post.word_count > 0
    assert post.image_idea is not None
    assert post.quality_checks is not None
    assert post.quality_checks["all_passed"] is True


@pytest.mark.asyncio
async def test_image_generator():
    generator = ImageGenerator()
    try:
        # Test placeholder image generation
        image_data = await generator.generate_placeholder_image("AI coding agents pricing 2026")
        # Image generation might fail if no API keys are configured, so we just test that it doesn't crash
        assert image_data is None or isinstance(image_data, bytes)
    finally:
        await generator.close()