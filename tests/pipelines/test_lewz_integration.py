"""
Integration test for Lewz crawler - demonstrates full workflow with fixtures.
This test does not require network access or pytest.
"""

import json
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler
from crawl4ai.models import CrawlResult


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "lewz"


def load_fixture(filename: str) -> str:
    """Load HTML fixture file"""
    with open(FIXTURES_DIR / filename, 'r', encoding='utf-8') as f:
        return f.read()


async def test_single_article_extraction():
    """Test extracting data from a single article"""
    print("Testing single article extraction...")
    
    crawler = LewzKnowledgeCrawler()
    article_html = load_fixture("article_with_links.html")
    
    # Mock the AsyncWebCrawler
    mock_result = MagicMock(spec=CrawlResult)
    mock_result.success = True
    mock_result.html = article_html
    mock_result.error_message = None
    
    with patch('crawl4ai.crawlers.lewz_baidu.crawler.AsyncWebCrawler') as mock_crawler_class:
        mock_crawler_instance = AsyncMock()
        mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
        mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
        mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler_instance
        
        # Run the crawler
        result_json = await crawler.run(
            url="https://www.lewz.cn/jprj/12345.html",
            article_limit=1
        )
        
        # Parse and validate result
        result = json.loads(result_json)
        
        assert isinstance(result, list), "Result should be a list"
        assert len(result) == 1, "Should have 1 article"
        
        article = result[0]
        assert article['source_url'] == "https://www.lewz.cn/jprj/12345.html"
        assert "Python" in article['title']
        assert len(article['seo_tags']) > 0
        assert len(article['share_links']) == 2
        assert article['share_links'][0]['password'] == "1234"
        assert article['share_links'][1]['password'] == "abcd"
        
        print("  ✓ Single article extraction passed")
        return True


async def test_article_without_links():
    """Test article with no Baidu links"""
    print("Testing article without links...")
    
    crawler = LewzKnowledgeCrawler()
    article_html = load_fixture("article_no_links.html")
    
    mock_result = MagicMock(spec=CrawlResult)
    mock_result.success = True
    mock_result.html = article_html
    mock_result.error_message = None
    
    with patch('crawl4ai.crawlers.lewz_baidu.crawler.AsyncWebCrawler') as mock_crawler_class:
        mock_crawler_instance = AsyncMock()
        mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
        mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
        mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler_instance
        
        result_json = await crawler.run(
            url="https://www.lewz.cn/jprj/99999.html",
            article_limit=1
        )
        
        result = json.loads(result_json)
        assert len(result[0]['share_links']) == 0, "Should have no links"
        
        print("  ✓ Article without links passed")
        return True


async def test_malformed_password():
    """Test handling of articles with missing/malformed passwords"""
    print("Testing malformed password handling...")
    
    crawler = LewzKnowledgeCrawler()
    article_html = load_fixture("article_malformed_password.html")
    
    mock_result = MagicMock(spec=CrawlResult)
    mock_result.success = True
    mock_result.html = article_html
    mock_result.error_message = None
    
    with patch('crawl4ai.crawlers.lewz_baidu.crawler.AsyncWebCrawler') as mock_crawler_class:
        mock_crawler_instance = AsyncMock()
        mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
        mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
        mock_crawler_instance.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler_instance
        
        result_json = await crawler.run(
            url="https://www.lewz.cn/jprj/88888.html",
            article_limit=1
        )
        
        result = json.loads(result_json)
        
        # Should extract links even without passwords
        assert len(result[0]['share_links']) >= 2
        # At least some should have None password
        assert any(link['password'] is None for link in result[0]['share_links'])
        
        print("  ✓ Malformed password handling passed")
        return True


async def test_output_schema():
    """Test that output matches expected schema"""
    print("Testing output schema...")
    
    crawler = LewzKnowledgeCrawler()
    article_html = load_fixture("article_with_links.html")
    
    mock_result = MagicMock(spec=CrawlResult)
    mock_result.success = True
    mock_result.html = article_html
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
        article = result[0]
        
        # Verify all required fields
        required_fields = ['source_url', 'title', 'seo_tags', 'share_links']
        for field in required_fields:
            assert field in article, f"Missing required field: {field}"
        
        # Verify types
        assert isinstance(article['source_url'], str)
        assert isinstance(article['title'], str)
        assert isinstance(article['seo_tags'], list)
        assert isinstance(article['share_links'], list)
        
        # Verify share_link structure
        if len(article['share_links']) > 0:
            link = article['share_links'][0]
            assert 'url' in link
            assert 'password' in link
        
        print("  ✓ Output schema validation passed")
        return True


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("Lewz Crawler Integration Tests")
    print("="*60 + "\n")
    
    tests = [
        test_single_article_extraction,
        test_article_without_links,
        test_malformed_password,
        test_output_schema,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Test failed: {str(e)}")
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60 + "\n")
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
