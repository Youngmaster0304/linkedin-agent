from datetime import datetime, timedelta, timezone

def _now():
    return _now().replace(tzinfo=None)
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy import select, func, and_
import structlog

from src.storage.database import get_session
from src.storage.models import Post, EngagementMetrics, TopicPerformance, AgentState

logger = structlog.get_logger()


@dataclass
class PostAnalytics:
    post_id: int
    topic: str
    word_count: int
    posted_at: Optional[datetime]
    total_engagement: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float
    days_since_posted: int


@dataclass
class TopicAnalytics:
    category: str
    keywords: List[str]
    post_count: int
    avg_engagement: float
    best_performing_post: Optional[int]
    trend: str


class AnalyticsEngine:
    async def get_post_performance(self, days: int = 30) -> List[PostAnalytics]:
        cutoff = _now() - timedelta(days=days)
        
        async with get_session() as session:
            result = await session.execute(
                select(
                    Post.id,
                    Post.topic,
                    Post.word_count,
                    Post.posted_at,
                    func.coalesce(func.sum(EngagementMetrics.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(EngagementMetrics.comments), 0).label("total_comments"),
                    func.coalesce(func.sum(EngagementMetrics.shares), 0).label("total_shares"),
                )
                .outerjoin(EngagementMetrics, Post.id == EngagementMetrics.post_id)
                .where(Post.posted_at >= cutoff)
                .group_by(Post.id, Post.topic, Post.word_count, Post.posted_at)
                .order_by(Post.posted_at.desc())
            )
            
            analytics = []
            for row in result:
                total = row.total_likes + row.total_comments + row.total_shares
                days_since = (_now() - row.posted_at).days if row.posted_at else 0
                rate = total / max(days_since, 1) if days_since > 0 else 0
                
                analytics.append(PostAnalytics(
                    post_id=row.id,
                    topic=row.topic,
                    word_count=row.word_count,
                    posted_at=row.posted_at,
                    total_engagement=total,
                    likes=row.total_likes,
                    comments=row.total_comments,
                    shares=row.total_shares,
                    engagement_rate=round(rate, 2),
                    days_since_posted=days_since,
                ))
            
            return analytics

    async def get_topic_performance(self) -> List[TopicAnalytics]:
        async with get_session() as session:
            result = await session.execute(
                select(TopicPerformance).order_by(TopicPerformance.avg_engagement_rate.desc())
            )
            
            analytics = []
            for row in result.scalars():
                trend = "improving" if row.avg_engagement_rate > 10 else "stable"
                analytics.append(TopicAnalytics(
                    category=row.topic_category,
                    keywords=row.topic_keywords,
                    post_count=row.post_count,
                    avg_engagement=row.avg_engagement_rate,
                    best_performing_post=row.best_post_id,
                    trend=trend,
                ))
            
            return analytics

    async def get_optimal_posting_time(self) -> Dict[str, Any]:
        async with get_session() as session:
            result = await session.execute(
                select(
                    func.strftime("%H", Post.posted_at).label("hour"),
                    func.avg(EngagementMetrics.likes + EngagementMetrics.comments + EngagementMetrics.shares).label("avg_engagement"),
                    func.count(Post.id).label("post_count"),
                )
                .join(EngagementMetrics, Post.id == EngagementMetrics.post_id)
                .where(Post.posted_at.isnot(None))
                .group_by("hour")
                .order_by(func.avg(EngagementMetrics.likes + EngagementMetrics.comments + EngagementMetrics.shares).desc())
            )
            
            hours = []
            for row in result:
                hours.append({
                    "hour": int(row.hour),
                    "avg_engagement": round(row.avg_engagement, 2),
                    "post_count": row.post_count,
                })
            
            best_hour = hours[0]["hour"] if hours else 10
            return {"best_hour_utc": best_hour, "hourly_breakdown": hours}

    async def get_content_insights(self) -> Dict[str, Any]:
        async with get_session() as session:
            result = await session.execute(
                select(
                    func.avg(Post.word_count).label("avg_word_count"),
                    func.min(Post.word_count).label("min_word_count"),
                    func.max(Post.word_count).label("max_word_count"),
                    func.count(Post.id).label("total_posts"),
                )
                .where(Post.status == "published")
            )
            row = result.one()
            
            hook_result = await session.execute(
                select(Post.hook, func.avg(EngagementMetrics.likes + EngagementMetrics.comments + EngagementMetrics.shares).label("avg_engagement"))
                .join(EngagementMetrics, Post.id == EngagementMetrics.post_id)
                .group_by(Post.hook)
                .order_by(func.avg(EngagementMetrics.likes + EngagementMetrics.comments + EngagementMetrics.shares).desc())
                .limit(5)
            )
            
            top_hooks = [{"hook": r.hook[:100], "avg_engagement": round(r.avg_engagement, 2)} for r in hook_result]
            
            return {
                "avg_word_count": round(row.avg_word_count or 0),
                "word_count_range": f"{row.min_word_count}-{row.max_word_count}",
                "total_published": row.total_posts,
                "top_performing_hooks": top_hooks,
            }

    async def generate_weekly_report(self) -> Dict[str, Any]:
        post_perf = await self.get_post_performance(7)
        topic_perf = await self.get_topic_performance()
        optimal_time = await self.get_optimal_posting_time()
        content_insights = await self.get_content_insights()
        
        total_engagement = sum(p.total_engagement for p in post_perf)
        avg_engagement = total_engagement / len(post_perf) if post_perf else 0
        
        return {
            "period": "7_days",
            "generated_at": _now().isoformat(),
            "summary": {
                "posts_published": len(post_perf),
                "total_engagement": total_engagement,
                "avg_engagement_per_post": round(avg_engagement, 2),
            },
            "top_posts": sorted(post_perf, key=lambda x: x.total_engagement, reverse=True)[:3],
            "topic_performance": topic_perf,
            "optimal_posting_time": optimal_time,
            "content_insights": content_insights,
            "recommendations": self._generate_recommendations(post_perf, topic_perf, optimal_time),
        }

    def _generate_recommendations(
        self,
        posts: List[PostAnalytics],
        topics: List[TopicAnalytics],
        optimal_time: Dict,
    ) -> List[str]:
        recs = []
        
        if posts:
            best = max(posts, key=lambda x: x.total_engagement)
            recs.append(f"Replicate format from top post: '{best.topic[:50]}...' ({best.total_engagement} engagement)")
        
        if topics:
            best_topic = topics[0]
            recs.append(f"Focus on '{best_topic.category}' topics (avg {best_topic.avg_engagement:.1f} engagement)")
        
        best_hour = optimal_time.get("best_hour_utc", 10)
        recs.append(f"Schedule posts at {best_hour}:00 UTC for maximum reach")
        
        if posts:
            avg_words = sum(p.word_count for p in posts) / len(posts)
            if avg_words > 250:
                recs.append("Consider shorter posts (under 250 words) for higher engagement")
        
        return recs


async def get_dashboard_data() -> Dict[str, Any]:
    engine = AnalyticsEngine()
    return await engine.generate_weekly_report()