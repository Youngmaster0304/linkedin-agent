from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, JSON, Index
)
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
from typing import Optional

Base = declarative_base()


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(500), nullable=False)
    hook = Column(Text, nullable=False)
    context = Column(Text, nullable=False)
    personal_angle = Column(Text, nullable=False)
    takeaways = Column(JSON, nullable=False)
    closing_question = Column(Text, nullable=False)
    hashtags = Column(JSON, nullable=False)
    full_content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    image_idea = Column(Text, nullable=True)
    image_data = Column(Text, nullable=True)

    status = Column(String(50), default="draft")
    scheduled_at = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    linkedin_post_id = Column(String(100), nullable=True)
    linkedin_post_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_posts_status_scheduled", "status", "scheduled_at"),
        Index("ix_posts_created", "created_at"),
    )


class EngagementMetrics(Base):
    __tablename__ = "engagement_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False, index=True)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    click_through_rate = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)

    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_engagement_post_fetched", "post_id", "fetched_at"),
    )


class TopicPerformance(Base):
    __tablename__ = "topic_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_category = Column(String(100), nullable=False, index=True)
    topic_keywords = Column(JSON, nullable=False)
    avg_engagement_rate = Column(Float, default=0.0)
    avg_impressions = Column(Float, default=0.0)
    post_count = Column(Integer, default=0)
    best_post_id = Column(Integer, nullable=True)
    worst_post_id = Column(Integer, nullable=True)

    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AgentState(Base):
    __tablename__ = "agent_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))