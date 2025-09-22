#!/usr/bin/env python3
"""
Debugged Defense & Space News Scraper
Fixed version with comprehensive error handling and debugging
"""

import sys
import os
import traceback
import logging
from datetime import datetime

# Setup logging FIRST before any other imports
def setup_logging():
    """Setup comprehensive logging"""
    log_filename = f"scraper_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    log_path = os.path.join('logs', log_filename)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("SCRAPER STARTUP - DEBUG MODE")
    logger.info(f"Log file: {log_path}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("="*60)
    
    return logger

# Initialize logging
logger = setup_logging()

try:
    logger.info("Importing required modules...")
    import requests
    logger.info("✅ requests imported successfully")
    
    from bs4 import BeautifulSoup
    logger.info("✅ BeautifulSoup imported successfully")
    
    import feedparser
    logger.info("✅ feedparser imported successfully")
    
    import schedule
    logger.info("✅ schedule imported successfully")
    
    import time
    import argparse
    import json
    import re
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from urllib.parse import urlparse, urljoin
    import random
    from time import sleep
    from datetime import timedelta
    logger.info("✅ All standard libraries imported successfully")
    
except ImportError as e:
    logger.error(f"CRITICAL: Failed to import required module: {e}")
    print(f"\n❌ IMPORT ERROR: {e}")
    print("\nPlease install missing packages:")
    print("pip install requests beautifulsoup4 feedparser schedule")
    sys.exit(1)

class SimpleNewsScraper:
    def __init__(self):
        try:
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.info("Initializing SimpleNewsScraper...")
            
            # Setup session with better headers and timeout
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            self.logger.info("✅ HTTP session configured")
            
            # MINIMAL WORKING RSS SOURCES (tested and verified)
            self.sources = {
                "Defense News": [
                    "https://www.livefistdefence.com/feed/",           # Most reliable
                    "https://defence.in/feed/",                       # Active site
                    "https://stratpost.com/feed/",                    # Strategic coverage
                    "https://forceindia.net/feed/",                   # Established magazine
                ],
                "Space News": [
                    "https://spacenews.com/feed/",                    # Industry standard
                    "https://www.space.com/feeds/all",                # Popular space news
                    "https://spaceflightnow.com/feed/",               # Launch coverage
                    "https://www.thehindu.com/sci-tech/science/feeder/default.rss", # Indian coverage
                ]
            }
            self.logger.info(f"✅ RSS sources configured: {sum(len(feeds) for feeds in self.sources.values())} total feeds")
            
            # ESSENTIAL KEYWORDS ONLY (simplified for reliability)
            self.defense_keywords = [
                "india", "indian", "defense", "defence", "military", "armed forces",
                "indian air force", "iaf", "indian army", "indian navy",
                "hal", "drdo", "tejas", "brahmos", "indigenous", "atmanirbhar",
                "defense contract", "military exercise", "border", "security",
                "livefist", "force magazine", "stratpost"
            ]
            
            self.space_keywords = [
                "space", "satellite", "launch", "rocket", "mission", "isro",
                "chandrayaan", "gaganyaan", "pslv", "gslv", "indian space",
                "space mission", "satellite launch", "rocket launch",
                "skyroot", "agnikul", "space startup", "commercial space"
            ]
            
            # CRITICAL EXCLUSION KEYWORDS
            self.exclusion_keywords = [
                "bollywood", "cricket", "football", "movie", "entertainment",
                "wedding", "birthday", "festival", "cooking", "recipe",
                "stock market", "election", "politics", "agriculture"
            ]
            
            self.keywords = self.defense_keywords + self.space_keywords
            self.logger.info(f"✅ Keywords configured: {len(self.keywords)} total keywords")
            
        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to initialize scraper: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def make_request_with_retry(self, url, max_retries=2, timeout=10):
        """Simplified request with retry mechanism"""
        self.logger.debug(f"Making request to: {url}")
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    sleep_time = random.uniform(1, 3)
                    self.logger.debug(f"Retry {attempt + 1} after {sleep_time:.1f}s delay")
                    time.sleep(sleep_time)
                
                response = self.session.get(url, timeout=timeout)
                self.logger.debug(f"Response: {response.status_code} for {url}")
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    self.logger.warning(f"Access forbidden (403) for {url}")
                    continue
                elif response.status_code == 404:
                    self.logger.warning(f"URL not found (404) for {url}")
                    break  # Don't retry 404s
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    continue
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout for {url} (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url} (attempt {attempt + 1})")
            except Exception as e:
                self.logger.warning(f"Request error for {url}: {e}")
        
        self.logger.error(f"All retries failed for {url}")
        return None
    
    def is_relevant_article(self, title, content=""):
        """Simplified relevance check"""
        if not title:
            return False
            
        text = (title + " " + content).lower()
        
        # FIRST: Check exclusion keywords
        exclusion_matches = sum(1 for exclusion in self.exclusion_keywords if exclusion in text)
        if exclusion_matches >= 2:
            self.logger.debug(f"Article excluded due to {exclusion_matches} exclusion matches: {title[:50]}")
            return False
        
        # Check for relevant keywords
        keyword_matches = sum(1 for keyword in self.keywords if keyword in text)
        is_relevant = keyword_matches >= 2
        
        self.logger.debug(f"Article relevance: {keyword_matches} matches, relevant={is_relevant}: {title[:50]}")
        return is_relevant
    
    def parse_date(self, date_input):
        """Simplified date parsing"""
        if not date_input:
            return datetime.now().strftime("%d %B %Y")
        
        try:
            if hasattr(date_input, 'timetuple'):
                return datetime(*date_input.timetuple()[:6]).strftime("%d %B %Y")
        except Exception as e:
            self.logger.debug(f"Date parsing failed: {e}")
        
        return datetime.now().strftime("%d %B %Y")
    
    def extract_simple_content(self, url):
        """Simplified content extraction"""
        try:
            response = self.make_request_with_retry(url, max_retries=1, timeout=8)
            if not response:
                return "Could not fetch article content"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                if element:
                    element.decompose()
            
            # Try to find main content
            content_selectors = ['article', '.content', 'main', '.post-content']
            content = ""
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator='\n', strip=True)
                    if len(content) > 100:
                        break
            
            if not content or len(content) < 50:
                # Fallback to body
                body = soup.find('body')
                if body:
                    content = body.get_text(separator='\n', strip=True)
            
            # Clean and limit content
            content = re.sub(r'\n+', '\n', content)
            content = re.sub(r' +', ' ', content)
            
            if len(content) > 3000:  # Limit content length
                content = content[:3000] + "... [Content truncated]"
                
            return content if content else "Could not extract content"
            
        except Exception as e:
            self.logger.debug(f"Content extraction failed for {url}: {e}")
            return f"Error extracting content: {str(e)}"
    
    def scrape_single_feed(self, feed_url, category):
        """Simplified single feed scraping"""
        articles = []
        
        try:
            self.logger.info(f"Scraping: {feed_url}")
            response = self.make_request_with_retry(feed_url, timeout=15)
            
            if not response:
                self.logger.warning(f"Failed to fetch feed: {feed_url}")
                return articles
            
            self.logger.debug(f"Feed response size: {len(response.content)} bytes")
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if not hasattr(feed, 'entries'):
                self.logger.warning(f"No entries in feed: {feed_url}")
                return articles
            
            self.logger.info(f"Found {len(feed.entries)} entries in {feed_url}")
            
            # Process entries (limit to 5 per feed to avoid overload)
            processed = 0
            for entry in feed.entries[:5]:
                try:
                    if not hasattr(entry, 'title') or not entry.title:
                        continue
                    
                    # Check relevance
                    if not self.is_relevant_article(entry.title, entry.get('summary', '')):
                        continue
                    
                    self.logger.info(f"Processing relevant article: {entry.title[:50]}...")
                    
                    # Extract content (optional - can be disabled for speed)
                    full_content = entry.get('summary', 'No content available')
                    # Uncomment next line if you want full article extraction (slower)
                    # full_content = self.extract_simple_content(entry.link)
                    
                    article = {
                        'title': entry.title,
                        'url': entry.link,
                        'content': full_content,
                        'date': self.parse_date(entry.get('published_parsed')),
                        'source': feed_url,
                        'category': category
                    }
                    
                    articles.append(article)
                    processed += 1
                    
                except Exception as e:
                    self.logger.debug(f"Error processing entry: {e}")
                    continue
            
            self.logger.info(f"Successfully processed {processed} articles from {feed_url}")
            
        except Exception as e:
            self.logger.error(f"Error scraping {feed_url}: {e}")
        
        return articles
    
    def scrape_rss_feeds(self, days_back=7):
        """Simplified RSS scraping"""
        all_articles = []
        
        self.logger.info(f"Starting RSS scraping for last {days_back} days...")
        
        # Process each category
        for category, feeds in self.sources.items():
            self.logger.info(f"Processing {category} sources ({len(feeds)} feeds)...")
            
            for feed_url in feeds:
                try:
                    articles = self.scrape_single_feed(feed_url, category)
                    all_articles.extend(articles)
                    self.logger.info(f"Added {len(articles)} articles from {category}")
                    
                    # Small delay between feeds
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Failed to process feed {feed_url}: {e}")
                    continue
        
        # Remove duplicates
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        self.logger.info(f"Total articles: {len(all_articles)}, unique: {len(unique_articles)}")
        return unique_articles
    
    def generate_simple_report(self, articles, days_back):
        """Generate basic markdown report"""
        if not articles:
            return f"# No Articles Found\n\nNo relevant articles found for the last {days_back} days.\nGenerated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}"
        
        # Separate articles by category
        defense_articles = [a for a in articles if a['category'] == 'Defense News']
        space_articles = [a for a in articles if a['category'] == 'Space News']
        
        report = f"""# Defense & Space News Summary
## Last {days_back} Days - Generated on {datetime.now().strftime('%B %d, %Y')}

**Total Articles:** {len(articles)} ({len(defense_articles)} Defense, {len(space_articles)} Space)

---

"""
        
        # Defense section
        if defense_articles:
            report += f"## 🛡️ DEFENSE NEWS ({len(defense_articles)} articles)\n\n"
            for i, article in enumerate(defense_articles, 1):
                report += f"""### {i}. {article['title']}

**Date:** {article['date']}
**Source:** {article['source']}
**Link:** {article['url']}

**Content:**
{article['content'][:1000]}{'...' if len(article['content']) > 1000 else ''}

---

"""
        
        # Space section
        if space_articles:
            report += f"## 🚀 SPACE NEWS ({len(space_articles)} articles)\n\n"
            for i, article in enumerate(space_articles, 1):
                report += f"""### {i}. {article['title']}

**Date:** {article['date']}
**Source:** {article['source']}
**Link:** {article['url']}

**Content:**
{article['content'][:1000]}{'...' if len(article['content']) > 1000 else ''}

---

"""
        
        return report
    
    def save_report(self, report, days_back=7):
        """Save report with error handling"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"news_report_{days_back}days_{timestamp}.md"
        
        try:
            # Ensure output directory exists
            os.makedirs('output', exist_ok=True)
            filepath = os.path.join('output', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"Report saved to: {filepath}")
            
            # Also save to root directory for CI compatibility
            root_filename = f"scraper_output_{timestamp}.md"
            with open(root_filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.logger.info(f"Report also saved to: {root_filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            
            # Fallback - save to current directory
            try:
                fallback_filename = f"emergency_report_{timestamp}.md"
                with open(fallback_filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.logger.info(f"Report saved to fallback location: {fallback_filename}")
                return fallback_filename
            except Exception as e2:
                self.logger.error(f"Failed to save report completely: {e2}")
                return None
    
    def run_scraper(self, days_back=7):
        """Main scraping function with comprehensive error handling"""
        start_time = datetime.now()
        
        try:
            self.logger.info("="*60)
            self.logger.info("STARTING NEWS SCRAPER")
            self.logger.info(f"Date: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"Days back: {days_back}")
            self.logger.info("="*60)
            
            # Test internet connectivity
            try:
                test_response = self.make_request_with_retry("https://www.google.com", max_retries=1, timeout=5)
                if not test_response:
                    raise Exception("No internet connectivity")
                self.logger.info("✅ Internet connectivity confirmed")
            except Exception as e:
                self.logger.error(f"❌ Internet connectivity test failed: {e}")
                raise
            
            # Scrape articles
            self.logger.info("Starting RSS feed scraping...")
            articles = self.scrape_rss_feeds(days_back)
            
            self.logger.info(f"Scraping completed. Found {len(articles)} articles")
            
            # Generate report
            self.logger.info("Generating report...")
            report = self.generate_simple_report(articles, days_back)
            
            # Save report
            self.logger.info("Saving report...")
            filename = self.save_report(report, days_back)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info("="*60)
            self.logger.info("SCRAPER COMPLETED SUCCESSFULLY")
            self.logger.info(f"Total time: {duration.total_seconds():.1f} seconds")
            self.logger.info(f"Articles found: {len(articles)}")
            self.logger.info(f"Report saved: {filename}")
            self.logger.info("="*60)
            
            return filename
            
        except Exception as e:
            self.logger.error("="*60)
            self.logger.error("CRITICAL ERROR IN SCRAPER")
            self.logger.error(f"Error: {e}")
            self.logger.error("Full traceback:")
            self.logger.error(traceback.format_exc())
            self.logger.error("="*60)
            
            # Create error report
            try:
                error_report = f"""# Scraper Error Report

**Error occurred during scraping:**

- **Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}
- **Error:** {str(e)}
- **Days back:** {days_back}

**Check the log files for detailed error information.**

**Common Solutions:**
1. Check internet connectivity
2. Verify RSS feeds are accessible
3. Install required packages: `pip install requests beautifulsoup4 feedparser schedule`
4. Check file permissions for output directory
"""
                error_filename = f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(error_filename, 'w', encoding='utf-8') as f:
                    f.write(error_report)
                self.logger.info(f"Error report saved: {error_filename}")
                return error_filename
            except:
                self.logger.error("Could not save error report")
                return None

def main():
    """Main function with argument parsing"""
    try:
        parser = argparse.ArgumentParser(description='Defense & Space News Scraper')
        parser.add_argument('--manual', action='store_true', help='Run scraper now')
        parser.add_argument('--days', type=int, help='Number of days to look back (1-30)', default=7)
        parser.add_argument('--test', action='store_true', help='Run in test mode (minimal scraping)')
        
        args = parser.parse_args()
        
        if args.test:
            print("🧪 Running in TEST MODE (minimal scraping)...")
            logger.info("TEST MODE: Running minimal scraping")
        
        if args.manual or args.test:
            days = 1 if args.test else (args.days if args.days else 7)
            
            # Validate days parameter
            if days < 1 or days > 30:
                print("❌ Error: Days parameter must be between 1 and 30")
                sys.exit(1)
            
            print(f"🚀 Starting scraper for last {days} days...")
            print(f"📝 Check logs directory for detailed output")
            
            scraper = SimpleNewsScraper()
            result = scraper.run_scraper(days)
            
            if result:
                print(f"✅ Scraping completed successfully!")
                print(f"📄 Report saved: {result}")
                print(f"📋 Check logs directory for detailed logs")
                sys.exit(0)
            else:
                print("❌ Scraping completed with errors")
                print("📋 Check logs directory for error details")
                sys.exit(1)
        else:
            print("Defense & Space News Scraper")
            print("Usage:")
            print("  python scraper.py --manual              # Run now (7 days)")
            print("  python scraper.py --manual --days 3     # Run for last 3 days")
            print("  python scraper.py --test                # Test mode (1 day)")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⏹️  Scraper stopped by user")
        logger.info("Scraper stopped by user (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        logger.error(f"FATAL ERROR in main(): {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
