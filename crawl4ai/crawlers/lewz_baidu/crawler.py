from crawl4ai import BrowserConfig, AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.hub import BaseCrawler
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import json
import re
from urllib.parse import urlparse, parse_qs


__meta__ = {
    "version": "1.0.0",
    "tested_on": ["lewz.cn/jprj"],
    "rate_limit": "20 RPM",
    "description": "Extracts Baidu Netdisk links and metadata from Lewz knowledge base",
}


@dataclass
class ShareLink:
    """Represents a Baidu Netdisk share link with optional password"""
    url: str
    password: Optional[str] = None

    def to_dict(self) -> Dict:
        return {"url": self.url, "password": self.password}


@dataclass
class ArticleData:
    """Structured data for an article with Baidu share links"""
    source_url: str
    title: str
    seo_tags: List[str]
    share_links: List[ShareLink]

    def to_dict(self) -> Dict:
        return {
            "source_url": self.source_url,
            "title": self.title,
            "seo_tags": self.seo_tags,
            "share_links": [link.to_dict() for link in self.share_links]
        }


class LewzKnowledgeCrawler(BaseCrawler):
    """
    Crawler for https://www.lewz.cn/jprj that extracts Baidu Netdisk links and article metadata.
    
    Expected return schema:
    {
        "source_url": "https://www.lewz.cn/jprj/12345.html",
        "title": "Article Title",
        "seo_tags": ["tag1", "tag2", "tag3"],
        "share_links": [
            {
                "url": "https://pan.baidu.com/s/1234567890",
                "password": "abcd"
            }
        ]
    }
    """
    
    __meta__ = {
        "version": "1.0.0",
        "tested_on": ["lewz.cn/jprj"],
        "rate_limit": "20 RPM",
        "description": "Extracts Baidu Netdisk links and metadata from Lewz knowledge base",
    }

    def __init__(self):
        super().__init__()

    async def run(self, url: str = "", article_limit: int = 10, **kwargs) -> str:
        """
        Crawl Lewz knowledge base and extract article data.
        
        Args:
            url: Starting URL (listing page or direct article URL)
            article_limit: Maximum number of articles to process
            **kwargs: Additional configuration options
                - cache_mode: Cache mode to use (default: BYPASS)
                - output_format: 'json' (default) or 'raw'
        
        Returns:
            JSON string containing list of ArticleData objects
        """
        try:
            cache_mode = kwargs.get("cache_mode", CacheMode.BYPASS)
            
            # Check if this is a listing page or article page
            if "/jprj/" in url and url.split("/jprj/")[-1].replace(".html", "").isdigit():
                # Direct article URL
                article_data = await self._process_article(url, cache_mode)
                return json.dumps([article_data.to_dict()], indent=2, ensure_ascii=False)
            else:
                # Listing page - collect article URLs
                article_urls = await self._collect_article_urls(url, article_limit, cache_mode)
                
                # Process each article
                results = []
                for article_url in article_urls[:article_limit]:
                    try:
                        article_data = await self._process_article(article_url, cache_mode)
                        results.append(article_data.to_dict())
                    except Exception as e:
                        self.logger.warning(f"Failed to process {article_url}: {str(e)}")
                        continue
                
                return json.dumps(results, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Crawl failed: {str(e)}")
            return json.dumps({
                "error": str(e),
                "metadata": self.__meta__
            }, ensure_ascii=False)

    async def _collect_article_urls(self, listing_url: str, limit: int, cache_mode) -> List[str]:
        """
        Collect article URLs from listing page.
        
        Args:
            listing_url: URL of the listing page
            limit: Maximum number of URLs to collect
            cache_mode: Cache mode to use
            
        Returns:
            List of article URLs
        """
        browser_config = BrowserConfig(headless=True, verbose=False)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                cache_mode=cache_mode,
                delay_before_return_html=1.0
            )
            
            result = await crawler.arun(url=listing_url, config=config)
            if not result.success:
                raise Exception(f"Failed to fetch listing page: {result.error_message}")
            
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Extract article links from listing page
            article_urls = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Look for article URLs in the pattern /jprj/123.html
                if '/jprj/' in href and href.endswith('.html'):
                    # Handle relative URLs
                    if href.startswith('/'):
                        parsed = urlparse(listing_url)
                        full_url = f"{parsed.scheme}://{parsed.netloc}{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    if full_url not in article_urls:
                        article_urls.append(full_url)
                        if len(article_urls) >= limit:
                            break
            
            return article_urls

    async def _process_article(self, article_url: str, cache_mode) -> ArticleData:
        """
        Process a single article and extract metadata and Baidu links.
        
        Args:
            article_url: URL of the article
            cache_mode: Cache mode to use
            
        Returns:
            ArticleData object with extracted information
        """
        browser_config = BrowserConfig(headless=True, verbose=False)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                cache_mode=cache_mode,
                delay_before_return_html=1.0
            )
            
            result = await crawler.arun(url=article_url, config=config)
            if not result.success:
                raise Exception(f"Failed to fetch article: {result.error_message}")
            
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract SEO tags (keywords, meta tags)
            seo_tags = self._extract_seo_tags(soup)
            
            # Extract Baidu share links
            share_links = self._extract_baidu_links(soup, result.html)
            
            return ArticleData(
                source_url=article_url,
                title=title,
                seo_tags=seo_tags,
                share_links=share_links
            )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title from HTML"""
        # Try multiple strategies
        # 1. <title> tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # 2. <h1> tag
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        # 3. meta og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        return "Untitled"

    def _extract_seo_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract SEO tags and keywords from HTML"""
        tags = []
        
        # 1. Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = meta_keywords['content']
            tags.extend([k.strip() for k in keywords.split(',') if k.strip()])
        
        # 2. Meta tags (og:tag, article:tag, etc.)
        for meta in soup.find_all('meta'):
            if meta.get('property') in ['article:tag', 'og:tag']:
                content = meta.get('content', '').strip()
                if content and content not in tags:
                    tags.append(content)
        
        # 3. Tag links (common in CMS)
        for tag_link in soup.find_all('a', class_=re.compile(r'tag|keyword|label', re.I)):
            tag_text = tag_link.get_text().strip()
            if tag_text and tag_text not in tags:
                tags.append(tag_text)
        
        return tags

    def _extract_baidu_links(self, soup: BeautifulSoup, html_text: str) -> List[ShareLink]:
        """
        Extract Baidu Netdisk share links and passwords from HTML.
        
        Supports:
        - Direct links: https://pan.baidu.com/s/xxxxx
        - Password in text: "提取码: abcd", "提取码：abcd", "密码: abcd"
        - Password in URL: ?pwd=abcd
        """
        share_links = []
        
        # Find all Baidu pan links
        baidu_pattern = r'https?://pan\.baidu\.com/s/[A-Za-z0-9_-]+'
        
        # Search in all <a> tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'pan.baidu.com/s/' in href:
                url = re.search(baidu_pattern, href)
                if url:
                    baidu_url = url.group(0)
                    
                    # Check for pwd in URL parameters
                    parsed = urlparse(baidu_url)
                    pwd = None
                    if '?' in href:
                        query_params = parse_qs(urlparse(href).query)
                        pwd = query_params.get('pwd', [None])[0]
                    
                    # If no pwd in URL, look for password in nearby text
                    if not pwd:
                        pwd = self._find_nearby_password(link, soup)
                    
                    share_links.append(ShareLink(url=baidu_url, password=pwd))
        
        # Also search in plain text for links not in <a> tags
        text_matches = re.finditer(baidu_pattern, html_text)
        for match in text_matches:
            baidu_url = match.group(0)
            # Check if this URL is already in our list
            if not any(link.url == baidu_url for link in share_links):
                # Try to find password near this URL in text
                pwd = self._find_password_in_context(html_text, match.start(), match.end())
                share_links.append(ShareLink(url=baidu_url, password=pwd))
        
        return share_links

    def _find_nearby_password(self, link_element, soup: BeautifulSoup) -> Optional[str]:
        """Find password near a link element"""
        # Check parent element text
        parent = link_element.parent
        if parent:
            parent_text = parent.get_text()
            pwd = self._extract_password_from_text(parent_text)
            if pwd:
                return pwd
            
            # Check parent's next siblings (common pattern: link in one <p>, password in next <p>)
            for sibling in parent.find_next_siblings(limit=3):
                if hasattr(sibling, 'get_text'):
                    pwd = self._extract_password_from_text(sibling.get_text())
                    if pwd:
                        return pwd
        
        # Check link's own next siblings as fallback
        for sibling in link_element.find_next_siblings(limit=3):
            if hasattr(sibling, 'get_text'):
                pwd = self._extract_password_from_text(sibling.get_text())
                if pwd:
                    return pwd
        
        return None

    def _find_password_in_context(self, text: str, start_pos: int, end_pos: int, context_size: int = 200) -> Optional[str]:
        """Find password in surrounding context of a URL"""
        # Extract text around the URL
        context_start = max(0, start_pos - context_size)
        context_end = min(len(text), end_pos + context_size)
        context = text[context_start:context_end]
        
        return self._extract_password_from_text(context)

    def _extract_password_from_text(self, text: str) -> Optional[str]:
        """
        Extract password from text using various patterns.
        
        Patterns supported:
        - 提取码: abcd
        - 提取码：abcd
        - 密码: abcd
        - 密码：abcd
        - 提取码 abcd
        - pwd: abcd
        - password: abcd
        """
        # Chinese patterns
        patterns = [
            r'提取码[：:]\s*([A-Za-z0-9]{4,})',
            r'提取码\s+([A-Za-z0-9]{4,})',
            r'密码[：:]\s*([A-Za-z0-9]{4,})',
            r'密码\s+([A-Za-z0-9]{4,})',
            r'pwd[：:]\s*([A-Za-z0-9]{4,})',
            r'password[：:]\s*([A-Za-z0-9]{4,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
