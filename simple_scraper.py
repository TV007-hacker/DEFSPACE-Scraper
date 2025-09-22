#!/usr/bin/env python3
"""
Simple Defense News Scraper - ERROR FREE VERSION
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
        
        # UPDATED - Enhanced news sources with VERIFIED working RSS feeds
        self.sources = {
            "Defense News": [
                "https://www.livefistdefence.com/feed/",           # Most reliable Indian defense blog
                "https://defence.in/feed/",                       # Active defense forum
                "https://stratpost.com/feed/",                    # Strategic affairs
                "https://forceindia.net/feed/",                   # FORCE Magazine
                "https://www.indiandefensenews.in/feeds/posts/default?alt=rss",  # Indian Defense News
                "https://www.ajaishukla.com/feeds/posts/default?alt=rss",  # Broadsword blog
                "https://theigmp.org/feeds/posts/default",        # India's Growing Military Power
                "https://idrw.org/feed/",                         # IDRW (backup - can be slow)
            ],
            "Space News": [
                "https://spacenews.com/feed/",                    # Leading space industry news
                "https://www.space.com/feeds/all",                # Popular space news
                "https://spaceflightnow.com/feed/",               # Launch coverage
                "https://www.thehindu.com/sci-tech/science/feeder/default.rss",  # Hindu Science
                "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",    # TOI Science
                "https://economictimes.indiatimes.com/industry/aerospace/defence/rssfeeds/13352306.cms",  # ET Aerospace
                "https://www.universetoday.com/feed/",            # Universe Today
                "https://phys.org/rss-feed/space-news/",          # Physics.org space
            ]
        }
        
        # UPDATED - Enhanced keywords to filter relevant articles
        self.defense_keywords = [
            # Core Indian Defense
            "india", "indian", "defense", "defence", "military", "armed forces",
            "indian air force", "iaf", "indian army", "indian navy", "coast guard",
            
            # Defense Organizations & Companies
            "hal", "hindustan aeronautics", "drdo", "defence research", "bel", "bhel",
            "tata advanced systems", "tasl", "l&t", "larsen toubro", "mahindra defense",
            "kalyani group", "bharat forge", "reliance defence", "adani defence",
            "godrej aerospace", "bharat dynamics", "bdl", "ordnance factory",
            "private", "contract", "deal", "startup", "investment", "manufacturing",
            
            # Indigenous Programs & Concepts
            "atmanirbhar", "make in india", "indigenous", "domestic", "self reliance",
            "strategic partnership", "defense export", "defense import", "technology transfer",
            "joint venture", "fdi in defense", "defense corridor", "defense manufacturing",
            
            # Key Platforms & Weapons
            "tejas", "lca", "light combat aircraft", "brahmos", "akash", "nag", "helina",
            "agni", "prithvi", "pinaka", "arjun", "bhishma", "k9 vajra", "dhanush",
            "apache", "chinook", "rafale", "sukhoi", "mig", "jaguar", "mirage",
            "dhruv", "rudra", "prachand", "sarang",
            
            # Naval Platforms
            "ins vikrant", "ins vikramaditya", "ins arihant", "ins chakra",
            "indigenous aircraft carrier", "nuclear submarine", "stealth frigate",
            "destroyer", "corvette", "patrol vessel", "fast attack craft",
            
            # Operations & Strategy
            "border", "lac", "line of control", "loc", "ceasefire", "violation",
            "infiltration", "counter terrorism", "surgical strike", "air strike",
            "exercise", "drill", "training", "joint exercise", "war game",
            "deployment", "strategic", "tactical", "surveillance", "reconnaissance",
            
            # Budget & Policy
            "defense budget", "capital acquisition", "modernization", "procurement",
            "tender", "rfp", "trial", "test", "evaluation", "induction"
        ]
        
        self.space_keywords = [
            # ISRO & Indian Space Program
            "isro", "indian space research", "indian space", "space program", "space programme",
            "shar", "sriharikota", "thumba", "vssc", "lpsc", "isac", "sac",
            "space", "satellite", "launch", "rocket", "mission", "orbit", "spacecraft",
            
            # Major Missions
            "chandrayaan", "mangalyaan", "gaganyaan", "aditya", "astrosat",
            "cartosat", "resourcesat", "oceansat", "risat", "microsat", "nanosat",
            
            # Launch Vehicles
            "pslv", "gslv", "sslv", "mk3", "mk2", "cryogenic", "semi cryogenic",
            "scramjet", "ramjet", "solid motor", "liquid engine",
            
            # Commercial Space & Policy
            "antrix", "nsil", "newspace india", "in-space", "commercial space",
            "space policy", "space reform", "private space", "space startup",
            "space sector", "space economy", "space industry", "space business",
            
            # Indian Space Startups
            "skyroot", "skyroot aerospace", "agnikul", "agnikul cosmos", "pixxel",
            "bellatrix", "bellatrix aerospace", "dhruva space", "astrome",
            "kawa space", "momentus india", "satellogic india", "team indus",
            "digantara", "galaxeye", "satsure", "spire global india",
            
            # Space Applications
            "earth observation", "remote sensing", "gis", "mapping", "cartography",
            "communication satellite", "broadcasting", "dtv", "vsat", "satcom",
            "navigation", "positioning", "irnss", "navic", "gps", "glonass",
            "weather satellite", "meteorology", "climate monitoring", "disaster management",
            
            # Space Technology & Science
            "propulsion", "thruster", "ion drive", "hall thruster", "electric propulsion",
            "avionics", "guidance", "navigation", "control", "telemetry", "tracking",
            "ground station", "mission control", "launch pad", "vehicle assembly",
            "payload", "fairing", "stage", "booster", "upper stage", "reusable",
            "constellation", "formation flying", "rendezvous", "docking",
            "space debris", "collision avoidance", "space situational awareness",
            "interplanetary", "deep space", "lunar", "mars", "planetary", "astronomy"
        ]
        
        self.keywords = self.defense_keywords + self.space_keywords
    
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
        """Enhanced relevance check for defense/space articles"""
        text = (title + " " + content).lower()
        
        # Higher priority for space content
        space_priority_keywords = [
            "isro", "indian space", "space mission", "satellite launch", "rocket",
            "skyroot", "agnikul", "pixxel", "private space", "space startup",
            "chandrayaan", "gaganyaan", "mangalyaan", "space policy"
        ]
        
        # Check for high-priority space content
        if any(keyword in text for keyword in space_priority_keywords):
            return True
        
        # Check for defense content
        defense_priority_keywords = [
            "hal", "drdo", "defense contract", "indigenous", "atmanirbhar",
            "tejas", "brahmos", "private defense", "defense startup"
        ]
        
        if any(keyword in text for keyword in defense_priority_keywords):
            return True
        
        # General relevance check
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
    
    def add_google_news_search(self, days_back=7):
        """Add Google News search for Indian space developments"""
        articles = []
        
        # Specific search terms for Indian space news
        search_terms = [
            "ISRO mission launch India",
            "Indian space startup funding",
            "Skyroot Aerospace India",
            "Agnikul Cosmos India", 
            "Pixxel satellite India"
        ]
        
        print("Searching Google News for Indian space developments...")
        
        for term in search_terms[:3]:  # Limit searches to avoid rate limiting
            try:
                # Simple Google News RSS search
                encoded_term = term.replace(" ", "+")
                search_url = f"https://news.google.com/rss/search?q={encoded_term}+india&hl=en-IN&gl=IN&ceid=IN:en"
                
                response = self.session.get(search_url, timeout=10)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries[:2]:  # Top 2 results per search
                        # Check date
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                            cutoff_date = datetime.now() - timedelta(days=days_back)
                            if pub_date < cutoff_date:
                                continue
                        
                        # Check relevance
                        if self.is_relevant_article(entry.title, entry.get('summary', '')):
                            print(f"    Found: {entry.title[:60]}...")
                            
                            # Extract full content
                            full_content = self.extract_full_article(entry.link)
                            
                            article = {
                                'title': entry.title,
                                'url': entry.link,
                                'content': full_content,
                                'date': self.parse_date(entry.get('published_parsed')),
                                'source': 'Google News Search',
                                'category': 'Space News' if any(kw in entry.title.lower() for kw in self.space_keywords) else 'Defense News'
                            }
                            
                            articles.append(article)
                            
            except Exception as e:
                print(f"    Error searching for '{term}': {e}")
        
        return articles
    
    def remove_duplicates(self, articles):
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Simple deduplication based on title
            title_key = re.sub(r'[^\w\s]', '', article['title'].lower())
            title_key = ' '.join(title_key.split()[:5])  # First 5 words
            
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        return unique_articles
    
    def scrape_rss_feeds(self, days_back=7):
        """Scrape all RSS feeds for articles from specified number of days"""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        print(f"Looking for articles from the last {days_back} days (since {cutoff_date.strftime('%Y-%m-%d')})")
        
        for category, feeds in self.sources.items():
            print(f"Scraping {category} sources...")
            
            for feed_url in feeds:
                try:
                    print(f"  - {feed_url}")
                    response = self.session.get(feed_url, timeout=10)
                    
                    if response.status_code == 200:
                        feed = feedparser.parse(response.content)
                        
                        for entry in feed.entries[:15]:  # Check more articles
                            # Check if article is within specified timeframe
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                                if pub_date < cutoff_date:
                                    continue
                            
                            # Enhanced relevance check
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
        
        # Add Google News search results for space content
        try:
            google_articles = self.add_google_news_search(days_back)
            articles.extend(google_articles)
        except Exception as e:
            print(f"Error in Google News search: {e}")
        
        # Remove duplicates based on title similarity
        articles = self.remove_duplicates(articles)
        
        return articles
    
    def generate_company_summary(self, articles):
        """Generate a summary of companies mentioned across all articles"""
        
        # UPDATED - Key companies to track
        defense_companies = [
            "HAL", "Hindustan Aeronautics", "DRDO", "BEL", "Bharat Electronics",
            "BHEL", "Bharat Heavy Electricals", "Tata Advanced Systems",
            "TASL", "L&T", "Larsen & Toubro", "Mahindra Defense", "Kalyani Group", 
            "Bharat Forge", "Reliance Defence", "Adani Defence", "Godrej Aerospace",
            "Bharat Dynamics", "BDL", "Ordnance Factory", "GRSE", "MDL", "CSL",
            "Alpha Design Technologies", "Dynamatic Technologies", "Zen Technologies",
            "Solar Industries", "Premier Explosives"
        ]
        
        space_companies = [
            "ISRO", "Indian Space Research Organisation", "Skyroot", "Skyroot Aerospace",
            "Agnikul", "Agnikul Cosmos", "Pixxel", "Bellatrix", "Bellatrix Aerospace",
            "Dhruva Space", "Astrome", "Astrome Technologies", "Antrix", "NSIL",
            "NewSpace India", "Kawa Space", "Satellogic India", "Momentus India",
            "Digantara", "GalaxEye", "SatSure", "Spire Global India"
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
    
    def save_report(self, report, days_back=7):
        """Save report to file"""
        filename = f"defense_news_{days_back}days_{datetime.now().strftime('%Y%m%d')}.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving report: {e}")
            return None
    
    def run_scraper(self, days_back=7):
        """Main scraping function - FIXED VERSION"""
        print("Starting defense & space news scraping...")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Looking for articles from the last {days_back} days")
        
        # Scrape articles
        articles = self.scrape_rss_feeds(days_back)
        
        if not articles:
            print(f"No relevant articles found for the last {days_back} days.")
            return
        
        print(f"Found {len(articles)} relevant articles")
        
        # Generate report
        report = self.generate_simple_report(articles, days_back)
        
        # Save report
        filename = self.save_report(report, days_back)
        
        print("Scraping complete!")
        if filename:
            print(f"Open {filename} to view the results")

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
        # Create scraper instance
        scraper = SimpleNewsScraper()
        
        if args.days and 1 <= args.days <= 30:
            # Use command line specified days
            scraper.run_scraper(args.days)
        else:
            # Use default 7 days
            scraper.run_scraper(7)
            
    elif args.schedule:
        run_scheduled()
    else:
        print("Usage:")
        print("  python simple_scraper.py --manual              # Run now (7 days default)")
        print("  python simple_scraper.py --manual --days 3     # Run for last 3 days")
        print("  python simple_scraper.py --schedule            # Run weekly")

if __name__ == "__main__":
    main()
