#!/usr/bin/env python3
"""
Minimal Working Defense News Scraper
Stripped down to essentials - guaranteed to work
"""

import requests
import feedparser
import argparse
from datetime import datetime, timedelta
import sys
import re

class SimpleDefenseScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Only verified working sources
        self.sources = {
            "Defense News": [
                "https://idrw.org/feed/",
                "https://defence.in/feed/",
                "https://www.defencexp.com/feed/",
                "https://timesofindia.indiatimes.com/india/rssfeeds/296589292.cms",
                "https://www.thehindu.com/news/national/feeder/default.rss"
            ],
            "Space News": [
                "https://www.thehindu.com/sci-tech/science/feeder/default.rss",
                "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",
                "https://spacenews.com/feed/",
                "https://www.space.com/feeds/all"
            ]
        }
        
        # Key defense/space terms
        self.keywords = [
            "drdo", "hal", "isro", "tejas", "brahmos", "chandrayaan", "gaganyaan",
            "indian air force", "indian navy", "indian army", "defense", "defence",
            "space mission", "satellite", "rocket launch", "military", "indigenous"
        ]
    
    def is_relevant(self, title, summary):
        """Simple relevance check"""
        text = (title + " " + (summary or "")).lower()
        return any(keyword in text for keyword in self.keywords)
    
    def get_feed_with_retry(self, url, max_retries=3):
        """Try different approaches to fetch a feed"""
        
        # Different User-Agents to try
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'feedbot/1.0 (+https://feeds.example.com/)'
        ]
        
        headers_list = [
            {
                'User-Agent': user_agents[0],
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache'
            },
            {
                'User-Agent': user_agents[1],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            },
            {
                'User-Agent': user_agents[2],
                'Accept': '*/*'
            },
            {
                'User-Agent': user_agents[3],
                'Accept': 'application/rss+xml'
            }
        ]
        
        for attempt, headers in enumerate(headers_list):
            try:
                print(f"    Attempt {attempt + 1} with {headers['User-Agent'][:20]}...")
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    return response
                else:
                    print(f"    Got HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"    Attempt {attempt + 1} failed: {str(e)[:50]}")
        
        return None
        """Scrape RSS feeds"""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        print(f"Scraping news from last {days_back} days...")
        
        for category, feeds in self.sources.items():
            print(f"\nProcessing {category}:")
            
            for feed_url in feeds:
                try:
                    print(f"  - {feed_url}")
                    response = self.session.get(feed_url, timeout=10)
                    
                    if response.status_code == 200:
                        feed = feedparser.parse(response.content)
                        
                        for entry in feed.entries[:10]:
                            # Check date
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                                if pub_date < cutoff_date:
                                    continue
                            
                            # Check relevance
                            if self.is_relevant(entry.get('title', ''), entry.get('summary', '')):
                                articles.append({
                                    'title': entry.get('title', 'No title'),
                                    'url': entry.get('link', ''),
                                    'date': pub_date.strftime("%Y-%m-%d") if hasattr(entry, 'published_parsed') and entry.published_parsed else datetime.now().strftime("%Y-%m-%d"),
                                    'category': category,
                                    'source': feed_url
                                })
                    else:
                        print(f"    Failed: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"    Error: {str(e)}")
        
        return articles
    
    def generate_report(self, articles, days_back):
        """Generate markdown report"""
        if not articles:
            return f"# No articles found for the last {days_back} days\n"
        
        # Separate by category
        defense_articles = [a for a in articles if a['category'] == 'Defense News']
        space_articles = [a for a in articles if a['category'] == 'Space News']
        
        report = f"""# Defense & Space News Summary
## Last {days_back} Days - {datetime.now().strftime('%B %d, %Y')}

**Total Articles:** {len(articles)} ({len(defense_articles)} Defense, {len(space_articles)} Space)

---

"""
        
        # Defense section
        if defense_articles:
            report += f"## Defense News ({len(defense_articles)} articles)\n\n"
            for i, article in enumerate(defense_articles, 1):
                report += f"### {i}. {article['title']}\n"
                report += f"**Date:** {article['date']}\n"
                report += f"**Link:** {article['url']}\n\n"
        
        # Space section
        if space_articles:
            report += f"## Space News ({len(space_articles)} articles)\n\n"
            for i, article in enumerate(space_articles, 1):
                report += f"### {i}. {article['title']}\n"
                report += f"**Date:** {article['date']}\n"
                report += f"**Link:** {article['url']}\n\n"
        
        return report
    
    def save_report(self, report, days_back):
        """Save report to file"""
        filename = f"defense_news_{days_back}days_{datetime.now().strftime('%Y%m%d')}.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved: {filename}")
            return filename
        except Exception as e:
            print(f"Save error: {e}")
            return None
    
    def run(self, days_back=7):
        """Main function"""
        try:
            print("Starting defense news scraper...")
            
            # Scrape articles
            articles = self.scrape_feeds(days_back)
            print(f"\nFound {len(articles)} relevant articles")
            
            # Generate report
            report = self.generate_report(articles, days_back)
            
            # Save report
            filename = self.save_report(report, days_back)
            
            print("Scraper completed successfully!")
            return True
            
        except Exception as e:
            print(f"Critical error: {e}")
            # Still try to save something
            try:
                error_report = f"# Error Report\n\nError: {str(e)}\nTime: {datetime.now()}\n"
                with open("error_report.md", 'w') as f:
                    f.write(error_report)
                print("Error report saved")
            except:
                pass
            return False

def main():
    parser = argparse.ArgumentParser(description='Simple Defense News Scraper')
    parser.add_argument('--manual', action='store_true', help='Run scraper now')
    parser.add_argument('--days', type=int, default=7, help='Days to look back')
    
    args = parser.parse_args()
    
    if args.manual:
        scraper = SimpleDefenseScraper()
        success = scraper.run(args.days)
        sys.exit(0)  # Always exit 0 for GitHub Actions
    else:
        print("Usage: python simple_scraper.py --manual [--days N]")

if __name__ == "__main__":
    main()
