#!/usr/bin/env python3
"""
Lewz Knowledge Base Pipeline CLI

A command-line interface for crawling https://www.lewz.cn/jprj and extracting
Baidu Netdisk links and article metadata.

Usage:
    python -m crawl4ai.scripts.lewz_knowledge_pipeline \\
        --url "https://www.lewz.cn/jprj" \\
        --limit 10 \\
        --output results.json

Exit codes:
    0 - Success
    1 - Error during crawling or processing
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crawl4ai.crawlers.lewz_baidu import LewzKnowledgeCrawler


async def run_pipeline(url: str, limit: int, output_path: Optional[str] = None) -> int:
    """
    Run the Lewz knowledge base crawling pipeline.
    
    Args:
        url: Starting URL (listing page or article URL)
        limit: Maximum number of articles to process
        output_path: Optional path to save JSON output
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        crawler = LewzKnowledgeCrawler()
        
        print(f"Starting crawl of {url}")
        print(f"Article limit: {limit}")
        print(f"Crawler version: {crawler.__meta__['version']}")
        print("-" * 60)
        
        # Run the crawler
        result_json = await crawler.run(url=url, article_limit=limit)
        
        # Parse result to check for errors
        result = json.loads(result_json)
        
        if isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            return 1
        
        # Output results
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {output_path}")
        else:
            # Print to stdout
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Print summary
        if isinstance(result, list):
            print("-" * 60)
            print(f"Successfully processed {len(result)} article(s)")
            for item in result:
                print(f"  - {item.get('title', 'Untitled')}: {len(item.get('share_links', []))} share link(s)")
        
        return 0
        
    except Exception as e:
        print(f"Pipeline error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Crawl Lewz knowledge base and extract Baidu Netdisk links",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl listing page and extract up to 5 articles
  python -m crawl4ai.scripts.lewz_knowledge_pipeline \\
      --url "https://www.lewz.cn/jprj" --limit 5

  # Process a single article
  python -m crawl4ai.scripts.lewz_knowledge_pipeline \\
      --url "https://www.lewz.cn/jprj/12345.html" --limit 1

  # Save results to file
  python -m crawl4ai.scripts.lewz_knowledge_pipeline \\
      --url "https://www.lewz.cn/jprj" --limit 10 \\
      --output results.json

Output format:
  [
    {
      "source_url": "https://www.lewz.cn/jprj/12345.html",
      "title": "Article Title",
      "seo_tags": ["tag1", "tag2"],
      "share_links": [
        {
          "url": "https://pan.baidu.com/s/xxxxx",
          "password": "abcd"
        }
      ]
    }
  ]
        """
    )
    
    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help='Starting URL (listing page or article URL)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of articles to process (default: 10)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file path (default: stdout)'
    )
    
    args = parser.parse_args()
    
    # Run the async pipeline
    exit_code = asyncio.run(run_pipeline(args.url, args.limit, args.output))
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
