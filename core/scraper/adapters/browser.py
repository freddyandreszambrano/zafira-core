import concurrent.futures


class BrowserFetcher:
    """La sync API de Playwright no puede correr en el hilo principal de Django
    (event loop activo), así que todas las llamadas pasan por un hilo dedicado."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def fetch_rendered(self, url, user_agent, timeout_ms=25000, max_scrolls=25):
        return self._executor.submit(
            self._fetch_rendered_sync, url, user_agent, timeout_ms, max_scrolls
        ).result()

    def close(self):
        try:
            self._executor.submit(self._close_browser).result()
        finally:
            self._executor.shutdown(wait=True)

    def _get_browser(self):
        if self._browser is None:
            from playwright.sync_api import sync_playwright

            if self._playwright is None:
                self._playwright = sync_playwright().start()
            try:
                self._browser = self._playwright.chromium.launch(headless=True)
            except Exception:
                # Si el launch falla hay que detener Playwright: dejarlo a medio
                # iniciar rompe todos los intentos siguientes en este hilo con
                # el error engañoso "Sync API inside the asyncio loop".
                self._playwright.stop()
                self._playwright = None
                raise
        return self._browser

    def _close_browser(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def _fetch_rendered_sync(self, url, user_agent, timeout_ms, max_scrolls):
        browser = self._get_browser()
        page = browser.new_page(user_agent=user_agent)
        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in ("image", "font", "media")
            else route.continue_(),
        )
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(1200)

            previous_count = -1
            stable_rounds = 0
            for _ in range(max_scrolls):
                current_count = page.eval_on_selector_all("a[href]", "elements => elements.length")
                if current_count == previous_count:
                    stable_rounds += 1
                    if stable_rounds >= 2:
                        break
                else:
                    stable_rounds = 0
                previous_count = current_count
                page.mouse.wheel(0, 2500)
                page.wait_for_timeout(500)
            return page.content()
        finally:
            page.close()
