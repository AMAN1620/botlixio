"""Web crawler using Crawl4AI — scrapes URLs and returns clean text.

Uses the same config proven in the POC (chatbot_scraper.py):
- PruningContentFilter to eliminate boilerplate
- BrowserConfig with text_mode for faster loading
- Multi-page crawl following internal links up to max_pages
"""

import re
from urllib.parse import urlparse, urljoin

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter


def _build_configs() -> tuple[BrowserConfig, CrawlerRunConfig]:
    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(
            threshold=0.48,
            threshold_type="fixed",
            min_word_threshold=15,
        ),
        options={
            "ignore_links": True,
            "citations": False,
            "escape_html": True,
        },
    )

    browser_config = BrowserConfig(
        headless=True,
        text_mode=True,
        verbose=False,
    )

    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=md_generator,
        excluded_tags=["nav", "footer", "header", "aside", "form", "script", "style", "noscript"],
        exclude_external_links=True,
        exclude_social_media_links=True,
        remove_overlay_elements=True,
        scan_full_page=True,
        scroll_delay=0.3,
        magic=True,
        wait_until="domcontentloaded",
        page_timeout=30000,
    )

    return browser_config, run_config


async def crawl_url(url: str, max_pages: int = 5) -> str:
    """
    Crawl a URL (and follow internal links up to max_pages).
    Returns concatenated clean markdown text.
    Raises ValueError if nothing could be extracted.
    """
    domain = urlparse(url).netloc
    extracted: dict[str, str] = {}
    visited: set[str] = set()
    queue: list[str] = [url]

    browser_config, run_config = _build_configs()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while queue and len(extracted) < max_pages:
            # Batch up to 5 concurrent requests
            batch: list[str] = []
            while queue and len(batch) < 5 and len(extracted) + len(batch) < max_pages:
                next_url = queue.pop(0)
                if next_url not in visited:
                    visited.add(next_url)
                    batch.append(next_url)

            if not batch:
                break

            results = await crawler.arun_many(urls=batch, config=run_config)

            for result in results:
                if result.success and result.markdown:
                    extracted[result.url] = result.markdown

                    # Follow internal links
                    for link_item in result.links.get("internal", []):
                        href = link_item.get("href", "")
                        if not href:
                            continue
                        if href.startswith("/"):
                            href = urljoin(url, href)
                        parsed = urlparse(href)
                        if domain in parsed.netloc:
                            href_clean = href.split("#")[0]
                            if href_clean not in visited and href_clean not in queue:
                                queue.append(href_clean)

    if not extracted:
        raise ValueError(f"Failed to extract any content from {url}")

    # Concatenate all pages with source headers
    parts = []
    for page_url, content in extracted.items():
        parts.append(f"## Source: {page_url}\n\n{content}")

    combined = "\n\n---\n\n".join(parts)
    return _clean_text(combined)


def _clean_text(text: str) -> str:
    """Collapse excessive blank lines."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
