import pytest
from aiohttp import web
from patchright.async_api import async_playwright
import bot
import config
from tests.mock_server import create_mock_app
from tests.conftest import get_browser_launch_kwargs

@pytest.mark.asyncio
async def test_full_unit_automation_end_to_end(tmp_path, monkeypatch):
    """Verifies that the bot autonomously completes login, media playback,

    speaking tasks with fake audio, multiple choice, and finishes the unit.
    """
    monkeypatch.setattr(config, "EMAIL", "student@example.com")
    monkeypatch.setattr(config, "PASSWORD", "secret")

    app = create_mock_app()
    runner = web.AppRunner(app)
    await runner.setup()
    port = 8899
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()

    target_url = f"http://127.0.0.1:{port}/gap/ui/self-study"

    try:
        async with async_playwright() as playwright:
            # For headless unit testing, launch isolated test context directly
            launch_kwargs = {
                "user_data_dir": str(tmp_path / "test_profile"),
                "headless": True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--use-fake-ui-for-media-stream",
                    "--use-fake-device-for-media-stream",
                    "--autoplay-policy=no-user-gesture-required",
                ],
                "ignore_default_args": ["--enable-automation"],
                "permissions": ["microphone"],
            }
            chrome_path = bot.find_chrome_executable()
            if chrome_path:
                launch_kwargs["executable_path"] = chrome_path
            else:
                launch_kwargs["channel"] = "chrome"

            context = await playwright.chromium.launch_persistent_context(**launch_kwargs)
            page = context.pages[0] if context.pages else await context.new_page()

            await bot.login_if_needed(page, context, target_url=target_url)

            success = await bot.solve_unit(page, context, max_steps=25)

            assert success is True, "Bot failed to finish unit"

            completed_text = await page.locator(".unit-completed").text_content()
            assert "Unit Complete" in completed_text
            print(f"[TEST PASS] Completed unit with content: {completed_text.strip()}")

            await context.close()
    finally:
        await runner.cleanup()

@pytest.mark.asyncio
async def test_get_current_level_detection():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**get_browser_launch_kwargs())
        page = await browser.new_page()

        # Mock page with Level 9 button
        await page.set_content("""
        <html>
        <body>
            <button data-id="level-view-header-change-level-btn"><span>Level 9</span></button>
        </body>
        </html>
        """)
        level = await bot.get_current_level(page)
        assert level == "Level 9"

        # Mock page with Level 10 heading
        await page.set_content("""
        <html>
        <body>
            <h1>LEVEL 10 - UPPER INTERMEDIATE</h1>
        </body>
        </html>
        """)
        level2 = await bot.get_current_level(page)
        assert "Level 10" in level2

        await browser.close()

@pytest.mark.asyncio
async def test_dashboard_progress_calculation():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**get_browser_launch_kwargs())
        page = await browser.new_page()

        # 4 cards: 2 completed, 2 incomplete
        await page.set_content("""
        <html>
        <body>
            <div data-id="lesson-card-1"><span data-id="lesson-card-1-state-icon"></span></div>
            <div data-id="lesson-card-2"><span data-id="lesson-card-2-state-icon"></span></div>
            <div data-id="lesson-card-3"></div>
            <div data-id="lesson-card-4"><span data-id="lesson-card-4-lock-icon"></span></div>
        </body>
        </html>
        """)
        completed, total = await bot.get_dashboard_progress(page)
        assert total == 4
        assert completed == 2

        await browser.close()

@pytest.mark.asyncio
async def test_empty_credentials_protection(monkeypatch):
    """Verifies that empty credentials in .env prevent sending empty string to inputs."""
    monkeypatch.setattr(config, "EMAIL", "")
    monkeypatch.setattr(config, "PASSWORD", "")

    from unittest.mock import AsyncMock, MagicMock
    mock_page = MagicMock()
    mock_page.url = "https://learn.better.efekta.com/gap/ui/self-study"
    # Wait for url times out quickly
    mock_page.wait_for_url = AsyncMock(side_effect=TimeoutError("manual login timed out"))
    mock_context = MagicMock()

    # Form locator with email input
    email_loc = MagicMock()
    email_loc.count = AsyncMock(return_value=1)
    email_loc.fill = AsyncMock()

    def loc_mock(selector):
        loc = MagicMock()
        if "email" in selector:
            loc.count = AsyncMock(return_value=1)
            loc.first = email_loc
        else:
            loc.count = AsyncMock(return_value=0)
            loc.first = MagicMock(count=AsyncMock(return_value=0))
        return loc

    mock_page.locator = loc_mock

    # Run login_if_needed: must NOT call email_loc.fill("")!
    await bot.login_if_needed(mock_page, mock_context)
    email_loc.fill.assert_not_called()

