# FOCUSED FIX: Just fix the content extraction problem

def extract_full_content(self, url):
    """Fixed content extraction - replaces your extract_simple_content method"""
    try:
        self.logger.debug(f"Extracting content from: {url}")
        response = self.make_request_with_retry(url, max_retries=2, timeout=20)
        
        if not response or response.status_code != 200:
            return "Could not fetch article content"
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements that clutter content
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                           'aside', '.sidebar', '.related', '.comments', 
                           '.social-share', '.advertisement', '.ad', '.ads',
                           '.widget', '.menu', '.navigation']):
            if element:
                element.decompose()
        
        # Try content selectors in order of preference
        content_selectors = [
            # WordPress and common CMS selectors
            '.post-content',           # WordPress posts
            '.entry-content',          # WordPress entries
            '.article-content',        # Generic articles
            '.content-area',           # Content areas
            
            # HTML5 semantic selectors
            'article',                 # HTML5 article tag
            'main',                    # Main content
            
            # News site specific selectors
            '.story-body',             # News stories
            '.article-body',           # Article bodies
            '.post-body',              # Post bodies
            
            # Forum/discussion selectors (for defence.in)
            '.bbWrapper',              # BBCode wrapper
            '.message-content',        # Message content
            
            # Generic fallbacks
            '.content',                # Generic content
            '#content',                # Content by ID
            '.single-post',            # Single post pages
            '.page-content',           # Page content
        ]
        
        content = ""
        used_selector = None
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # Try each element until we find substantial content
                for elem in elements:
                    extracted = elem.get_text(separator='\n', strip=True)
                    if len(extracted) > 200:  # Must have substantial content
                        content = extracted
                        used_selector = selector
                        break
                if content:
                    break
        
        # Fallback to body if no specific content area found
        if not content or len(content) < 100:
            self.logger.debug("Using body fallback for content extraction")
            body = soup.find('body')
            if body:
                content = body.get_text(separator='\n', strip=True)
                used_selector = "body (fallback)"
        
        if not content:
            return "No readable content found"
        
        # Clean the extracted content
        content = self.clean_content_text(content)
        
        # Log successful extraction
        self.logger.debug(f"Extracted {len(content)} chars using selector: {used_selector}")
        
        # Reasonable content length limit
        if len(content) > 5000:
            content = content[:5000] + "\n\n[Content continues - truncated for readability]"
        
        return content
        
    except Exception as e:
        self.logger.error(f"Content extraction error for {url}: {str(e)}")
        return f"Content extraction failed: {str(e)}"

def clean_content_text(self, text):
    """Clean extracted text"""
    if not text:
        return ""
    
    # Handle HTML entities
    import html
    text = html.unescape(text)
    
    # Clean whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
    text = re.sub(r'[ \t]+', ' ', text)             # Multiple spaces to single
    text = re.sub(r'^\s+|\s+$', '', text)           # Trim start/end
    
    # Remove common noise patterns
    noise_patterns = [
        r'Advertisement\s*',
        r'Subscribe.*?newsletter',
        r'Share\s+(this\s+)?(on\s+)?(Facebook|Twitter|LinkedIn|WhatsApp)',
        r'Follow\s+us\s+on\s+',
        r'Read\s+(more|full\s+story)',
        r'Continue\s+reading',
        r'Also\s+read:?',
        r'Related\s+(articles?|stories?):?',
        r'Tags?\s*:',
        r'Posted\s+(by|on)',
        r'Loading\.\.\.+',
        r'\[Continue reading\]',
        r'\[Read more\]',
        r'&[#\w]+;',  # HTML entities that weren't decoded
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up spacing again after removals
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = text.strip()
    
    return text

# USAGE: Replace your extract_simple_content method with extract_full_content
# and add the clean_content_text helper method

# Update your scrape_single_feed method to use the new function:
def scrape_single_feed(self, feed_url, category):
    """Updated to use better content extraction"""
    articles = []
    
    try:
        self.logger.info(f"Scraping: {feed_url}")
        response = self.make_request_with_retry(feed_url, timeout=15)
        
        if not response:
            self.logger.warning(f"Failed to fetch feed: {feed_url}")
            return articles
        
        feed = feedparser.parse(response.content)
        
        if not hasattr(feed, 'entries'):
            self.logger.warning(f"No entries in feed: {feed_url}")
            return articles
        
        self.logger.info(f"Found {len(feed.entries)} entries in {feed_url}")
        
        # Process entries (limit to 5 per feed)
        processed = 0
        for entry in feed.entries[:5]:
            try:
                if not hasattr(entry, 'title') or not entry.title:
                    continue
                
                # Check relevance (keep your existing logic)
                if not self.is_relevant_article(entry.title, entry.get('summary', '')):
                    continue
                
                self.logger.info(f"Processing: {entry.title[:60]}...")
                
                # Use improved content extraction
                full_content = self.extract_full_content(entry.link)
                
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
                
                # Small delay between article extractions to be polite
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.debug(f"Error processing entry: {e}")
                continue
        
        self.logger.info(f"Successfully processed {processed} articles from {feed_url}")
        
    except Exception as e:
        self.logger.error(f"Error scraping {feed_url}: {e}")
    
    return articles
