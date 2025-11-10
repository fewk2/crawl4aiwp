import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from bs4 import BeautifulSoup

# Import the crawler and related classes
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler, ArticleData, ShareLink
from crawl4ai.models import CrawlResult


# Fixture paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "lewz"


def load_fixture(filename: str) -> str:
    """Load HTML fixture file"""
    with open(FIXTURES_DIR / filename, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def crawler():
    """Create a LewzKnowledgeCrawler instance"""
    return LewzKnowledgeCrawler()


@pytest.fixture
def article_with_links_html():
    """Load article with Baidu links fixture"""
    return load_fixture("article_with_links.html")


@pytest.fixture
def article_no_links_html():
    """Load article without links fixture"""
    return load_fixture("article_no_links.html")


@pytest.fixture
def article_malformed_password_html():
    """Load article with malformed password fixture"""
    return load_fixture("article_malformed_password.html")


@pytest.fixture
def listing_page_html():
    """Load listing page fixture"""
    return load_fixture("listing_page.html")


class TestPasswordExtraction:
    """Test password extraction from various text formats"""
    
    def test_extract_password_chinese_colon(self, crawler):
        """Test extraction with Chinese colon (：)"""
        text = "提取码：abcd"
        password = crawler._extract_password_from_text(text)
        assert password == "abcd"
    
    def test_extract_password_english_colon(self, crawler):
        """Test extraction with English colon (:)"""
        text = "提取码: xyz9"
        password = crawler._extract_password_from_text(text)
        assert password == "xyz9"
    
    def test_extract_password_with_space(self, crawler):
        """Test extraction with space separator"""
        text = "提取码 test123"
        password = crawler._extract_password_from_text(text)
        assert password == "test123"
    
    def test_extract_password_chinese_mima(self, crawler):
        """Test extraction with 密码 (password in Chinese)"""
        text = "密码: pass1234"
        password = crawler._extract_password_from_text(text)
        assert password == "pass1234"
    
    def test_extract_password_pwd(self, crawler):
        """Test extraction with pwd keyword"""
        text = "pwd: testpwd"
        password = crawler._extract_password_from_text(text)
        assert password == "testpwd"
    
    def test_extract_password_not_found(self, crawler):
        """Test when no password pattern is found"""
        text = "This text has no password"
        password = crawler._extract_password_from_text(text)
        assert password is None
    
    def test_extract_password_too_short(self, crawler):
        """Test that short passwords (< 4 chars) are not matched"""
        text = "提取码: ab"  # Only 2 characters
        password = crawler._extract_password_from_text(text)
        assert password is None


class TestBaiduLinkExtraction:
    """Test Baidu Netdisk link extraction"""
    
    def test_extract_links_from_article(self, crawler, article_with_links_html):
        """Test extraction of Baidu links from article HTML"""
        soup = BeautifulSoup(article_with_links_html, 'html.parser')
        share_links = crawler._extract_baidu_links(soup, article_with_links_html)
        
        assert len(share_links) == 2
        assert share_links[0].url == "https://pan.baidu.com/s/1AbCdEfGhIjKlMnOpQrStUv"
        assert share_links[0].password == "1234"
        assert share_links[1].url == "https://pan.baidu.com/s/2XyZaBcDeFgHiJkLmNoPqRs"
        assert share_links[1].password == "abcd"
    
    def test_extract_no_links(self, crawler, article_no_links_html):
        """Test article with no Baidu links"""
        soup = BeautifulSoup(article_no_links_html, 'html.parser')
        share_links = crawler._extract_baidu_links(soup, article_no_links_html)
        
        assert len(share_links) == 0
    
    def test_extract_links_without_password(self, crawler, article_malformed_password_html):
        """Test extraction when password is missing or malformed"""
        soup = BeautifulSoup(article_malformed_password_html, 'html.parser')
        share_links = crawler._extract_baidu_links(soup, article_malformed_password_html)
        
        assert len(share_links) >= 2
        # Some links should have no password
        assert any(link.password is None for link in share_links)


class TestTitleExtraction:
    """Test article title extraction"""
    
    def test_extract_title_from_title_tag(self, crawler, article_with_links_html):
        """Test title extraction from <title> tag"""
        soup = BeautifulSoup(article_with_links_html, 'html.parser')
        title = crawler._extract_title(soup)
        assert title == "测试文章 - Python编程资源"
    
    def test_extract_title_from_h1(self, crawler, article_with_links_html):
        """Test fallback to <h1> tag"""
        soup = BeautifulSoup(article_with_links_html, 'html.parser')
        # Remove title tag
        title_tag = soup.find('title')
        if title_tag:
            title_tag.decompose()
        
        title = crawler._extract_title(soup)
        assert "测试文章" in title or "Python" in title
    
    def test_extract_title_untitled(self, crawler):
        """Test default 'Untitled' when no title found"""
        html = "<html><body><p>No title</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        title = crawler._extract_title(soup)
        assert title == "Untitled"


class TestSEOTagsExtraction:
    """Test SEO tags and keywords extraction"""
    
    def test_extract_seo_tags_from_meta(self, crawler, article_with_links_html):
        """Test extraction from meta keywords"""
        soup = BeautifulSoup(article_with_links_html, 'html.parser')
        tags = crawler._extract_seo_tags(soup)
        
        assert "Python" in tags
        assert "编程" in tags
        assert "教程" in tags
        assert "资源" in tags
    
    def test_extract_seo_tags_from_tag_links(self, crawler, article_with_links_html):
        """Test extraction from tag links"""
        soup = BeautifulSoup(article_with_links_html, 'html.parser')
        tags = crawler._extract_seo_tags(soup)
        
        # Should include tags from <a class="tag">
        assert "教程" in tags
    
    def test_extract_seo_tags_empty(self, crawler):
        """Test when no SEO tags are present"""
        html = "<html><body><p>No tags</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        tags = crawler._extract_seo_tags(soup)
        assert len(tags) == 0


class TestListingPageParsing:
    """Test listing page URL collection"""
    
    def test_collect_article_urls_from_listing(self, crawler, listing_page_html):
        """Test URL collection from listing page"""
        soup = BeautifulSoup(listing_page_html, 'html.parser')
        
        # Extract article links manually to test the pattern
        article_urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/jprj/' in href and href.endswith('.html'):
                article_urls.append(href)
        
        assert len(article_urls) == 4
        assert any('12345.html' in url for url in article_urls)
        assert any('12346.html' in url for url in article_urls)


class TestArticleDataModel:
    """Test data models"""
    
    def test_share_link_to_dict(self):
        """Test ShareLink serialization"""
        link = ShareLink(url="https://pan.baidu.com/s/test", password="1234")
        data = link.to_dict()
        
        assert data['url'] == "https://pan.baidu.com/s/test"
        assert data['password'] == "1234"
    
    def test_article_data_to_dict(self):
        """Test ArticleData serialization"""
        share_links = [
            ShareLink(url="https://pan.baidu.com/s/test1", password="abc1"),
            ShareLink(url="https://pan.baidu.com/s/test2", password=None)
        ]
        
        article = ArticleData(
            source_url="https://www.lewz.cn/jprj/123.html",
            title="Test Article",
            seo_tags=["tag1", "tag2"],
            share_links=share_links
        )
        
        data = article.to_dict()
        
        assert data['source_url'] == "https://www.lewz.cn/jprj/123.html"
        assert data['title'] == "Test Article"
        assert len(data['seo_tags']) == 2
        assert len(data['share_links']) == 2
        assert data['share_links'][0]['password'] == "abc1"
        assert data['share_links'][1]['password'] is None


class TestCrawlerIntegration:
    """Test full crawler integration with mocked AsyncWebCrawler"""
    
    @pytest.mark.asyncio
    async def test_process_single_article(self, crawler, article_with_links_html):
        """Test processing a single article with mocked crawler"""
        # Create mock CrawlResult
        mock_result = MagicMock(spec=CrawlResult)
        mock_result.success = True
        mock_result.html = article_with_links_html
        mock_result.error_message = None
        
        # Mock AsyncWebCrawler
        with patch('crawl4ai.crawlers.lewz_baidu.crawler.AsyncWebCrawler') as mock_crawler_class:
            mock_crawler_instance = AsyncMock()
            mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
            mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
            mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
            mock_crawler_class.return_value = mock_crawler_instance
            
            # Test the crawler
            result_json = await crawler.run(
                url="https://www.lewz.cn/jprj/12345.html",
                article_limit=1
            )
            
            result = json.loads(result_json)
            
            assert isinstance(result, list)
            assert len(result) == 1
            
            article = result[0]
            assert article['source_url'] == "https://www.lewz.cn/jprj/12345.html"
            assert article['title'] == "测试文章 - Python编程资源"
            assert len(article['seo_tags']) > 0
            assert len(article['share_links']) == 2
    
    @pytest.mark.asyncio
    async def test_process_article_no_links(self, crawler, article_no_links_html):
        """Test processing article with no Baidu links"""
        mock_result = MagicMock(spec=CrawlResult)
        mock_result.success = True
        mock_result.html = article_no_links_html
        mock_result.error_message = None
        
        with patch('crawl4ai.crawlers.lewz_baidu.crawler.AsyncWebCrawler') as mock_crawler_class:
            mock_crawler_instance = AsyncMock()
            mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
            mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
            mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
            mock_crawler_class.return_value = mock_crawler_instance
            
            result_json = await crawler.run(
                url="https://www.lewz.cn/jprj/12345.html",
                article_limit=1
            )
            
            result = json.loads(result_json)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert len(result[0]['share_links']) == 0
    
    @pytest.mark.asyncio
    async def test_crawler_error_handling(self, crawler):
        """Test error handling when crawl fails"""
        mock_result = MagicMock(spec=CrawlResult)
        mock_result.success = False
        mock_result.error_message = "Network error"
        
        with patch('crawl4ai.crawlers.lewz_baidu.crawler.AsyncWebCrawler') as mock_crawler_class:
            mock_crawler_instance = AsyncMock()
            mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
            mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
            mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
            mock_crawler_class.return_value = mock_crawler_instance
            
            result_json = await crawler.run(
                url="https://www.lewz.cn/jprj/12345.html",
                article_limit=1
            )
            
            result = json.loads(result_json)
            
            # Should return error object
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_collect_article_urls(self, crawler, listing_page_html):
        """Test collecting article URLs from listing page"""
        mock_result = MagicMock(spec=CrawlResult)
        mock_result.success = True
        mock_result.html = listing_page_html
        mock_result.error_message = None
        
        with patch('crawl4ai.crawlers.lewz_baidu.crawler.AsyncWebCrawler') as mock_crawler_class:
            mock_crawler_instance = AsyncMock()
            mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
            mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
            mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
            mock_crawler_class.return_value = mock_crawler_instance
            
            # Test URL collection
            from crawl4ai import CacheMode
            urls = await crawler._collect_article_urls(
                "https://www.lewz.cn/jprj",
                limit=10,
                cache_mode=CacheMode.BYPASS
            )
            
            assert len(urls) == 4
            assert all('/jprj/' in url for url in urls)
            assert all('.html' in url for url in urls)


class TestOutputSchema:
    """Test that output matches expected schema"""
    
    def test_output_schema_structure(self):
        """Test that output has correct structure"""
        share_links = [
            ShareLink(url="https://pan.baidu.com/s/test", password="1234")
        ]
        
        article = ArticleData(
            source_url="https://www.lewz.cn/jprj/123.html",
            title="Test",
            seo_tags=["tag1"],
            share_links=share_links
        )
        
        data = article.to_dict()
        
        # Verify all required fields are present
        assert 'source_url' in data
        assert 'title' in data
        assert 'seo_tags' in data
        assert 'share_links' in data
        
        # Verify types
        assert isinstance(data['source_url'], str)
        assert isinstance(data['title'], str)
        assert isinstance(data['seo_tags'], list)
        assert isinstance(data['share_links'], list)
        
        # Verify share_link structure
        assert 'url' in data['share_links'][0]
        assert 'password' in data['share_links'][0]
    
    def test_json_serializable(self):
        """Test that output is JSON serializable"""
        share_links = [
            ShareLink(url="https://pan.baidu.com/s/test", password="1234")
        ]
        
        article = ArticleData(
            source_url="https://www.lewz.cn/jprj/123.html",
            title="Test Article",
            seo_tags=["tag1", "tag2"],
            share_links=share_links
        )
        
        data = article.to_dict()
        
        # Should not raise exception
        json_str = json.dumps([data], ensure_ascii=False)
        parsed = json.loads(json_str)
        
        assert len(parsed) == 1
        assert parsed[0]['title'] == "Test Article"
