#!/usr/bin/env python3
"""
Enhanced Defense News Scraper - Improved Keyword Filtering
Fixed keyword matching to reduce false positives
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

class EnhancedNewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Enhanced news sources with RSS feeds including popular news websites
        self.sources = {
            "Defense News": [
                # Specialized Defense Sources
                "https://idrw.org/feed/",
                "https://defence.in/feed/",
                "https://www.indiandefensenews.in/feed/",
                "https://www.defencexp.com/feed/",
                # Popular News Websites - Defense Sections
                "https://timesofindia.indiatimes.com/india/rssfeeds/296589292.cms",  # TOI India News
                "https://www.thehindu.com/news/national/feeder/default.rss",  # The Hindu National
                "https://indianexpress.com/section/india/feed/",  # Indian Express India
                "https://www.ndtv.com/india-news/rss",  # NDTV India
                "https://www.hindustantimes.com/rss/india-news/rssfeed.xml",  # HT India News
                "https://www.news18.com/rss/india.xml",  # News18 India
                "https://www.dnaindia.com/feeds/india.xml",  # DNA India
                "https://zeenews.india.com/rss/india-national-news.xml",  # Zee News India
                "https://www.business-standard.com/rss/current-affairs-106.rss"  # BS Current Affairs
            ],
            "Space News": [
                # Space Specific Sources
                "https://www.isro.gov.in/rss.xml",
                "https://ispa.space/feed/",
                # Popular News Websites - Science/Tech Sections
                "https://www.thehindu.com/sci-tech/science/feeder/default.rss",  # The Hindu Science
                "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",  # TOI Science
                "https://indianexpress.com/section/technology/science/feed/",  # IE Science
                "https://www.ndtv.com/science-news/rss",  # NDTV Science
                "https://www.hindustantimes.com/rss/science/rssfeed.xml",  # HT Science
                "https://www.news18.com/rss/tech.xml",  # News18 Tech
                "https://economictimes.indiatimes.com/industry/aerospace/defence/rssfeeds/13352306.cms",  # ET Aerospace
                "https://www.livemint.com/rss/technology",  # Mint Technology
                "https://zeenews.india.com/rss/technology-news.xml",  # Zee Tech
                # International Space News (for context)
                "https://www.space.com/feeds/all",  # Space.com
                "https://spaceflightnow.com/feed/"  # Spaceflight Now
            ]
        }
        
        # High-priority exact match keywords (guaranteed relevance)
        self.high_priority_defense = [
            "drdo", "hal", "hindustan aeronautics", "bel", "bhel", "ordnance factory",
            "indian air force", "indian army", "indian navy", "coast guard",
            "tejas", "brahmos", "agni", "prithvi", "akash", "nag missile",
            "pinaka", "indigenous aircraft carrier", "ins vikrant", "ins arihant",
            "light combat aircraft", "advanced medium combat aircraft", "amca",
            "defence research", "military exercise", "surgical strike",
            "border security force", "central reserve police", "itbp",
            "defense procurement", "defense contract", "defense manufacturing",
            "atmanirbhar defense", "make in india defense", "defense export",
            "military modernization", "fighter aircraft", "combat helicopter",
            "naval ship", "submarine", "missile defense", "radar system",
            "electronic warfare", "cyber warfare", "military satellite"
        ]
        
        self.high_priority_space = [
            "isro", "indian space research", "chandrayaan", "mangalyaan", "gaganyaan",
            "pslv", "gslv", "sslv", "rocket launch", "satellite launch",
            "space mission", "lunar mission", "mars mission", "venus mission",
            "earth observation", "communication satellite", "navigation satellite",
            "space technology", "space exploration", "orbital mission",
            "space station", "space program", "space policy", "space sector",
            "space startup", "commercial space", "space economy",
            "antrix", "nsil", "newspace india", "in-space",
            "skyroot", "agnikul", "pixxel", "bellatrix", "dhruva space",
            "space applications centre", "vikram sarabhai", "space centre",
            "satellite constellation", "remote sensing", "space research"
        ]
        
        # Secondary keywords that need context
        self.defense_keywords = [
            "defense", "defence", "military", "armed forces", "security forces",
            "border security", "national security", "homeland security",
            "peacekeeping", "counter-terrorism", "anti-terrorism",
            "strategic partnership", "defense cooperation", "military cooperation",
            "joint exercise", "bilateral exercise", "war game", "training exercise",
            "modernization", "procurement", "acquisition", "indigenous",
            "self-reliance", "strategic autonomy", "geopolitical",
            "warfare", "combat", "operational", "tactical", "strategic",
            "intelligence", "surveillance", "reconnaissance",
            "armament", "weaponry", "munitions", "ordinance",
            "fleet", "squadron", "regiment", "battalion", "brigade",
            "command", "headquarters", "base", "cantonment",
            "veteran", "soldier", "officer", "personnel", "deployment",
            "maritime security", "coastal security", "airspace",
            "line of control", "line of actual control", "ceasefire",
            "cross-border", "infiltration", "escalation", "deterrence"
        ]
        
        self.space_keywords = [
            "space", "satellite", "launch", "rocket", "mission", "orbit",
            "spacecraft", "probe", "lander", "rover", "orbiter",
            "astronaut", "cosmonaut", "space flight", "space travel",
            "launch vehicle", "propulsion", "engine", "fuel", "payload",
            "trajectory", "orbital", "interplanetary", "lunar", "planetary",
            "astronomy", "astrophysics", "space science", "cosmology",
            "telescope", "observatory", "space weather", "solar",
            "constellation", "network", "communication", "navigation",
            "positioning", "tracking", "monitoring", "imaging",
            "data", "signal", "transmission", "ground station",
            "mission control", "launch pad", "spaceport", "facility",
            "technology transfer", "commercial", "private sector",
            "startup", "innovation", "research", "development",
            "international", "collaboration", "partnership", "agreement"
        ]
        
        # Exclusion keywords to filter out unrelated content
        self.exclusion_keywords = [
            "bollywood", "hollywood", "cinema", "movie", "film", "actor", "actress",
            "cricket", "football", "sports", "match", "tournament", "player",
            "recipe", "cooking", "food", "restaurant", "cuisine", "chef",
            "entertainment", "music", "concert", "show", "performance",
            "festival", "celebration", "wedding", "marriage", "ceremony",
            "stock market", "share price", "trading", "investment banking",
            "real estate", "property", "housing", "construction",
            "agriculture", "farming", "crop", "harvest", "farmer",
            "education", "school", "college", "university", "student",
            "healthcare", "hospital", "doctor", "patient", "treatment",
            "politics", "election", "voting", "campaign", "politician",
            "economics", "gdp", "inflation", "budget", "finance minister",
            "tourism", "travel", "vacation", "holiday", "destination",
            "weather", "climate", "rain", "temperature", "season"
        ]
        
        self.all_keywords = self.high_priority_defense + self.high_priority_space + self.defense_keywords + self.space_keywords
    
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
        """Enhanced relevance check with better filtering"""
        text = (title + " " + content).lower()
        
        # First, check for exclusion keywords
        if any(excl_keyword in text for excl_keyword in self.exclusion_keywords):
            return False
        
        # Check for high-priority exact matches (guaranteed relevance)
        for keyword in self.high_priority_defense + self.high_priority_space:
            if keyword in text:
                return True
        
        # For general keywords, require multiple matches to reduce false positives
        defense_matches = sum(1 for kw in self.defense_keywords if kw in text)
        space_matches = sum(1 for kw in self.space_keywords if kw in text)
        
        # Require at least 2 keyword matches for general terms
        total_matches = defense_matches + space_matches
        
        # Additional context checks for borderline cases
        if total_matches >= 2:
            # Ensure it's actually about defense/space, not just mentioning terms
            defense_context = any(term in text for term in [
                "military", "defense", "defence", "armed forces", "security",
                "missile", "aircraft", "naval", "army", "air force"
            ])
            
            space_context = any(term in text for term in [
                "space", "satellite", "launch", "rocket", "mission", "isro",
                "orbital", "astronaut", "spacecraft"
            ])
            
            return defense_context or space_context
        
        return False
    
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
        
        # More specific search terms for better relevance
        search_terms = [
            "ISRO mission launch India",
            "Indian defense procurement contract",
            "HAL Tejas fighter aircraft India",
            "DRDO missile test India",
            "Indian space startup funding",
            "Skyroot Aerospace India launch",
            "Agnikul Cosmos India rocket"
        ]
        
        print("Searching Google News for defense and space developments...")
        
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
                        
                        # Check relevance with enhanced filtering
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
                                'category': 'Space News' if any(kw in entry.title.lower() for kw in self.high_priority_space + ['space', 'satellite', 'launch', 'rocket']) else 'Defense News'
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
        
        # Add Google News search results
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
        
        # Enhanced company lists
        defense_companies = [
            "HAL", "Hindustan Aeronautics Limited", "DRDO", "BEL", "Bharat Electronics",
            "BHEL", "Bharat Heavy Electricals", "Tata Advanced Systems", "TASL", 
            "L&T", "Larsen & Toubro", "Mahindra Defense", "Mahindra Defence",
            "Kalyani Group", "Bharat Forge", "Reliance Defence", "Adani Defence",
            "Godrej Aerospace", "Bharat Dynamics Limited", "BDL", "Ordnance Factory",
            "Hindustan Shipyard", "Garden Reach Shipbuilders", "GRSE",
            "Mazagon Dock Shipbuilders", "MDL", "Cochin Shipyard", "CSL",
            "Bharat Earth Movers Limited", "BEML", "Mishra Dhatu Nigam", "MIDHANI"
        ]
        
        space_companies = [
            "ISRO", "Indian Space Research Organisation", "Skyroot Aerospace", "Skyroot",
            "Agnikul Cosmos", "Agnikul", "Pixxel", "Bellatrix Aerospace", "Bellatrix",
            "Dhruva Space", "Astrome Technologies", "Astrome", "Antrix Corporation",
            "Antrix", "NSIL", "NewSpace India Limited", "Kawa Space", "Momentus India",
            "Satellogic India", "Team Indus", "Xpressbees", "IN-SPACe",
            "Vikram Sarabhai Space Centre", "VSSC", "Liquid Propulsion Systems Centre",
            "LPSC", "ISRO Satellite Centre", "ISAC", "Space Applications Centre", "SAC"
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
        """Main scraping function - Enhanced version"""
        print("Starting enhanced defense & space news scraping...")
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
    scraper = EnhancedNewsScraper()
    
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
    parser = argparse.ArgumentParser(description='Enhanced Defense News Scraper')
    parser.add_argument('--manual', action='store_true', help='Run scraper now (with time selection)')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled scraper (weekly)')
    parser.add_argument('--days', type=int, help='Number of days to look back (1-30)', default=7)
    
    args = parser.parse_args()
    
    if args.manual:
        # Create scraper instance
        scraper = EnhancedNewsScraper()
        
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
        print("  python enhanced_scraper.py --manual              # Run now (7 days default)")
        print("  python enhanced_scraper.py --manual --days 3     # Run for last 3 days")
        print("  python enhanced_scraper.py --schedule            # Run weekly")

if __name__ == "__main__":
    main()
