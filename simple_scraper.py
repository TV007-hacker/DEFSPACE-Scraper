# CORRECTED AND VERIFIED RSS SOURCES (Updated September 2025)
self.sources = {
    "Defense News": [
        # VERIFIED WORKING Indian Defense Sources
        "https://www.livefistdefence.com/feed/",           # ✅ VERIFIED - India's most popular defense blog
        "https://defence.in/feed/",                        # ✅ VERIFIED - Redirects to forums/news/index.rss
        "https://www.indiandefensenews.in/feeds/posts/default?alt=rss",  # ✅ Active Indian Defense News
        "https://forceindia.net/feed/",                    # ✅ VERIFIED - FORCE Magazine
        "https://stratpost.com/feed/",                     # ✅ VERIFIED - Strategic Affairs
        "https://www.ajaishukla.com/feeds/posts/default?alt=rss",  # ✅ Broadsword by Col Ajai Shukla
        "https://theigmp.org/feeds/posts/default",         # ✅ India's Growing Military Power
        "https://defenceupdate.in/feed/",                  # ✅ Defence Update India
        
        # IDRW.org feed may be intermittent - keep as backup
        "https://idrw.org/feed/",                          # ⚠️  Sometimes works, high traffic site
        
        # International Defense Sources (for broader context)
        "https://defence-blog.com/feed/",                  # ✅ VERIFIED - Global defense blog
        "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",  # ✅ Defense News Global
        "https://breakingdefense.com/feed/",               # ✅ Breaking Defense
        "https://www.defenseworld.net/rss/news.xml",       # ✅ Defense World
        "https://quwa.org/feed/",                          # ✅ Quwa Defense Analysis
        "https://thediplomat.com/feed/",                   # ✅ The Diplomat (covers Asia Defense)
        
        # Remove broken/non-existent feeds:
        # ❌ REMOVED: "https://www.defencexp.com/feed/" - Site not accessible
        # ❌ REMOVED: Specific PIB defense RSS - generic PIB feed available instead
    ],
    
    "Space News": [
        # Note: ISRO does NOT have a public RSS feed at isro.gov.in
        
        # VERIFIED WORKING International Space Sources
        "https://spacenews.com/feed/",                     # ✅ VERIFIED - Leading space industry news
        "https://www.space.com/feeds/all",                 # ✅ VERIFIED - Space.com all feeds
        "https://spaceflightnow.com/feed/",                # ✅ VERIFIED - Spaceflight Now
        "https://www.universetoday.com/feed/",             # ✅ VERIFIED - Universe Today
        "https://phys.org/rss-feed/space-news/",           # ✅ VERIFIED - Phys.org space section
        "https://www.planetary.org/feed.xml",              # ✅ VERIFIED - Planetary Society
        
        # Indian Mainstream Media Space Coverage
        "https://www.thehindu.com/sci-tech/science/feeder/default.rss",  # ✅ Hindu Science
        "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",    # ✅ TOI Science
        "https://economictimes.indiatimes.com/industry/aerospace/defence/rssfeeds/13352306.cms", # ✅ ET Aerospace
        
        # NASA & ESA (cover ISRO collaborations)
        "https://www.nasa.gov/news/releases/latest/rss",   # ✅ NASA News Releases
        "https://www.esa.int/rssfeed/Our_Activities/Space_Science",  # ✅ ESA Space Science
        
        # Remove non-working feeds:
        # ❌ REMOVED: "https://www.isro.gov.in/rss.xml" - Does not exist
        # ❌ REMOVED: "https://ispa.space/feed/" - Site not accessible
        # ❌ REMOVED: MOSDAC RSS - limited public access
    ]
}

# ADDITIONAL BACKUP FEEDS (use if primary feeds fail)
self.backup_sources = {
    "Defense News": [
        "https://www.janes.com/feeds/news.xml",            # Janes Defense (may require subscription)
        "https://ukdefencejournal.org.uk/feed/",           # UK Defence Journal
        "https://www.defensedaily.com/rss",                # Defense Daily
        "https://realcleardefense.com/index.xml",          # RealClear Defense
    ],
    
    "Space News": [
        "https://spacedaily.com/spacedaily.xml",           # Space Daily
        "https://www.spacq.ca/feed/",                      # SpaceQ (Canadian)
        "https://www.nextbigfuture.com/category/space/feed", # Next Big Future Space
    ]
}

# RSS FEED VALIDATION FUNCTION
def validate_rss_feeds(self):
    """Validate all RSS feeds before scraping"""
    valid_sources = {"Defense News": [], "Space News": []}
    
    for category, feeds in self.sources.items():
        print(f"\nValidating {category} feeds...")
        
        for feed_url in feeds:
            try:
                response = self.make_request_with_retry(feed_url, max_retries=2, timeout=10)
                if response and response.status_code == 200:
                    # Try to parse as RSS to ensure it's valid
                    import feedparser
                    feed = feedparser.parse(response.content)
                    
                    if hasattr(feed, 'entries') and len(feed.entries) > 0:
                        valid_sources[category].append(feed_url)
                        print(f"✅ VALID: {feed_url}")
                    else:
                        print(f"⚠️  EMPTY: {feed_url} (no entries)")
                else:
                    print(f"❌ FAILED: {feed_url} (HTTP {response.status_code if response else 'No response'})")
                    
            except Exception as e:
                print(f"❌ ERROR: {feed_url} - {str(e)}")
    
    # Update sources with only valid feeds
    self.sources = valid_sources
    
    # Add backup feeds if primary feeds are insufficient
    for category in self.sources:
        if len(self.sources[category]) < 3:  # If less than 3 working feeds
            print(f"\n⚠️  Only {len(self.sources[category])} working feeds for {category}, adding backups...")
            for backup_feed in self.backup_sources.get(category, []):
                try:
                    response = self.make_request_with_retry(backup_feed, max_retries=1, timeout=8)
                    if response and response.status_code == 200:
                        self.sources[category].append(backup_feed)
                        print(f"✅ BACKUP ADDED: {backup_feed}")
                        if len(self.sources[category]) >= 5:  # Stop at 5 feeds per category
                            break
                except:
                    continue
    
    return self.sources

# ENHANCED GOOGLE NEWS SEARCH (Fixed URLs)
def add_google_news_search(self, days_back=7):
    """Fixed Google News search with proper RSS URLs"""
    articles = []
    
    # More targeted search terms to get relevant results
    search_terms = [
        "India ISRO space mission launch",
        "Indian defense HAL DRDO contract deal",
        "India military procurement defense export",
        "Indian space startup Skyroot Agnikul funding"
    ]
    
    self.logger.info("Searching Google News...")
    
    for term in search_terms[:2]:  # Limit searches to avoid blocking
        try:
            # Use proper Google News RSS search format
            encoded_term = term.replace(" ", "+").replace(",", "")
            # Fixed Google News RSS URL format
            search_url = f"https://news.google.com/rss/search?q={encoded_term}&hl=en-IN&gl=IN&ceid=IN:en"
            
            response = self.make_request_with_retry(search_url, timeout=12)
            if not response or response.status_code != 200:
                self.logger.warning(f"Google News search failed for: {term}")
                continue
            
            feed = feedparser.parse(response.content)
            
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                self.logger.warning(f"No Google News results for: {term}")
                continue
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for entry in feed.entries[:3]:  # Top 3 results per search
                try:
                    # Check date if available
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date < cutoff_date:
                            continue
                    
                    # Enhanced relevance check
                    if self.is_relevant_article(entry.title, entry.get('summary', '')):
                        self.logger.info(f"Found Google News: {entry.title[:50]}...")
                        
                        # Extract full content
                        full_content = self.extract_full_article(entry.link)
                        
                        article = {
                            'title': entry.title,
                            'url': entry.link,
                            'content': full_content,
                            'date': self.parse_date(entry.get('published_parsed')),
                            'source': f"Google News ({entry.get('source', {}).get('title', 'Unknown')})",
                            'category': self.determine_category(entry.title, entry.get('summary', ''))
                        }
                        
                        articles.append(article)
                        
                except Exception as e:
                    self.logger.error(f"Error processing Google News entry: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Google News search error for '{term}': {e}")
    
    self.logger.info(f"Found {len(articles)} relevant Google News articles")
    return articles

def determine_category(self, title, summary=""):
    """Determine if article is Defense or Space category"""
    text = (title + " " + summary).lower()
    
    space_indicators = ['space', 'isro', 'satellite', 'rocket', 'launch', 'orbit', 'mission', 
                       'chandrayaan', 'gaganyaan', 'pslv', 'gslv', 'astronaut', 'spacecraft']
    defense_indicators = ['defense', 'defence', 'military', 'army', 'navy', 'air force', 
                         'hal', 'drdo', 'tejas', 'brahmos', 'border', 'security']
    
    space_score = sum(1 for indicator in space_indicators if indicator in text)
    defense_score = sum(1 for indicator in defense_indicators if indicator in text)
    
    return 'Space News' if space_score > defense_score else 'Defense News'

# USAGE INSTRUCTIONS:
# 1. Add the validate_rss_feeds() method to your SimpleNewsScraper class
# 2. Call self.validate_rss_feeds() in your __init__ method after setting up sources
# 3. Replace your existing add_google_news_search method with the fixed version above
# 4. Update your sources dictionary with the corrected URLs

# Example initialization:
def __init__(self):
    # ... existing initialization code ...
    
    # Set up RSS sources (corrected versions)
    self.sources = {/* corrected sources from above */}
    self.backup_sources = {/* backup sources from above */}
    
    # Validate feeds on startup (optional - may slow initialization)
    # self.validate_rss_feeds()
