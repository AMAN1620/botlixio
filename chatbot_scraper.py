import asyncio
from urllib.parse import urlparse, urljoin
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def crawl_website_for_embeddings(base_url: str, max_pages: int = 20):
    """
    Crawls a website starting from base_url to gather content for embeddings.
    Extracts pure Markdown by removing noisy elements like navs, footers, etc.
    """
    print(f"Starting crawl for {base_url} (Max pages: {max_pages})")
    
    domain = urlparse(base_url).netloc
    extracted_data = {}
    visited_urls = set()
    queue = [base_url]
    
    # 1. Config for high-quality Markdown generation
    # PruningContentFilter helps eliminate boilerplate and short texts
    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(
            threshold=0.48,           # Stricter pruning
            threshold_type="fixed",
            min_word_threshold=15     # Ignore tiny text blocks
        ),
        options={
            "ignore_links": True,     # Usually don't need raw URLs in embeddings
            "citations": False,
            "escape_html": True
        }
    )

    # 2. Browser Config
    browser_config = BrowserConfig(
        headless=True,
        text_mode=True,               # Disable images and media for faster loading
        verbose=False
    )

    # 3. Crawler Run Config
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=md_generator,
        
        # --- Crucial for Embeddings & Clean Content ---
        excluded_tags=["nav", "footer", "header", "aside", "form", "script", "style", "noscript"],
        exclude_external_links=True,
        exclude_social_media_links=True,
        remove_overlay_elements=True, # Remove cookie consent and popups
        
        # --- Multi-page & Interactions ---
        scan_full_page=True,          # Scroll to bottom to load lazy content
        scroll_delay=0.3,             # Delay between scrolls
        magic=True,                   # Auto-handle popups and overlays
        
        # We don't need network idle if we just want the text
        wait_until="domcontentloaded",
        page_timeout=30000
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while queue and len(extracted_data) < max_pages:
            # Batch process URLs (up to 5 concurrently) to avoid overwhelming the server
            batch = []
            while queue and len(batch) < 5 and len(extracted_data) + len(batch) < max_pages:
                url = queue.pop(0)
                if url not in visited_urls:
                    visited_urls.add(url)
                    batch.append(url)
            
            if not batch:
                break
                
            print(f"Crawling batch of {len(batch)} URLs...")
            
            # Execute concurrent crawl for the batch
            results = await crawler.arun_many(urls=batch, config=run_config)
            
            for result in results:
                if result.success and result.markdown:
                    # Successfully extracted markdown
                    clean_markdown = result.markdown
                    extracted_data[result.url] = clean_markdown
                    print(f"✅ Success: {result.url} | Context length: {len(clean_markdown)} chars")
                    
                    # Extract internal links for continued crawling
                    internal_links = result.links.get("internal", [])
                    for link_item in internal_links:
                        href = link_item.get("href", "")
                        if not href:
                            continue
                            
                        # Normalize URL
                        if href.startswith("/"):
                            href = urljoin(base_url, href)
                            
                        # Ensure link is within the same domain and not already queued/visited
                        parsed_href = urlparse(href)
                        if domain in parsed_href.netloc:
                            # Remove fragments to avoid duplicate URLs for same page
                            href_no_fragment = href.split("#")[0]
                            if href_no_fragment not in visited_urls and href_no_fragment not in queue:
                                queue.append(href_no_fragment)
                else:
                    print(f"❌ Failed: {result.url} | Error: {result.error_message}")

    print(f"\nCompleted! Successfully scraped {len(extracted_data)} pages.")
    return extracted_data


async def main():
    # Replace this with the target website you want to scrape for the chatbot POC
    test_url = "https://docs.langchain.com/oss/python/langchain/rag" 
    
    # Run the crawler
    data = await crawl_website_for_embeddings(test_url, max_pages=5)
    print(data)
    # Optional: Save the output to a markdown file for checking
    with open("chatbot_knowledge_base.md", "w") as f:
        for url, content in data.items():
            f.write(f"\n\n# Source: {url}\n\n")
            f.write(content)
            
    print(f"Knowledge base saved to chatbot_knowledge_base.md")

if __name__ == "__main__":
    asyncio.run(main())
