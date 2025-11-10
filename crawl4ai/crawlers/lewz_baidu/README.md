# Lewz Knowledge Base Crawler

A specialized crawler for extracting Baidu Netdisk links and article metadata from https://www.lewz.cn/jprj.

## Features

- **Article Discovery**: Automatically collects article URLs from listing pages
- **Metadata Extraction**: Extracts titles, SEO tags, and keywords from articles
- **Baidu Link Detection**: Finds Baidu Netdisk share links in various formats
- **Password Extraction**: Automatically extracts share passwords from text with support for:
  - Chinese patterns: `提取码：xxxx`, `密码：xxxx`
  - English patterns: `pwd: xxxx`, `password: xxxx`
  - Various separator formats (colon, space)
- **Flexible Input**: Supports both listing pages and direct article URLs

## Usage

### As a Crawler Hub Plugin

```python
from crawl4ai import CrawlerHub
import asyncio
import json

async def example():
    # Get the crawler from the hub
    crawler_cls = CrawlerHub.get("lewz_baidu")
    crawler = crawler_cls()
    
    # Crawl an article
    result = await crawler.run(
        url="https://www.lewz.cn/jprj/12345.html",
        article_limit=1
    )
    
    # Parse and use the results
    articles = json.loads(result)
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Tags: {', '.join(article['seo_tags'])}")
        for link in article['share_links']:
            print(f"  Link: {link['url']}")
            print(f"  Password: {link['password']}")

asyncio.run(example())
```

### Using the CLI

Process a single article:
```bash
python -m crawl4ai.scripts.lewz_knowledge_pipeline \
    --url "https://www.lewz.cn/jprj/12345.html" \
    --limit 1 \
    --output article.json
```

Crawl a listing page:
```bash
python -m crawl4ai.scripts.lewz_knowledge_pipeline \
    --url "https://www.lewz.cn/jprj" \
    --limit 10 \
    --output results.json
```

### Direct Usage

```python
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler
import asyncio
import json

async def main():
    crawler = LewzKnowledgeCrawler()
    
    # Process a listing page
    result_json = await crawler.run(
        url="https://www.lewz.cn/jprj",
        article_limit=5
    )
    
    results = json.loads(result_json)
    print(f"Found {len(results)} articles")

asyncio.run(main())
```

## Output Schema

The crawler returns JSON with the following structure:

```json
[
  {
    "source_url": "https://www.lewz.cn/jprj/12345.html",
    "title": "Article Title",
    "seo_tags": ["tag1", "tag2", "tag3"],
    "share_links": [
      {
        "url": "https://pan.baidu.com/s/1234567890abcdef",
        "password": "abcd"
      },
      {
        "url": "https://pan.baidu.com/s/fedcba0987654321",
        "password": null
      }
    ]
  }
]
```

### Fields

- **source_url** (string): The URL of the article
- **title** (string): Article title extracted from `<title>`, `<h1>`, or meta tags
- **seo_tags** (array): List of SEO keywords and tags from meta tags and article content
- **share_links** (array): List of Baidu Netdisk share links
  - **url** (string): The Baidu Netdisk share URL
  - **password** (string|null): Extraction code/password, or null if not found

## Password Pattern Support

The crawler recognizes various password formats:

| Pattern | Example |
|---------|---------|
| Chinese colon | `提取码：abcd` |
| English colon | `提取码: xyz9` |
| Space separator | `提取码 test123` |
| Password keyword | `密码: pass1234` |
| Latin abbreviation | `pwd: testpwd` |
| Full word | `password: secret` |

Passwords must be at least 4 characters long to be recognized.

## Testing

Run the integration tests:

```bash
python tests/pipelines/test_lewz_integration.py
```

The test suite includes:
- Single article extraction
- Articles without Baidu links
- Malformed or missing passwords
- Output schema validation
- Listing page URL collection

## Implementation Details

### Components

- **LewzKnowledgeCrawler**: Main crawler class extending `BaseCrawler`
- **ArticleData**: Dataclass for structured article information
- **ShareLink**: Dataclass for Baidu share link with optional password

### Parsing Strategy

1. **Title Extraction**: Tries `<title>` tag, falls back to `<h1>`, then meta tags
2. **SEO Tags**: Extracts from meta keywords, article:tag properties, and tag class links
3. **Link Detection**: 
   - Finds links in `<a>` tags
   - Searches plain text with regex pattern
   - Checks for duplicate URLs
4. **Password Discovery**:
   - Checks URL query parameters (`?pwd=xxxx`)
   - Examines parent element text
   - Scans sibling elements (up to 3)
   - Applies regex patterns for various formats

## Dependencies

Uses existing Crawl4AI dependencies:
- `AsyncWebCrawler` for page fetching
- `BeautifulSoup4` for HTML parsing
- `re` and `urllib.parse` for pattern matching and URL handling

No additional dependencies required.

## Metadata

- **Version**: 1.0.0
- **Tested on**: lewz.cn/jprj
- **Rate limit**: 20 RPM (recommended)
- **Cache support**: Yes (configurable via `cache_mode` parameter)

## Error Handling

The crawler handles:
- Network failures (returns error JSON)
- Missing HTML elements (uses fallbacks)
- Malformed passwords (returns `null`)
- Articles without links (returns empty array)

Error responses include the error message and crawler metadata:

```json
{
  "error": "Failed to fetch article: Network timeout",
  "metadata": {
    "version": "1.0.0",
    "tested_on": ["lewz.cn/jprj"]
  }
}
```

## Contributing

When extending the crawler:

1. Add test fixtures to `tests/fixtures/lewz/`
2. Update integration tests in `tests/pipelines/test_lewz_integration.py`
3. Update this README with new features
4. Ensure backward compatibility with existing output schema
