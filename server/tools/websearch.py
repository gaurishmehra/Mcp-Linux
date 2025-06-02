import re
import asyncio
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from urllib.parse import urlparse
import time

async def scrape_web_content(query: str, max_links: int = 7, max_content_length: int = None, use_duckduckgo: bool = True) -> Dict[str, Any]:
    async with async_playwright() as p:
        # Launch browser with stealth settings but NOT headless
        browser = await p.chromium.launch(
            headless=False,  # Keep visible to avoid detection
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-default-apps',
                '--no-first-run',
                '--disable-background-networking',
                '--disable-ipc-flooding-protection',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--force-color-profile=srgb',
                '--metrics-recording-only',
                '--use-mock-keychain',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--mute-audio',
                '--no-default-browser-check',
                '--autoplay-policy=user-gesture-required',
                '--disable-background-mode',
                '--disable-notifications'
            ]
        )
        
        # Create 7 contexts for maximum parallel processing
        contexts = []
        num_contexts = 7  # Full 7 parallel contexts

        for i in range(num_contexts):
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1366, 'height': 768},
                locale='en-US',
                timezone_id='America/New_York',
                ignore_https_errors=True,
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            # Enhanced stealth techniques
            await context.add_init_script("""
                // Override the `plugins` property to use a custom getter.
                Object.defineProperty(navigator, 'plugins', {
                    get: function() {
                        return [1, 2, 3, 4, 5];
                    },
                });

                // Override the `languages` property to use a custom getter.
                Object.defineProperty(navigator, 'languages', {
                    get: function() {
                        return ['en-US', 'en'];
                    },
                });

                // Override the webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Mock chrome object
                window.chrome = {
                    runtime: {},
                };

                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: 'granted' }) :
                        originalQuery(parameters)
                );
            """)
            
            contexts.append(context)
        
        try:
            # Step 1: Fast search using single context
            if use_duckduckgo:
                search_links = await _search_duckduckgo_ultra_fast(contexts[0], query, max_links)
            else:
                search_links = []
            
            # Step 2: Distribute scraping across 7 contexts (1 link per context for maximum speed)
            print(f"Scraping {len(search_links)} websites across {len(contexts)} browser contexts in parallel...")
            scraped_content = await _scrape_7_parallel_contexts(contexts, search_links)

            return {
                'query': query,
                'search_engine': 'DuckDuckGo' if use_duckduckgo else 'Google',
                'total_results': len(scraped_content),
                'results': scraped_content
            }
            
        finally:
            for context in contexts:
                await context.close()
            await browser.close()


async def _search_duckduckgo_ultra_fast(context, query: str, max_links: int) -> List[Dict[str, str]]:
    """Ultra-fast DuckDuckGo search with aggressive optimizations"""
    page = await context.new_page()
    links = []
    
    try:
        print(f"Searching DuckDuckGo for: {query}")
        
        # Block everything except HTML and scripts for fastest loading
        await page.route('**/*', lambda route: route.abort() 
                        if route.request.resource_type in ['image', 'stylesheet', 'font', 'media', 'websocket', 'other'] 
                        else route.continue_())
        
        # Navigate with minimal wait
        await page.goto("https://duckduckgo.com/", wait_until="commit", timeout=8000)
        
        # Lightning-fast search execution
        await page.fill("input[name='q']", query)
        
        # Use keyboard shortcut instead of button click (faster)
        await page.keyboard.press("Enter")
        
        # Wait only for essential content
        await page.wait_for_function(
            "document.querySelectorAll('article[data-testid=\"result\"]').length > 0",
            timeout=8000
        )
        
        # Extract all data in single JavaScript execution (fastest method)
        results = await page.evaluate(f"""
            () => {{
                const articles = Array.from(document.querySelectorAll("article[data-testid='result']")).slice(0, {max_links});
                
                return articles.map(article => {{
                    const linkEl = article.querySelector("h2 a");
                    const snippetEl = article.querySelector("[data-result='snippet']");
                    
                    return linkEl ? {{
                        url: linkEl.href,
                        title: linkEl.innerText.trim(),
                        snippet: snippetEl ? snippetEl.innerText.trim() : ''
                    }} : null;
                }}).filter(Boolean);
            }}
        """)
        
        # Filter valid URLs
        for result in results:
            if result['url'] and _is_valid_url(result['url']):
                links.append(result)
                print(f"Found: {result['title']}")
        
    except Exception as e:
        print(f"Error searching DuckDuckGo: {e}")
    
    finally:
        await page.close()
    
    return links


async def _scrape_7_parallel_contexts(contexts: List, links: List[Dict]) -> List[Dict]:
    """Maximum parallelization: each link gets its own dedicated context"""
    
    async def scrape_single_link_dedicated_context(context, link_data, index):
        """Each link gets a dedicated context for maximum speed"""
        page = await context.new_page()
        
        try:
            print(f"Context {index + 1}: Scraping {link_data['url']}")
            result = await _scrape_page_unlimited_content(page, link_data, index)
            return result
        except Exception as e:
            print(f"Context {index + 1} error: {e}")
            return {}
        finally:
            await page.close()

    # Create tasks - each link gets its own context (up to 7)
    tasks = []
    for i, link in enumerate(links[:7]):  # Limit to 7 for perfect 1:1 mapping
        context = contexts[i % len(contexts)]
        tasks.append(scrape_single_link_dedicated_context(context, link, i))
    
    # Execute all 7 scraping operations simultaneously
    print(f"Launching {len(tasks)} parallel scraping operations...")
    start_time = time.time()
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    print(f"Completed all scraping in {end_time - start_time:.2f} seconds")
    
    # Filter successful results
    scraped_content = []
    for i, result in enumerate(results):
        if isinstance(result, dict) and result.get('content'):
            scraped_content.append(result)
            print(f"Context {i + 1}: Successfully scraped {len(result['content'])} characters")
        elif isinstance(result, Exception):
            print(f"Context {i + 1}: Failed with error: {result}")
    
    return scraped_content


async def _scrape_page_unlimited_content(page, link_data: Dict, context_index: int) -> Dict:
    """Lightning-fast page scraping with UNLIMITED content length"""
    
    try:
        # Aggressive resource blocking - only allow essential resources
        await page.route('**/*', lambda route: (
            route.abort() if route.request.resource_type in [
                'image', 'stylesheet', 'font', 'media', 'websocket', 'other',
                'manifest', 'texttrack', 'eventsource'
            ] else route.continue_()
        ))
        
        # Set aggressive timeouts
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(15000)
        
        # Navigate with minimal wait - don't wait for full load
        await page.goto(link_data['url'], wait_until="commit", timeout=15000)
        
        # Wait only for document ready, not full load
        await page.wait_for_load_state("domcontentloaded", timeout=12000)
        
        # Extract ALL content without length limits
        content = await page.evaluate("""
            () => {
                // Immediate DOM cleanup and content extraction
                const unwantedSelectors = [
                    'script', 'style', 'nav', 'header', 'footer', 'aside',
                    '.nav', '.menu', '.sidebar', '.advertisement', '.ad', 
                    '.popup', '.modal', '.cookie', '.gdpr', '.newsletter',
                    '.social', '.share', '.comment', '.related', '.sidebar',
                    '.ads', '.banner', '.promotion', '.widget'
                ];
                
                // Remove unwanted elements in batches for speed
                unwantedSelectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => el.remove());
                });
                
                // Priority content selectors (most likely to least likely)
                const contentSelectors = [
                    'main article', 'article', 'main', '[role="main"]',
                    '.post-content', '.entry-content', '.article-content',
                    '.content', '.main-content', '.story-body', '#content',
                    '.post', '.entry', '.article', '.text-content',
                    '.article-body', '.post-body', '.content-body'
                ];
                
                let allContent = '';
                let foundMainContent = false;
                
                // Try to find the main content area first
                for (const selector of contentSelectors) {
                    const element = document.querySelector(selector);
                    if (element) {
                        const text = element.innerText || element.textContent || '';
                        if (text.length > 500) { // Substantial content
                            allContent = text;
                            foundMainContent = true;
                            break;
                        }
                    }
                }
                
                // If no main content found, get everything from body
                if (!foundMainContent) {
                    const body = document.body;
                    if (body) {
                        allContent = body.innerText || body.textContent || '';
                    }
                }
                
                // Also try to get content from multiple content sections and combine
                if (!foundMainContent || allContent.length < 1000) {
                    const contentElements = document.querySelectorAll(
                        'p, div.content, div.text, div.article, div.post, section, .paragraph'
                    );
                    
                    const additionalContent = Array.from(contentElements)
                        .map(el => el.innerText || el.textContent || '')
                        .filter(text => text.length > 50)
                        .join('\\n\\n');
                    
                    if (additionalContent.length > allContent.length) {
                        allContent = additionalContent;
                    }
                }
                
                return allContent;
            }
        """)
        
        # Clean text but keep ALL content
        content = _clean_text_unlimited(content)
        
        if len(content) < 100:  # Skip pages with too little content
            print(f"Context {context_index + 1}: Content too short ({len(content)} chars), skipping")
            return {}
        
        print(f"Context {context_index + 1}: Extracted {len(content)} characters from {link_data['url']}")
        
        return {
            'url': link_data['url'],
            'title': link_data['title'],
            'search_snippet': link_data.get('snippet', ''),
            'content': content,
            'content_length': len(content)
        }
        
    except Exception as e:
        print(f"Context {context_index + 1}: Error scraping {link_data['url']}: {e}")
        return {}


def _is_valid_url(url: str) -> bool:
    """Ultra-fast URL validation"""
    if not url or len(url) < 10:
        return False
    
    # Quick string checks before parsing
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    # Quick domain blacklist check
    if any(blocked in url.lower() for blocked in ['linkedin.com', 'facebook.com/tr']):
        return False
    
    return True


def _clean_text_unlimited(text: str) -> str:
    """Ultra-fast text cleaning that preserves ALL content"""
    if not text:
        return ""
    
    # Preserve all content, just clean up formatting
    # Replace multiple whitespace with single space but keep paragraph breaks
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        cleaned_line = ' '.join(line.split())  # Remove extra spaces within line
        if cleaned_line.strip():  # Only keep non-empty lines
            cleaned_lines.append(cleaned_line)
    
    # Join with double newlines to preserve paragraph structure
    text = '\n\n'.join(cleaned_lines)
    
    # Remove only the most obvious unwanted patterns (minimal cleaning)
    quick_removes = [
        'Click here to', 'Subscribe to', 'Sign up for', 'Follow us on',
        'Share this article', 'Related articles', 'You may also like'
    ]
    
    for phrase in quick_removes:
        if phrase in text:
            text = text.replace(phrase, '')
    
    return text.strip()



websearch_description = "Search the web for a given query and return the content of the top results with unlimited content length. "