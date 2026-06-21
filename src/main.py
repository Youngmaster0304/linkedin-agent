import asyncio
import sys
import argparse
import structlog
from contextlib import asynccontextmanager

from config.settings import settings
from src.scheduler.scheduler import AgentScheduler
from src.analytics.analytics import get_dashboard_data
from src.content.research import ResearchAgent
from src.content.writer import ContentWriter

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def run_scheduler():
    scheduler = AgentScheduler()
    try:
        await scheduler.start()
        logger.info("Scheduler running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    finally:
        await scheduler.shutdown()


async def run_once():
    scheduler = AgentScheduler()
    try:
        await scheduler.start()
        await scheduler.run_once()
        logger.info("Single run completed")
    finally:
        await scheduler.shutdown()


async def generate_test_post(topic: str):
    research_agent = ResearchAgent()
    writer = ContentWriter()
    
    try:
        research = await research_agent.research_topic(topic)
        post = writer.generate_post(research)
        
        print("\n" + "="*60)
        print(f"TOPIC: {post.topic}")
        print(f"WORD COUNT: {post.word_count}")
        print(f"QUALITY: {'PASS' if post.quality_checks.get('all_passed') else 'FAIL'}")
        print("="*60)
        print(post.full_content)
        print("="*60)
        print(f"\nIMAGE IDEA: {post.image_idea}")
        print(f"\nQUALITY CHECKS: {post.quality_checks}")
    finally:
        await research_agent.close()


async def show_analytics():
    data = await get_dashboard_data()
    import json
    print(json.dumps(data, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Content Automation Agent")
    parser.add_argument("command", choices=["scheduler", "once", "test", "analytics"], 
                       help="Command to run")
    parser.add_argument("--topic", type=str, help="Topic for test post generation")
    
    args = parser.parse_args()
    
    if args.command == "scheduler":
        asyncio.run(run_scheduler())
    elif args.command == "once":
        asyncio.run(run_once())
    elif args.command == "test":
        if not args.topic:
            print("Error: --topic required for test command")
            sys.exit(1)
        asyncio.run(generate_test_post(args.topic))
    elif args.command == "analytics":
        asyncio.run(show_analytics())


if __name__ == "__main__":
    main()