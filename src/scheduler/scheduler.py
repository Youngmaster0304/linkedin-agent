import asyncio
from datetime import datetime, time, timedelta
from typing import List, Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz
import structlog
import base64

from config.settings import settings
from src.storage.database import get_session, init_db

def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
from src.storage.models import Post, AgentState
from src.content.research import ResearchAgent
from src.content.writer import ContentWriter
from src.poster.linkedin_poster import LinkedInPoster

logger = structlog.get_logger()


class AgentScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(settings.timezone))
        self.research_agent = ResearchAgent()
        self.writer = ContentWriter()
        self._running = False

    async def start(self):
        await init_db()
        self._setup_jobs()
        self.scheduler.start()
        self._running = True
        logger.info("Scheduler started", timezone=settings.timezone)

    async def shutdown(self):
        self.scheduler.shutdown(wait=True)
        await self.research_agent.close()
        self._running = False
        logger.info("Scheduler stopped")

    def _setup_jobs(self):
        post_hour, post_minute = map(int, settings.post_time_utc.split(":"))
        
        self.scheduler.add_job(
            self._generate_and_schedule_posts,
            CronTrigger(hour=post_hour, minute=post_minute),
            id="daily_post_generation",
            name="Generate and schedule daily posts",
            max_instances=1,
            coalesce=True,
        )

        self.scheduler.add_job(
            self._check_and_publish_due_posts,
            IntervalTrigger(minutes=15),
            id="publish_due_posts",
            name="Check and publish due posts",
            max_instances=1,
            coalesce=True,
        )

        if settings.track_engagement:
            self.scheduler.add_job(
                self._fetch_engagement_metrics,
                IntervalTrigger(hours=settings.engagement_check_hours),
                id="fetch_engagement",
                name="Fetch engagement metrics",
                max_instances=1,
                coalesce=True,
            )

        self.scheduler.add_job(
            self._update_topic_performance,
            CronTrigger(hour=2, minute=0),
            id="update_performance",
            name="Update topic performance analytics",
            max_instances=1,
            coalesce=True,
        )

    async def _generate_and_schedule_posts(self):
        logger.info("Starting daily post generation")
        try:
            topics = await self.research_agent.get_trending_topics()
            
            async with get_session() as session:
                for topic in topics[:settings.posts_per_week]:
                    research = await self.research_agent.research_topic(topic)
                    
                    if research.relevance_score < 0.3:
                        logger.info("Skipping low relevance topic", topic=topic, score=research.relevance_score)
                        continue

                    generated = await self.writer.generate_with_image(research)
                    
                    if not generated.quality_checks.get("all_passed", False):
                        logger.warning("Quality checks failed", topic=topic, checks=generated.quality_checks)
                        continue

                    post = Post(
                        topic=generated.topic,
                        hook=generated.hook,
                        context=generated.context,
                        personal_angle=generated.personal_angle,
                        takeaways=generated.takeaways,
                        closing_question=generated.closing_question,
                        hashtags=generated.hashtags,
                        full_content=generated.full_content,
                        word_count=generated.word_count,
                        image_idea=generated.image_idea,
                        image_data=base64.b64encode(generated.image_data).decode('utf-8') if generated.image_data else None,
                        status="scheduled",
                        scheduled_at=_now() + timedelta(hours=1),
                    )
                    session.add(post)
                    logger.info("Post scheduled", topic=topic, post_id=post.id, has_image=generated.image_data is not None)

        except Exception as e:
            logger.error("Post generation error", error=str(e))

    async def _check_and_publish_due_posts(self):
        now = _now()
        async with get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Post).where(
                    Post.status == "scheduled",
                    Post.scheduled_at <= now
                ).limit(1)
            )
            post = result.scalar_one_or_none()
            
            if post:
                await self._publish_post(post, session)

    async def _publish_post(self, post: Post, session):
        logger.info("Publishing post", post_id=post.id)
        post.status = "publishing"
        
        async with LinkedInPoster() as poster:
            logged_in = await poster.login()
            if not logged_in:
                post.status = "failed"
                logger.error("LinkedIn login failed")
                return

            image_data = None
            if post.image_data:
                try:
                    image_data = base64.b64decode(post.image_data)
                except Exception as e:
                    logger.warning("Failed to decode image data", error=str(e))

            success, post_id, post_url = await poster.create_post(post.full_content, image_data)
            
            if success:
                post.status = "published"
                post.posted_at = datetime.now(timezone.utc)
                post.linkedin_post_id = post_id
                post.linkedin_post_url = post_url
                logger.info("Post published successfully", post_id=post.id, linkedin_id=post_id)
            else:
                post.status = "failed"
                logger.error("Post publication failed")

    async def _fetch_engagement_metrics(self):
        logger.info("Fetching engagement metrics")
        async with get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Post).where(
                    Post.status == "published",
                    Post.linkedin_post_url.isnot(None)
                ).limit(10)
            )
            posts = result.scalars().all()

            async with LinkedInPoster() as poster:
                logged_in = await poster.login()
                if not logged_in:
                    return

                for post in posts:
                    metrics = await poster.fetch_engagement(post.linkedin_post_url)
                    
                    from src.storage.models import EngagementMetrics
                    engagement = EngagementMetrics(
                        post_id=post.id,
                        likes=metrics.get("likes", 0),
                        comments=metrics.get("comments", 0),
                        shares=metrics.get("shares", 0),
                        impressions=0,
                    )
                    session.add(engagement)
                    logger.info("Engagement fetched", post_id=post.id, metrics=metrics)

    async def _update_topic_performance(self):
        logger.info("Updating topic performance")
        async with get_session() as session:
            from sqlalchemy import select, func
            from src.storage.models import TopicPerformance, EngagementMetrics
            
            result = await session.execute(
                select(
                    Post.topic,
                    func.avg(EngagementMetrics.likes + EngagementMetrics.comments + EngagementMetrics.shares).label("avg_engagement"),
                    func.count(Post.id).label("post_count"),
                )
                .join(EngagementMetrics, Post.id == EngagementMetrics.post_id)
                .group_by(Post.topic)
            )
            
            for row in result:
                perf = TopicPerformance(
                    topic_category=row.topic.split()[0] if row.topic else "general",
                    topic_keywords=row.topic.split()[:5],
                    avg_engagement_rate=row.avg_engagement or 0,
                    post_count=row.post_count,
                )
                session.merge(perf)

    async def run_once(self):
        await self._generate_and_schedule_posts()
        await self._check_and_publish_due_posts()
        if settings.track_engagement:
            await self._fetch_engagement_metrics()