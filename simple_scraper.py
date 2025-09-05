#!/usr/bin/env python3
"""
Simple Defense News Scraper
Just extracts articles with links, full text, and dates
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import schedule
import time
import argparse
from datetime import datetime, timedelta
import json
import re

class SimpleNewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # News sources with RSS feeds
        self.sources = {
            "Defense News": [
                "https://idrw.org/feed/",
                "https://defence.in/feed/",
                "https://www.indiandefensenews.in/feed/"
            ],
            "Space News": [
                "https://www.isro.gov.in/rss.xml"
            ]
        }
        
        # Keywords to filter relevant articles
        self.keywords = [
            "india", "indian", "defense", "defence", "space", "isro", "hal", "drdo",
            "private", "contract", "deal", "startup", "investment", "manufacturing"
        ]
    
    def extract_full_article(self, url):
        """Extract full article text from URL"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return "Could not fetch article content"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                               'aside', 'advertisement', '.ad', '.ads']):
                element.decompose()
            
            # Try to find main content
            content_selectors = [
                'article', '.article-content', '.post-content', '.entry-content',
                '.content', 'main', '.main', '.story', '.article-body'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator='\n', strip=True)
                    break
            
            if not content:
                # Fallback to body content
                body = soup.find('body')
                if body:
                    content = body.get_text(separator='\n', strip=True)
            
            # Clean up the text
            content = self.clean_text(content)
            return content
            
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    def clean_text(self, text):
        """Clean and format text"""
        # Remove extra whitespace
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'(Advertisement|Subscribe|Read More|Continue Reading).*',
            r'Share.*?(Facebook|Twitter|LinkedIn).*',
            r'Follow us on.*',
            r'Also Read:.*',
            r'Related:.*'
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def is_relevant_article(self, title, content):
        """Check if article is relevant to defense/space"""
        text = (title + " " + content).lower()
        return any(keyword in text for keyword in self.keywords)
    
    def parse_date(self, date_string):
        """Parse various date formats to standard format"""
        if not date_string:
            return datetime.now().strftime("%d %B %Y")
        
        try:
            # Try different date parsing approaches
            if hasattr(date_string, 'timetuple'):
                # feedparser date object
                return datetime(*date_string.timetuple()[:6]).strftime("%d %B %Y")
            elif isinstance(date_string, str):
                # Try to parse string date
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(date_string, fmt).strftime("%d %B %Y")
                    except ValueError:
                        continue
        except:
            pass
        
        return datetime.now().strftime("%d %B %Y")
    
    def scrape_rss_feeds(self):
        """Scrape all RSS feeds"""
        articles = []
        
        for category, feeds in self.sources.items():
            print(f"Scraping {category} sources...")
            
            for feed_url in feeds:
                try:
                    print(f"  - {feed_url}")
                    response = self.session.get(feed_url, timeout=10)
                    
                    if response.status_code == 200:
                        feed = feedparser.parse(response.content)
                        
                        for entry in feed.entries[:10]:  # Latest 10 articles
                            # Check if article is from last 7 days
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                                if (datetime.now() - pub_date).days > 7:
                                    continue
                            
                            # Basic relevance check
                            if self.is_relevant_article(entry.title, entry.get('summary', '')):
                                
                                # Extract full article content
                                print(f"    Extracting: {entry.title[:50]}...")
                                full_content = self.extract_full_article(entry.link)
                                
                                # Parse publication date
                                pub_date = self.parse_date(entry.get('published_parsed'))
                                
                                article = {
                                    'title': entry.title,
                                    'url': entry.link,
                                    'content': full_content,
                                    'date': pub_date,
                                    'source': feed_url,
                                    'category': category
                                }
                                
                                articles.append(article)
                                
                except Exception as e:
                    print(f"    Error scraping {feed_url}: {e}")
        
        return articles
    
    def generate_simple_report(self, articles):
        """Generate simple markdown report"""
        if not articles:
            return "No articles found this week."
        
        report = f"""# Defense & Space News Summary
## Week of {datetime.now().strftime('%B %d, %Y')}

Total Articles: {len(articles)}

---

"""
        
    def generate_simple_report(self, articles, days_back):
        """Generate enhanced markdown report with separate defense and space sections"""
        if not articles:
            return f"No articles found for the last {days_back} days."
        
        # Separate articles by category
        defense_articles = [a for a in articles if a['category'] == 'Defense News']
        space_articles = [a for a in articles if a['category'] == 'Space News']
        
        period_text = f"last {days_back} day{'s' if days_back != 1 else ''}"
        report = f"""# Defense & Space News Summary
## {period_text.title()} - Generated on {datetime.now().strftime('%B %d, %Y')}

**Total Articles:** {len(articles)} ({len(defense_articles)} Defense, {len(space_articles)} Space)

---

"""
        
        # Defense section
        if defense_articles:
            report += f"## 🛡️ DEFENSE SECTOR NEWS ({len(defense_articles)} articles)\n\n"
            for i, article in enumerate(defense_articles, 1):
                report += f"""### {i}. {article['title']}

**Date:** {article['date']}
**Link:** {article['url']}
**Source:** {article['source']}

**Full Article Text:**
{article['content']}

---

"""
        
        # Space section
        if space_articles:
            report += f"## 🚀 SPACE SECTOR NEWS ({len(space_articles)} articles)\n\n"
            for i, article in enumerate(space_articles, 1):
                report += f"""### {i}. {article['title']}

**Date:** {article['date']}
**Link:** {article['url']}
**Source:** {article['source']}

**Full Article Text:**
{article['content']}

---

"""
        
        # Add summary of companies mentioned
        report += self.generate_company_summary(articles)
        
        return report
    
    def generate_company_summary(self, articles):
        """Generate a summary of companies mentioned across all articles"""
        
        # Key companies to track
        defense_companies = [
            "HAL", "Hindustan Aeronautics", "DRDO", "BEL", "BHEL", "Tata Advanced Systems",
            "TASL", "L&T", "Larsen & Toubro", "Mahindra Defense", "Kalyani Group", 
            "Bharat Forge", "Reliance Defence", "Adani Defence"
        ]
        
        space_companies = [
            "ISRO", "Skyroot", "Agnikul", "Pixxel", "Bellatrix", "Dhruva Space",
            "Astrome", "Antrix", "NSIL", "Kawa Space", "Satellogic India"
        ]
        
        mentioned_defense = set()
        mentioned_space = set()
        
        for article in articles:
            text = (article['title'] + " " + article['content']).lower()
            
            for company in defense_companies:
                if company.lower() in text:
                    mentioned_defense.add(company)
            
            for company in space_companies:
                if company.lower() in text:
                    mentioned_space.add(company)
        
        summary = "\n## 📊 COMPANIES MENTIONED THIS PERIOD\n\n"
        
        if mentioned_defense:
            summary += f"**Defense Companies:** {', '.join(sorted(mentioned_defense))}\n\n"
        
        if mentioned_space:
            summary += f"**Space Companies:** {', '.join(sorted(mentioned_space))}\n\n"
        
        if not mentioned_defense and not mentioned_space:
            summary += "No major defense or space companies specifically mentioned.\n\n"
        
        return summary
    
    def save_report(self, report):
        """Save report to file"""
        filename = f"defense_news_{datetime.now().strftime('%Y%m%d')}.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving report: {e}")
            return None
    
    def run_scraper(self):
        """Main scraping function"""
        print("Starting defense & space news scraping...")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Scrape articles
        articles = self.scrape_rss_feeds()
        
        if not articles:
            print("No relevant articles found.")
            return
        
        print(f"Found {len(articles)} relevant articles")
        
        # Generate report
        report = self.generate_simple_report(articles)
        
        # Save report
        filename = self.save_report(report)
        
        print("Scraping complete!")
        if filename:
            print(f"Open {filename} to view the results")

def run_manual():
    """Run scraper manually"""
    scraper = SimpleNewsScraper()
    scraper.run_scraper()

def run_scheduled():
    """Run scraper on schedule with default 7-day period"""
    scraper = SimpleNewsScraper()
    
    # Schedule for every Monday at 9 AM
    schedule.every().monday.at("09:00").do(scraper.run_scraper, 7)
    
    print("Scheduler started. Will run every Monday at 9:00 AM")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nScheduler stopped")

def main():
    parser = argparse.ArgumentParser(description='Simple Defense News Scraper')
    parser.add_argument('--manual', action='store_true', help='Run scraper now (with time selection)')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled scraper (weekly)')
    parser.add_argument('--days', type=int, help='Number of days to look back (1-30)', default=7)
    
    args = parser.parse_args()
    
    if args.manual:
        if args.days:
            # Command line specified days
            if 1 <= args.days <= 30:
                scraper = SimpleNewsScraper()
                scraper.run_scraper(args.days)
            else:
                print("Days must be between 1 and 30")
        else:
            # Interactive mode
            run_manual()
    elif args.schedule:
        run_scheduled()
    else:
        print("Usage:")
        print("  python simple_scraper.py --manual              # Run now (interactive)")
        print("  python simple_scraper.py --manual --days 3     # Run for last 3 days")
        print("  python simple_scraper.py --schedule            # Run weekly")

if __name__ == "__main__":
    main()
