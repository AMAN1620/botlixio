"""Web crawler using Crawl4AI — scrapes URLs and returns clean markdown + page metadata."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@dataclass
class CrawledPage:
    url: str
    title: str
    char_count: int


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


def _extract_title(markdown: str, fallback_url: str) -> str:
    """Extract the first H1/H2 heading from markdown as the page title."""
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
        if line.startswith("## "):
            return line[3:].strip()
    # Fall back to last path segment of the URL
    path = urlparse(fallback_url).path.rstrip("/")
    last_segment = path.split("/")[-1] if path else fallback_url
    return last_segment.replace("-", " ").replace("_", " ").title() or fallback_url


def _matches_path_filter(url: str, path_filter: str | None) -> bool:
    """Return True if the URL's path starts with path_filter (or no filter set)."""
    if not path_filter:
        return True
    return urlparse(url).path.startswith(path_filter)


async def crawl_url(
    url: str,
    max_pages: int = 10,
    path_filter: str | None = None,
) -> tuple[str, list[CrawledPage]]:
    """
    Crawl a URL and follow internal links up to max_pages.

    Args:
        url:         Root URL to start crawling from.
        max_pages:   Maximum number of pages to crawl (1–20).
        path_filter: Optional URL path prefix — only follow links under this path.
                     e.g. "/docs" will skip /blog, /pricing, etc.

    Returns:
        (combined_markdown, crawled_pages) where crawled_pages is a list of
        CrawledPage(url, title, char_count) for each successfully scraped page.

    Raises:
        ValueError: if no content could be extracted.
    """
    domain = urlparse(url).netloc
    extracted: dict[str, str] = {}   # url → markdown
    visited: set[str] = set()
    queue: list[str] = [url]

    browser_config, run_config = _build_configs()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while queue and len(extracted) < max_pages:
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
                if not (result.success and result.markdown):
                    continue

                extracted[result.url] = result.markdown

                # Follow internal links — respect path_filter
                for link_item in result.links.get("internal", []):
                    href = link_item.get("href", "")
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = urljoin(url, href)
                    parsed = urlparse(href)
                    if domain not in parsed.netloc:
                        continue
                    href_clean = href.split("#")[0]
                    if href_clean in visited or href_clean in queue:
                        continue
                    if not _matches_path_filter(href_clean, path_filter):
                        continue
                    queue.append(href_clean)

    if not extracted:
        raise ValueError(f"Failed to extract any content from {url}")

    # Build page metadata list
    pages: list[CrawledPage] = []
    parts: list[str] = []

    for page_url, content in extracted.items():
        title = _extract_title(content, page_url)
        pages.append(CrawledPage(url=page_url, title=title, char_count=len(content)))
        parts.append(f"## Source: {page_url}\n\n{content}")

    combined = _clean_text("\n\n---\n\n".join(parts))
    return combined, pages


def _clean_text(text: str) -> str:
    """Collapse excessive blank lines."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
