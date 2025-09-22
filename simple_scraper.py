#!/usr/bin/env python3
"""
Robust Defense News Scraper - Error-Free Version for GitHub Actions
Includes comprehensive error handling and fallback mechanisms
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
import sys
import logging
from urllib.parse import urljoin
import warnings

# Suppress warnings to keep output clean
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class RobustNewsScraper:
    def __init__(self):
        self.session = requests.Session()
        
        # Rotate User-Agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
        ]
        
        self.current_ua_index = 0
        self.update_user_agent()
        
        # Set timeouts and retries
        self.session.timeout = 15
        
        # Enhanced news sources with RSS feeds including popular news websites
        self.sources = {
            "Defense News": [
                # Specialized Defense Sources (Working)
                "https://defence.in/feed/",
                "https://www.defencexp.com/feed/",
                # Alternative Defense Sources (To replace failed ones)
                "https://www.defensenews.com/rss/",
                "https://www.janes.com/feeds/defence-news",
                "https://www.forceindia.net/rss.xml",
                "https://www.livefistdefence.com/feeds/posts/default",
                # Popular News Websites - Defense Sections
                "https://timesofindia.indiatimes.com/india/rssfeeds/296589292.cms",
                "https://www.thehindu.com/news/national/feeder/default.rss",
                "https://indianexpress.com/section/india/feed/",
                "https://www.hindustantimes.com/rss/india-news/rssfeed.xml",
                "https://www.news18.com/rss/india.xml",
                "https://zeenews.india.com/rss/india-national-news.xml",
                # Business/Defense Economics
                "https://economictimes.indiatimes.com/defence/rssfeeds/50355294.cms",
                "https://www.business-standard.com/rss/current-affairs-106.rss"
            ],
            "Space News": [
                # Alternative Space Sources (To replace failed ISRO/ISPA)
                "https://spacenews.com/feed/",
                "https://spaceflightnow.com/feed/",
                "https://www.space.com/feeds/all",
                "https://www.spacedaily.com/spacedaily.xml",
                # Indian Space Coverage via News Sites
                "https://www.thehindu.com/sci-tech/science/feeder/default.rss",
                "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",
                "https://indianexpress.com/section/technology/science/feed/",
                "https://economictimes.indiatimes.com/industry/aerospace/defence/rssfeeds/13352306.cms",
                "https://zeenews.india.com/rss/technology-news.xml",
                "https://www.livemint.com/rss/technology",
                # Business/Space Economics
                "https://economictimes.indiatimes.com/tech/technology/rssfeeds/13357270.cms"
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
        
        # Statistics tracking
        self.stats = {
            'total_feeds_processed': 0,
            'successful_feeds': 0,
            'failed_feeds': 0,
            'total_articles_found': 0,
            'relevant_articles': 0,
            'errors': []
        }
    
    def update_user_agent(self):
        """Rotate User-Agent to avoid blocking"""
        self.session.headers.update({
            'User-Agent': self.user_agents[self.current_ua_index],
            'Accept': 'application/rss+xml, application/xml, text/xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
    
    def safe_request(self, url, timeout=15, max_retries=3):
        """Make a safe HTTP request with retries, User-Agent rotation, and error handling"""
        for attempt in range(max_retries):
            try:
                # Rotate User-Agent for each attempt
                if attempt > 0:
                    self.update_user_agent()
                    time.sleep(2)  # Brief delay between retries
                
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout:
                logging.warning(f"Timeout for {url} (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    self.stats['errors'].append(f"Timeout: {url}")
                    return None
            except requests.exceptions.ConnectionError:
                logging.warning(f"Connection error for {url} (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    self.stats['errors'].append(f"Connection error: {url}")
                    return None
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [403, 404, 429]:
                    logging.warning(f"HTTP {e.response.status_code} for {url} (attempt {attempt + 1}/{max_retries})")
                    if attempt == max_retries - 1:
                        self.stats['errors'].append(f"HTTP {e.response.status_code}: {url}")
                        return None
                else:
                    logging.error(f"HTTP error for {url}: {str(e)}")
                    self.stats['errors'].append(f"HTTP error {url}: {str(e)}")
                    return None
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request error for {url}: {str(e)}")
                self.stats['errors'].append(f"Request error {url}: {str(e)}")
                return None
            except Exception as e:
                logging.error(f"Unexpected error for {url}: {str(e)}")
                self.stats['errors'].append(f"Unexpected error {url}: {str(e)}")
                return None
        return None
    
    def extract_full_article(self, url):
        """Extract full article text from URL with error handling"""
        try:
            response = self.safe_request(url, timeout=10)
            if not response:
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
            return content if content else "No content extracted"
            
        except Exception as e:
            logging.error(f"Error extracting content from {url}: {str(e)}")
            return f"Error extracting content: {str(e)}"
    
    def clean_text(self, text):
        """Clean and format text"""
        if not text:
            return ""
            
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
        if not title and not content:
            return False
            
        text = (str(title) + " " + str(content)).lower()
        
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
        except Exception as e:
            logging.warning(f"Date parsing error: {str(e)}")
        
        return datetime.now().strftime("%d %B %Y")
    
    def scrape_rss_feeds(self, days_back=7):
        """Scrape all RSS feeds for articles from specified number of days"""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        logging.info(f"Looking for articles from the last {days_back} days (since {cutoff_date.strftime('%Y-%m-%d')})")
        
        # Track failed URLs for alternative sourcing
        failed_urls = []
        
        for category, feeds in self.sources.items():
            logging.info(f"Scraping {category} sources...")
            
            for feed_url in feeds:
                self.stats['total_feeds_processed'] += 1
                
                try:
                    logging.info(f"  - Processing: {feed_url}")
                    response = self.safe_request(feed_url)
                    
                    if not response:
                        self.stats['failed_feeds'] += 1
                        failed_urls.append(feed_url)
                        continue
                    
                    try:
                        feed = feedparser.parse(response.content)
                        self.stats['successful_feeds'] += 1
                        
                        if not feed.entries:
                            logging.warning(f"    No entries found in feed: {feed_url}")
                            continue
                            
                        for entry in feed.entries[:10]:  # Limit to 10 articles per feed
                            self.stats['total_articles_found'] += 1
                            
                            # Check if article is within specified timeframe
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                try:
                                    pub_date = datetime(*entry.published_parsed[:6])
                                    if pub_date < cutoff_date:
                                        continue
                                except Exception as e:
                                    logging.warning(f"    Date parsing error: {str(e)}")
                                    continue
                            
                            # Enhanced relevance check
                            if self.is_relevant_article(entry.get('title', ''), entry.get('summary', '')):
                                self.stats['relevant_articles'] += 1
                                
                                # Extract full article content
                                logging.info(f"    Extracting: {entry.get('title', 'No title')[:50]}...")
                                full_content = self.extract_full_article(entry.get('link', ''))
                                
                                # Parse publication date
                                pub_date = self.parse_date(entry.get('published_parsed'))
                                
                                article = {
                                    'title': entry.get('title', 'No title'),
                                    'url': entry.get('link', ''),
                                    'content': full_content,
                                    'date': pub_date,
                                    'source': feed_url,
                                    'category': category
                                }
                                
                                articles.append(article)
                                
                    except Exception as e:
                        logging.error(f"    Error parsing feed {feed_url}: {str(e)}")
                        self.stats['errors'].append(f"Feed parsing error {feed_url}: {str(e)}")
                        self.stats['failed_feeds'] += 1
                        
                except Exception as e:
                    logging.error(f"    Error processing {feed_url}: {str(e)}")
                    self.stats['errors'].append(f"Processing error {feed_url}: {str(e)}")
                    self.stats['failed_feeds'] += 1
                    failed_urls.append(feed_url)
        
        # Try alternative sources for failed URLs
        if failed_urls:
            logging.info(f"Trying alternative sources for {len(failed_urls)} failed URLs...")
            alternative_articles = self.try_alternative_sources(failed_urls)
            articles.extend(alternative_articles)
            logging.info(f"Retrieved {len(alternative_articles)} articles from alternative sources")
        
        return articles
    
    def remove_duplicates(self, articles):
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Simple deduplication based on title
            title_key = re.sub(r'[^\w\s]', '', article.get('title', '').lower())
            title_key = ' '.join(title_key.split()[:5])  # First 5 words
            
            if title_key not in seen_titles and title_key.strip():
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        return unique_articles
    
    def try_alternative_sources(self, failed_urls):
        """Try alternative methods to get content from failed sources"""
        alternative_articles = []
        
        # For blocked ISRO content, try government press releases
        if any('isro' in url.lower() for url in failed_urls):
            try:
                logging.info("Trying PIB for ISRO news...")
                pib_url = "https://pib.gov.in/RssMain.aspx?ModId=7&Lang=1"
                response = self.safe_request(pib_url)
                if response:
                    feed = feedparser.parse(response.content)
                    for entry in feed.entries[:5]:
                        if any(keyword in entry.title.lower() for keyword in ['isro', 'space', 'satellite', 'launch']):
                            article = {
                                'title': entry.title,
                                'url': entry.link,
                                'content': self.extract_full_article(entry.link),
                                'date': self.parse_date(entry.get('published_parsed')),
                                'source': 'PIB (Alternative for ISRO)',
                                'category': 'Space News'
                            }
                            alternative_articles.append(article)
            except Exception as e:
                logging.warning(f"PIB alternative failed: {e}")
        
        # For defense news, try Ministry of Defence
        if any('defense' in url.lower() or 'idrw' in url.lower() for url in failed_urls):
            try:
                logging.info("Trying MoD press releases...")
                mod_url = "https://pib.gov.in/RssMain.aspx?ModId=8&Lang=1"
                response = self.safe_request(mod_url)
                if response:
                    feed = feedparser.parse(response.content)
                    for entry in feed.entries[:5]:
                        if any(keyword in entry.title.lower() for keyword in self.high_priority_defense[:10]):
                            article = {
                                'title': entry.title,
                                'url': entry.link,
                                'content': self.extract_full_article(entry.link),
                                'date': self.parse_date(entry.get('published_parsed')),
                                'source': 'MoD PIB (Alternative)',
                                'category': 'Defense News'
                            }
                            alternative_articles.append(article)
            except Exception as e:
                logging.warning(f"MoD PIB alternative failed: {e}")
        
        return alternative_articles
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
            text = (article.get('title', '') + " " + article.get('content', '')).lower()
            
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
        defense_articles = [a for a in articles if a.get('category') == 'Defense News']
        space_articles = [a for a in articles if a.get('category') == 'Space News']
        
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
                report += f"""### {i}. {article.get('title', 'No title')}

**Date:** {article.get('date', 'Unknown')}
**Link:** {article.get('url', 'No URL')}
**Source:** {article.get('source', 'Unknown')}

**Full Article Text:**
{article.get('content', 'No content available')}

---

"""
        
        # Space section
        if space_articles:
            report += f"## 🚀 SPACE SECTOR NEWS ({len(space_articles)} articles)\n\n"
            for i, article in enumerate(space_articles, 1):
                report += f"""### {i}. {article.get('title', 'No title')}

**Date:** {article.get('date', 'Unknown')}
**Link:** {article.get('url', 'No URL')}
**Source:** {article.get('source', 'Unknown')}

**Full Article Text:**
{article.get('content', 'No content available')}

---

"""
        
        # Add summary of companies mentioned
        report += self.generate_company_summary(articles)
        
        # Add statistics
        report += f"""
## 📈 SCRAPING STATISTICS

- Total feeds processed: {self.stats['total_feeds_processed']}
- Successful feeds: {self.stats['successful_feeds']}
- Failed feeds: {self.stats['failed_feeds']}
- Total articles found: {self.stats['total_articles_found']}
- Relevant articles: {self.stats['relevant_articles']}
- Success rate: {(self.stats['successful_feeds'] / max(self.stats['total_feeds_processed'], 1)) * 100:.1f}%

"""
        
        if self.stats['errors']:
            report += "## ⚠️ ERRORS ENCOUNTERED\n\n"
            for error in self.stats['errors'][:10]:  # Show max 10 errors
                report += f"- {error}\n"
            if len(self.stats['errors']) > 10:
                report += f"- ... and {len(self.stats['errors']) - 10} more errors\n"
        
        return report
    
    def save_report(self, report, days_back=7):
        """Save report to file"""
        filename = f"defense_news_{days_back}days_{datetime.now().strftime('%Y%m%d')}.md"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logging.info(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            logging.error(f"Error saving report: {e}")
            return None
    
    def run_scraper(self, days_back=7):
        """Main scraping function - Robust version"""
        try:
            logging.info("Starting robust defense & space news scraping...")
            logging.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"Looking for articles from the last {days_back} days")
            
            # Scrape articles
            articles = self.scrape_rss_feeds(days_back)
            
            # Remove duplicates
            articles = self.remove_duplicates(articles)
            
            logging.info(f"Found {len(articles)} unique relevant articles")
            
            # Generate report even if no articles found
            report = self.generate_simple_report(articles, days_back)
            
            # Save report
            filename = self.save_report(report, days_back)
            
            # Log final statistics
            logging.info("Scraping completed successfully!")
            logging.info(f"Statistics: {self.stats['successful_feeds']}/{self.stats['total_feeds_processed']} feeds successful")
            logging.info(f"Found {self.stats['relevant_articles']} relevant articles out of {self.stats['total_articles_found']} total")
            
            if filename:
                logging.info(f"Report saved as: {filename}")
            
            # Exit with appropriate code
            if self.stats['successful_feeds'] == 0:
                logging.error("No feeds were successfully processed!")
                sys.exit(1)
            elif len(articles) == 0:
                logging.warning("No relevant articles found, but some feeds were processed successfully")
                sys.exit(0)
            else:
                sys.exit(0)
                
        except Exception as e:
            logging.error(f"Critical error in main scraping function: {str(e)}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Robust Defense News Scraper')
    parser.add_argument('--manual', action='store_true', help='Run scraper now')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled scraper (weekly)')
    parser.add_argument('--days', type=int, help='Number of days to look back (1-30)', default=7)
    
    args = parser.parse_args()
    
    if args.manual:
        # Create scraper instance
        scraper = RobustNewsScraper()
        
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
        print("  python robust_scraper.py --manual              # Run now (7 days default)")
        print("  python robust_scraper.py --manual --days 3     # Run for last 3 days")
        print("  python robust_scraper.py --schedule            # Run weekly")

def run_scheduled():
    """Run scraper on schedule with default 7-day period"""
    scraper = RobustNewsScraper()
    
    # Schedule for every Monday at 9 AM
    schedule.every().monday.at("09:00").do(scraper.run_scraper, 7)
    
    logging.info("Scheduler started. Will run every Monday at 9:00 AM")
    logging.info("Press Ctrl+C to stop")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logging.info("Scheduler stopped")

if __name__ == "__main__":
    main()
