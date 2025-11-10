# Lewz Knowledge Base Crawler Guide

> **Overview**: This guide explains how to use Crawl4AI's specialized Lewz crawler to extract Baidu Netdisk share links and article metadata from https://www.lewz.cn/jprj for integration with WordPress knowledge base services.

## 1. Introduction

The Lewz Knowledge Base Crawler is a domain-specific crawler designed to:

- **Extract structured data** from Chinese knowledge-sharing platforms
- **Discover Baidu Netdisk links** with automatic password extraction
- **Parse article metadata** including titles and SEO tags
- **Integrate seamlessly** with WordPress knowledge base pipelines

**Use Cases:**

- Building knowledge base repositories from lewz.cn articles
- Automated content aggregation for resource libraries
- Batch extraction of educational materials with share links
- Content migration to WordPress or custom CMS platforms

---

## 2. Prerequisites

### 2.1 Environment Setup

Before using the Lewz crawler, ensure your environment is properly configured:

```bash
# Install Crawl4AI with all dependencies
pip install -U crawl4ai

# Run post-installation setup (installs Playwright browsers)
crawl4ai-setup

# Verify installation
crawl4ai-doctor
```

### 2.2 Manual Playwright Browser Installation

If you encounter browser-related issues:

```bash
# Install Chromium with system dependencies
python -m playwright install --with-deps chromium
```

### 2.3 Python Version Requirements

- **Python 3.10+** is required
- Async/await support is essential for the crawler

---

## 3. Usage Methods

The Lewz crawler can be used in three ways: via CLI, programmatically with CrawlerHub, or through direct import.

### 3.1 Command-Line Interface (Recommended for Quick Tasks)

The CLI provides the fastest way to extract articles:

#### Basic Single Article Extraction

```bash
python -m crawl4ai.scripts.lewz_knowledge_pipeline \
    --url "https://www.lewz.cn/jprj/12345.html" \
    --limit 1
```

#### Crawl Listing Page (Multiple Articles)

```bash
python -m crawl4ai.scripts.lewz_knowledge_pipeline \
    --url "https://www.lewz.cn/jprj" \
    --limit 10 \
    --output results.json
```

#### CLI Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--url` | string | *required* | Starting URL (listing page or article) |
| `--limit` | int | `10` | Maximum number of articles to process |
| `--output` | string | `stdout` | Path to save JSON output file |

#### Example Output

```json
[
  {
    "source_url": "https://www.lewz.cn/jprj/12345.html",
    "title": "Python高级编程教程",
    "seo_tags": ["Python", "编程", "教程", "高级"],
    "share_links": [
      {
        "url": "https://pan.baidu.com/s/1a2b3c4d5e6f7g8h9i0j",
        "password": "abcd"
      }
    ]
  }
]
```

### 3.2 CrawlerHub Integration (Recommended for Production)

The CrawlerHub automatically discovers the Lewz crawler without configuration:

```python
import asyncio
import json
from crawl4ai import CrawlerHub

async def crawl_lewz_articles():
    # Get the crawler from the hub
    crawler_cls = CrawlerHub.get("lewz_baidu")
    crawler = crawler_cls()
    
    # Crawl listing page
    result_json = await crawler.run(
        url="https://www.lewz.cn/jprj",
        article_limit=5
    )
    
    # Parse results
    articles = json.loads(result_json)
    
    # Process each article
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"URL: {article['source_url']}")
        print(f"Tags: {', '.join(article['seo_tags'])}")
        
        for link in article['share_links']:
            print(f"  Share Link: {link['url']}")
            if link['password']:
                print(f"  Password: {link['password']}")
        print("-" * 60)

# Run the crawler
asyncio.run(crawl_lewz_articles())
```

### 3.3 Direct Import (For Custom Workflows)

For maximum control, import the crawler class directly:

```python
import asyncio
import json
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler

async def main():
    # Create crawler instance
    crawler = LewzKnowledgeCrawler()
    
    # Display crawler metadata
    print(f"Crawler Version: {crawler.__meta__['version']}")
    print(f"Tested on: {', '.join(crawler.__meta__['tested_on'])}")
    
    # Process a single article
    result_json = await crawler.run(
        url="https://www.lewz.cn/jprj/12345.html",
        article_limit=1
    )
    
    results = json.loads(result_json)
    print(json.dumps(results, indent=2, ensure_ascii=False))

asyncio.run(main())
```

---

## 4. Output Schema

The crawler returns structured JSON data optimized for knowledge base integration.

### 4.1 Schema Structure

```json
[
  {
    "source_url": "string",
    "title": "string",
    "seo_tags": ["string"],
    "share_links": [
      {
        "url": "string",
        "password": "string | null"
      }
    ]
  }
]
```

### 4.2 Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `source_url` | string | The original article URL from lewz.cn |
| `title` | string | Article title (extracted from `<title>`, `<h1>`, or meta tags) |
| `seo_tags` | array[string] | SEO keywords and tags from meta tags and content |
| `share_links` | array[object] | List of Baidu Netdisk share links |
| `share_links[].url` | string | Baidu Netdisk share URL |
| `share_links[].password` | string \| null | Extraction code/password (null if not found) |

### 4.3 Real-World Example

Here's a complete example showing a typical article extraction:

```json
[
  {
    "source_url": "https://www.lewz.cn/jprj/2024-python-tutorial.html",
    "title": "2024年Python完整学习路线图",
    "seo_tags": [
      "Python",
      "编程教程",
      "学习路线",
      "开发",
      "编程语言"
    ],
    "share_links": [
      {
        "url": "https://pan.baidu.com/s/1xYz2aB3cD4eF5gH6iJ7kL8",
        "password": "py24"
      },
      {
        "url": "https://pan.baidu.com/s/9mN8oP7qR6sT5uV4wX3yZ2",
        "password": "code"
      }
    ]
  }
]
```

---

## 5. Password Extraction Patterns

The crawler intelligently recognizes various Chinese and English password formats.

### 5.1 Supported Patterns

| Pattern Type | Example | Regex Supported |
|-------------|---------|-----------------|
| Chinese colon | `提取码：abcd` | ✅ |
| Chinese colon (English) | `提取码: xyz9` | ✅ |
| Space separator | `提取码 test123` | ✅ |
| Password keyword | `密码：pass1234` | ✅ |
| Latin abbreviation | `pwd: testpwd` | ✅ |
| Full English word | `password: secret` | ✅ |
| URL parameter | `?pwd=abcd` | ✅ |

### 5.2 Password Search Strategy

The crawler uses a multi-step approach:

1. **URL Parameters**: Checks for `?pwd=xxxx` in the link URL
2. **Parent Element**: Examines the text of the link's parent element
3. **Sibling Elements**: Scans up to 3 sibling elements
4. **Pattern Matching**: Applies regex patterns for various formats
5. **Validation**: Ensures passwords are at least 4 characters long

### 5.3 Handling Missing Passwords

When a password cannot be found:

```json
{
  "url": "https://pan.baidu.com/s/1234567890abcdef",
  "password": null
}
```

This allows downstream systems to flag articles requiring manual password entry.

---

## 6. Integration with WordPress Knowledge Base

The crawler output is designed for seamless WordPress integration.

### 6.1 WordPress Custom Post Type Structure

Map the crawler output to WordPress custom fields:

```php
// Example WordPress integration
$article_data = json_decode($crawler_output, true);

foreach ($article_data as $article) {
    $post_id = wp_insert_post([
        'post_title'   => $article['title'],
        'post_content' => '', // Fetch full content separately if needed
        'post_status'  => 'publish',
        'post_type'    => 'knowledge_base',
        'meta_input'   => [
            'source_url'   => $article['source_url'],
            'seo_tags'     => implode(',', $article['seo_tags']),
            'share_links'  => json_encode($article['share_links'])
        ]
    ]);
    
    // Add tags as taxonomy terms
    wp_set_post_terms($post_id, $article['seo_tags'], 'kb_tags');
}
```

### 6.2 REST API Integration

For headless WordPress setups:

```python
import asyncio
import json
import httpx
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler

async def sync_to_wordpress(wp_api_url: str, wp_token: str):
    crawler = LewzKnowledgeCrawler()
    result_json = await crawler.run(
        url="https://www.lewz.cn/jprj",
        article_limit=20
    )
    
    articles = json.loads(result_json)
    
    async with httpx.AsyncClient() as client:
        for article in articles:
            response = await client.post(
                f"{wp_api_url}/wp-json/wp/v2/knowledge_base",
                headers={
                    "Authorization": f"Bearer {wp_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "title": article['title'],
                    "meta": {
                        "source_url": article['source_url'],
                        "share_links": article['share_links']
                    },
                    "tags": article['seo_tags']
                }
            )
            print(f"Created post ID: {response.json()['id']}")

# asyncio.run(sync_to_wordpress("https://your-wp-site.com", "your-token"))
```

### 6.3 Database Schema Example

For custom implementations:

```sql
CREATE TABLE lewz_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_url VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    seo_tags JSON,
    share_links JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source_url (source_url)
);
```

---

## 7. Best Practices

### 7.1 Rate Limiting

To avoid being blocked by the target website:

```python
import asyncio
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler

async def rate_limited_crawl():
    crawler = LewzKnowledgeCrawler()
    
    articles_urls = [
        "https://www.lewz.cn/jprj/12345.html",
        "https://www.lewz.cn/jprj/12346.html",
        "https://www.lewz.cn/jprj/12347.html",
    ]
    
    results = []
    for url in articles_urls:
        result_json = await crawler.run(url=url, article_limit=1)
        results.extend(json.loads(result_json))
        
        # Add 2-3 second delay between requests
        await asyncio.sleep(2)
    
    return results
```

**Recommended Rate Limits:**

- **20 requests per minute** for lewz.cn
- **2-3 second delay** between consecutive requests
- **Use exponential backoff** on rate limit errors (429/503)

### 7.2 Pagination and Limits

When crawling listing pages:

```python
async def crawl_in_batches():
    crawler = LewzKnowledgeCrawler()
    batch_size = 10
    total_articles = 50
    
    all_articles = []
    
    # Process in smaller batches
    for offset in range(0, total_articles, batch_size):
        result_json = await crawler.run(
            url="https://www.lewz.cn/jprj",
            article_limit=batch_size
        )
        batch = json.loads(result_json)
        all_articles.extend(batch)
        
        print(f"Processed {len(all_articles)}/{total_articles} articles")
        await asyncio.sleep(5)  # Longer delay between batches
    
    return all_articles
```

### 7.3 Error Handling

Implement robust error handling:

```python
import asyncio
import json
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler

async def safe_crawl(url: str, max_retries: int = 3):
    crawler = LewzKnowledgeCrawler()
    
    for attempt in range(max_retries):
        try:
            result_json = await crawler.run(url=url, article_limit=10)
            result = json.loads(result_json)
            
            # Check for error response
            if isinstance(result, dict) and "error" in result:
                print(f"Crawler error: {result['error']}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return []
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return []
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                return []
    
    return []
```

### 7.4 Caching Strategy

Leverage Crawl4AI's built-in caching:

```python
from crawl4ai import CacheMode
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler

async def crawl_with_cache():
    crawler = LewzKnowledgeCrawler()
    
    # First run: crawl and cache
    result_json = await crawler.run(
        url="https://www.lewz.cn/jprj",
        article_limit=10,
        # Caching is handled internally by AsyncWebCrawler
    )
    
    # Subsequent runs will use cached data if available
    # reducing server load and improving speed
```

### 7.5 Monitoring and Logging

Track crawler performance:

```python
import asyncio
import json
import logging
from datetime import datetime
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def monitored_crawl(url: str):
    crawler = LewzKnowledgeCrawler()
    start_time = datetime.now()
    
    logging.info(f"Starting crawl of {url}")
    
    try:
        result_json = await crawler.run(url=url, article_limit=10)
        articles = json.loads(result_json)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logging.info(f"Crawl completed in {duration:.2f}s")
        logging.info(f"Extracted {len(articles)} articles")
        logging.info(f"Total share links: {sum(len(a['share_links']) for a in articles)}")
        
        return articles
        
    except Exception as e:
        logging.error(f"Crawl failed: {e}", exc_info=True)
        return []
```

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Browser Not Found

**Error:** `Playwright browser not installed`

**Solution:**
```bash
python -m playwright install --with-deps chromium
```

#### Rate Limiting (429 Error)

**Error:** `HTTP 429 Too Many Requests`

**Solution:**
```python
# Increase delay between requests
await asyncio.sleep(5)  # 5 second delay
```

#### Empty Results

**Error:** Returns `[]` or no share links

**Solution:**
- Verify the URL is correct
- Check if the website structure has changed
- Ensure JavaScript is enabled (default in crawler)

#### JSON Parsing Error

**Error:** `json.JSONDecodeError`

**Solution:**
```python
try:
    result = json.loads(result_json)
except json.JSONDecodeError:
    print(f"Raw output: {result_json}")
    # Handle error appropriately
```

### 8.2 Debugging Tips

Enable verbose output:

```python
import sys
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler

async def debug_crawl():
    crawler = LewzKnowledgeCrawler()
    
    # The crawler prints progress to stdout
    result_json = await crawler.run(
        url="https://www.lewz.cn/jprj/12345.html",
        article_limit=1
    )
    
    # Print raw result for inspection
    print("Raw crawler output:", result_json, file=sys.stderr)
```

---

## 9. Advanced Configuration

### 9.1 Custom Crawler Configuration

While the Lewz crawler uses sensible defaults, you can customize the underlying `AsyncWebCrawler`:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.crawlers.lewz_baidu.crawler import LewzKnowledgeCrawler

# Note: The current implementation uses internal AsyncWebCrawler
# For custom configs, you may need to modify the crawler class
# or create a wrapper
```

### 9.2 Extending the Crawler

To add custom functionality:

```python
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler, ArticleData
import json

class CustomLewzCrawler(LewzKnowledgeCrawler):
    async def run(self, url: str, article_limit: int = 10) -> str:
        # Call parent method
        result_json = await super().run(url, article_limit)
        articles = json.loads(result_json)
        
        # Add custom processing
        for article in articles:
            article['custom_field'] = self.custom_processing(article)
        
        return json.dumps(articles, ensure_ascii=False)
    
    def custom_processing(self, article: dict) -> str:
        # Your custom logic here
        return f"Processed: {article['title']}"
```

---

## 10. Reference Links

- **Source Code**: [crawl4ai/crawlers/lewz_baidu/](https://github.com/unclecode/crawl4ai/tree/main/crawl4ai/crawlers/lewz_baidu)
- **CLI Script**: [crawl4ai/scripts/lewz_knowledge_pipeline.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/scripts/lewz_knowledge_pipeline.py)
- **Test Suite**: [tests/pipelines/test_lewz_crawler.py](https://github.com/unclecode/crawl4ai/tree/main/tests/pipelines)
- **Implementation Notes**: [LEWZ_CRAWLER_IMPLEMENTATION.md](https://github.com/unclecode/crawl4ai/blob/main/LEWZ_CRAWLER_IMPLEMENTATION.md)
- **Crawl4AI Documentation**: [https://docs.crawl4ai.com](https://docs.crawl4ai.com)

---

## 11. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial release with full feature set |

---

## Need Help?

If you encounter issues or have questions:

1. **Check the troubleshooting section** above
2. **Review the test fixtures** in `tests/fixtures/lewz/` for examples
3. **File an issue** on the [GitHub repository](https://github.com/unclecode/crawl4ai/issues)
4. **Join the community** on [Discord](https://discord.gg/jP8KfhDhyN)

Happy crawling! 🚀
