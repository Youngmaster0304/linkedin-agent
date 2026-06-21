 HEAD
# LinkedIn Content Automation Agent

Autonomous LinkedIn Content Automation Agent for Abhinav Jha — a dual-degree student (B.Tech ECE at IIIT Manipur + BS Data Science at IIT Madras), AI practitioner, and Social Media & Content Head at Synapse Club.

## Overview

This project implements a complete LinkedIn content automation agent that:
- Researches trending AI and tech topics
- Generates authentic, student-builder focused LinkedIn posts
- Posts to LinkedIn with optional images
- Tracks engagement and performance
- Provides analytics and recommendations

## Core Features

### Content Generation Pipeline
- **Research Agent**: Searches web and RSS feeds for latest AI/tech developments
- **Content Writer**: Generates authentic LinkedIn posts with personal angles
- **Image Generator**: Creates professional images for posts (OpenAI/Gemini/Groq)
- **Quality Checks**: Ensures posts meet LinkedIn guidelines and authenticity

### LinkedIn Integration
- **Playwright-based Poster**: Automated LinkedIn posting with stealth techniques
- **Image Upload**: Supports image uploads for enhanced engagement
- **2FA Support**: Handles LinkedIn 2FA authentication
- **Error Handling**: Robust error handling and retry logic

### Scheduling & Automation
- **APScheduler**: Daily post generation at configured times
- **GitHub Actions**: CI/CD pipeline for automated deployment
- **Flexible Scheduling**: Configurable posting frequency and times

### Analytics & Learning
- **Engagement Tracking**: Monitors likes, comments, shares, and CTR
- **Performance Analytics**: Tracks topic performance and optimal posting times
- **Weekly Reports**: Generates comprehensive analytics reports
- **Recommendations**: Provides data-driven content recommendations

## Technical Architecture

### Modules
- `src/content/`: Research, writing, and image generation
- `src/poster/`: LinkedIn posting automation
- `src/scheduler/`: Job scheduling and workflow management
- `src/analytics/`: Performance tracking and reporting
- `src/storage/`: Database models and persistence
- `config/`: Settings and configuration management

### Dependencies
- Python 3.11+
- FastAPI, uvicorn
- APScheduler, Playwright
- SQLAlchemy, Alembic
- OpenAI, Anthropic, Gemini, Groq APIs
- PostgreSQL/MySQL/SQLite

## Configuration

### Environment Variables
Create a `.env` file with the following:

```env
# LinkedIn Credentials (REQUIRED)
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-linkedin-password
LINKEDIN_2FA_SECRET=your-totp-secret-from-authenticator-app

# LLM API Keys (at least one required)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key

# Database (default: local SQLite)
DATABASE_URL=sqlite+aiosqlite:///./data/linkedin_agent.db

# Scheduling
POST_TIME_UTC=10:00
TIMEZONE=Asia/Kolkata
POSTS_PER_WEEK=12

# Content Generation
MAX_POST_LENGTH=280
MIN_POST_LENGTH=150
RESEARCH_DEPTH=deep

# Playwright
HEADLESS=true
BROWSER_TIMEOUT=60000

# Analytics
TRACK_ENGAGEMENT=true
ENGAGEMENT_CHECK_HOURS=24

# Storage
DATA_DIR=./data
```

### GitHub Actions
The project includes a GitHub Actions workflow that:
- Runs daily at 10:00 UTC
- Generates and posts content
- Tracks engagement
- Uploads database artifacts
- Provides deployment automation

## Usage

### Local Development

```bash
# Install dependencies
pip install -e .

# Run the agent
python -m src.main scheduler

# Test content generation
python -m src.main test --topic "AI coding agents pricing 2026"

# Run analytics
python -m src.main analytics
```

### GitHub Actions

The workflow is configured to run automatically:
- Daily post generation and publishing
- Engagement tracking
- Analytics reporting
- Database backups

## Content Guidelines

### Voice & Style
- **Audience perception**: Student-builder who ships real projects and shares genuine learnings — not a content creator performing expertise
- **Core interest pillars**: Agentic AI, LLMs, Data Science, Cloud/Kubernetes, Open Source, Quant Finance, Hackathons, Career Growth
- **Voice**: Intellectually curious, grounded, concise — thinks deeply, writes simply
- **Avoid**: Corporate speak, hype language, hollow inspiration, buzzword stuffing, clickbait

### Post Structure
Each post follows this structure:
1. **HOOK (lines 1–2)**: Bold claim, surprising stat, or counterintuitive observation
2. **CONTEXT (2–3 lines)**: What is this? Why does it matter right now?
3. **PERSONAL ANGLE (2–3 lines)**: What did Abhinav learn, build, or realize from this?
4. **TAKEAWAYS (3–5 bullet points)**: Concrete, specific, actionable advice
5. **CLOSING QUESTION (1 line)**: Open-ended, invites genuine discussion

### Formatting Rules
- Length: 150–280 words (strict)
- Paragraphs: max 2–3 lines each; use white space generously
- Emojis: 0–3 total; only where they add clarity, never decoration
- No bold/italic (LinkedIn strips most markdown)
- No unnecessary filler phrases

## Testing

### Unit Tests
- Content generation tests
- Research agent tests
- Image generation tests
- Quality check validation

### Test Commands

```bash
# Run all tests
pytest

# Run content generation tests
pytest tests/test_content_generation.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Deployment

### Local Deployment
```bash
# Start the agent
python -m src.main scheduler
```

### GitHub Actions Deployment
1. Add secrets to your GitHub repository:
   - LINKEDIN_EMAIL
   - LINKEDIN_PASSWORD
   - LINKEDIN_2FA_SECRET (optional)
   - OPENAI_API_KEY or ANTHROPIC_API_KEY or GEMINI_API_KEY or GROQ_API_KEY

2. Enable the workflow in your repository settings

## Analytics & Monitoring

### Dashboard
The analytics module provides:
- **Post Performance**: Engagement metrics for each post
- **Topic Performance**: Which topics perform best
- **Optimal Posting Times**: Data-driven scheduling recommendations
- **Content Insights**: Word count analysis, top-performing hooks
- **Weekly Reports**: Comprehensive analytics summaries

### Metrics Tracked
- Likes, comments, shares, impressions
- Click-through rate (CTR)
- Engagement rate
- Posting frequency and timing
- Topic performance trends

## Development

### Code Quality
- **Linting**: ruff
- **Type Checking**: mypy
- **Testing**: pytest with asyncio support
- **Code Formatting**: black

### Run Quality Checks

```bash
# Lint code
ruff check src/

# Type check
mypy src/

# Format code
black src/

# Run tests with coverage
pytest --cov=src --cov-report=term-missing
```

## Future Enhancements

### Planned Features
1. **Multi-Account Support**: Manage multiple LinkedIn accounts
2. **A/B Testing**: Test different content variations
3. **Social Integration**: Cross-post to Twitter/X
4. **Advanced Analytics**: Sentiment analysis, topic clustering
5. **Content Calendar**: Visual scheduling interface
6. **Template System**: Customizable post templates
7. **API Integration**: REST API for external tools

### Performance Optimizations
1. **Caching**: Cache research results and generated content
2. **Parallel Processing**: Concurrent research and generation
3. **Rate Limiting**: Respect API rate limits
4. **Retry Logic**: Robust error recovery

## License

This project is part of Abhinav Jha's personal automation toolkit for content creation and social media management.

## Support

For issues or questions, please contact Abhinav Jha directly or refer to the documentation.

# linkedin-agent
AI-powered LinkedIn content agent that generates posts, creates images, publishes content, and tracks engagement automatically.
7f4c2b3 (Initial commit)
