import asyncio
import os
import random
from datetime import datetime
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import structlog
import base64
import json

from config.settings import settings

logger = structlog.get_logger()


class LinkedInPoster:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=settings.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self.context.new_page()
        await self._add_stealth_scripts()

    async def _add_stealth_scripts(self):
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)

    async def close(self):
        if self.browser:
            await self.browser.close()

    async def login(self) -> bool:
        try:
            logger.info("Navigating to LinkedIn login")
            await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

            print(f"Current URL: {self.page.url}")

            await self.page.screenshot(path="linkedin_login.png")

            await self.page.wait_for_selector(
    "#username, input[name='session_key'], input[type='email']",
    timeout=60000
)

            if await self.page.locator("#username").count() > 0:
             await self.page.fill("#username", settings.linkedin_email)
            elif await self.page.locator("input[name='session_key']").count() > 0:
             await self.page.fill("input[name='session_key']", settings.linkedin_email)
            else:
             await self.page.fill("input[type='email']", settings.linkedin_email)
            await self._random_delay(0.5, 1.5)
            await self.page.fill("#password", settings.linkedin_password)
            await self._random_delay(0.5, 1.5)
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state("networkidle", timeout=settings.browser_timeout)
            await self._random_delay(3, 5)

            if await self._check_2fa():
                await self._handle_2fa()

            if "feed" in self.page.url or "linkedin.com" in self.page.url:
                logger.info("Login successful")
                return True
            
            logger.error("Login failed - unexpected URL", url=self.page.url)
            return False

        except Exception as e:
            logger.error("Login error", error=str(e))
            return False

    async def _check_2fa(self) -> bool:
        try:
            await self.page.wait_for_selector("#input__phone_verification_pin", timeout=5000)
            return True
        except Exception:
            return False

    async def _handle_2fa(self):
        if not settings.linkedin_2fa_secret:
            logger.warning("2FA required but no secret configured")
            return
        
        import pyotp
        totp = pyotp.TOTP(settings.linkedin_2fa_secret)
        code = totp.now()
        
        await self.page.fill("#input__phone_verification_pin", code)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle", timeout=settings.browser_timeout)
        await self._random_delay(3, 5)

    async def create_post(self, content: str, image_data: Optional[bytes] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            logger.info("Creating new post", has_image=image_data is not None)
            await self.page.goto("https://www.linkedin.com/feed/", wait_until="networkidle")
            await self._random_delay(2, 4)

            start_post_btn = await self._find_start_post_button()
            if not start_post_btn:
                logger.error("Could not find 'Start a post' button")
                return False, None, None

            await start_post_btn.click()
            await self._random_delay(1, 2)

            editor = await self._find_post_editor()
            if not editor:
                logger.error("Could not find post editor")
                return False, None, None

            await self._type_human_like(editor, content)
            await self._random_delay(1, 2)

            if image_data:
                await self._upload_image()
                await self._random_delay(1, 2)

            post_btn = await self._find_post_submit_button()
            if not post_btn:
                logger.error("Could not find 'Post' button")
                return False, None, None

            await post_btn.click()
            await self.page.wait_for_load_state("networkidle", timeout=settings.browser_timeout)
            await self._random_delay(3, 5)

            post_id, post_url = await self._extract_post_info()
            logger.info("Post published", post_id=post_id, url=post_url)
            return True, post_id, post_url

        except Exception as e:
            logger.error("Post creation error", error=str(e))
            return False, None, None

    async def _upload_image(self):
        try:
            await self.page.wait_for_selector('input[type="file"]', timeout=10000)
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files({"name": "image.png", "mimeType": "image/png"})
                await self._random_delay(2, 3)
                logger.info("Image uploaded")
        except Exception as e:
            logger.warning("Image upload failed, continuing without image", error=str(e))

    async def _find_start_post_button(self):
        selectors = [
            'button:has-text("Start a post")',
            '[data-control-name="share.post"]',
            'button[aria-label="Start a post"]',
            '.share-box-feed-entry__trigger',
        ]
        for sel in selectors:
            try:
                btn = await self.page.wait_for_selector(sel, timeout=5000)
                if btn:
                    return btn
            except Exception:
                continue
        return None

    async def _find_post_editor(self):
        selectors = [
            '[data-placeholder="What do you want to talk about?"]',
            '.ql-editor',
            '[contenteditable="true"]',
            'div[role="textbox"]',
        ]
        for sel in selectors:
            try:
                editor = await self.page.wait_for_selector(sel, timeout=5000)
                if editor:
                    return editor
            except Exception:
                continue
        return None

    async def _find_post_submit_button(self):
        selectors = [
            'button:has-text("Post")',
            'button[data-control-name="post.submit"]',
            'button[type="submit"]',
            '.share-actions__primary-action',
        ]
        for sel in selectors:
            try:
                btn = await self.page.wait_for_selector(sel, timeout=5000)
                if btn and await btn.is_enabled():
                    return btn
            except Exception:
                continue
        return None

    async def _type_human_like(self, element, text: str):
        await element.click()
        await self._random_delay(0.2, 0.5)
        
        for char in text:
            await element.type(char, delay=random.randint(30, 120))
            if char in ".!?":
                await self._random_delay(0.1, 0.3)

    async def _extract_post_info(self) -> Tuple[Optional[str], Optional[str]]:
        try:
            await self.page.wait_for_selector('[data-urn*="activity"]', timeout=10000)
            post_element = await self.page.query_selector('[data-urn*="activity"]')
            if post_element:
                urn = await post_element.get_attribute("data-urn")
                post_id = urn.split(":")[-1] if urn else None
                post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else None
                return post_id, post_url
        except Exception:
            pass
        return None, None

    async def _random_delay(self, min_sec: float, max_sec: float):
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def fetch_engagement(self, post_url: str) -> dict:
        try:
            await self.page.goto(post_url, wait_until="networkidle")
            await self._random_delay(2, 3)

            metrics = {}
            selectors = {
                "likes": '[data-test-id="social-counts-reactions-count"]',
                "comments": '[data-test-id="social-counts-comments-count"]',
                "shares": '[data-test-id="social-counts-shares-count"]',
            }

            for key, sel in selectors.items():
                try:
                    el = await self.page.wait_for_selector(sel, timeout=5000)
                    text = await el.inner_text()
                    metrics[key] = self._parse_count(text)
                except Exception:
                    metrics[key] = 0

            return metrics
        except Exception as e:
            logger.error("Engagement fetch error", error=str(e))
            return {"likes": 0, "comments": 0, "shares": 0}

    def _parse_count(self, text: str) -> int:
        text = text.strip().lower().replace(",", "")
        if "k" in text:
            return int(float(text.replace("k", "")) * 1000)
        if "m" in text:
            return int(float(text.replace("m", "")) * 1000000)
        try:
            return int(text)
        except ValueError:
            return 0