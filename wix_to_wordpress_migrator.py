#!/usr/bin/env python3
"""
Wix to WordPress Blog Migrator
==============================

A comprehensive tool for migrating blog content from Wix websites to WordPress.
This tool scrapes blog posts from Wix sites and cleans the content for WordPress import.

Features:
- Scrapes all blog posts from Wix sites (handles pagination)
- Extracts titles, dates, categories, and content
- Removes Wix-specific HTML/CSS clutter
- Eliminates excessive div wrappers and empty spans
- Preserves images and essential formatting
- Creates WordPress-compatible XML import files
- Handles JavaScript-rendered content with Selenium

Author: Community Project
License: MIT
Repository: https://github.com/your-username/wix-to-wordpress-migrator
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import re
from urllib.parse import urljoin
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import Selenium (optional dependency)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available. Install with: pip install selenium webdriver-manager")

class WixBlogScraper:
    """Main class for scraping Wix blog content"""
    
    def __init__(self, base_url):
        """
        Initialize the scraper
        
        Args:
            base_url (str): The base URL of the Wix website (e.g., "https://www.example.com")
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        
        if SELENIUM_AVAILABLE:
            self.setup_selenium()
    
    def setup_selenium(self):
        """Setup Selenium WebDriver for JavaScript-heavy sites"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--window-size=1280,720')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            logger.info("✓ Selenium initialized successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Selenium setup failed: {e}")
            self.driver = None
            return False
    
    def get_all_blog_post_urls(self, max_pages=20):
        """
        Find all blog post URLs using multiple methods
        
        Args:
            max_pages (int): Maximum number of pages to check for pagination
            
        Returns:
            list: List of unique blog post URLs
        """
        all_urls = set()
        
        # Method 1: Try with Selenium (best for modern Wix sites)
        if self.driver:
            logger.info("Method 1: Using Selenium to find blog posts...")
            selenium_urls = self.get_urls_with_selenium()
            all_urls.update(selenium_urls)
            logger.info(f"Found {len(selenium_urls)} URLs with Selenium")
        
        # Method 2: Try pagination patterns
        logger.info("Method 2: Checking pagination patterns...")
        pagination_urls = self.check_pagination_patterns(max_pages)
        all_urls.update(pagination_urls)
        logger.info(f"Found {len(pagination_urls)} URLs with pagination")
        
        # Method 3: Basic requests scraping
        logger.info("Method 3: Using requests to scrape blog listing...")
        requests_urls = self.get_urls_with_requests()
        all_urls.update(requests_urls)
        logger.info(f"Found {len(requests_urls)} URLs with requests")
        
        return list(all_urls)
    
    def get_urls_with_selenium(self):
        """Get URLs using Selenium with controlled scrolling"""
        if not self.driver:
            return []
        
        urls = set()
        blog_pages = [
            f"{self.base_url}/blog-1",
            f"{self.base_url}/blog",
            f"{self.base_url}/posts",
            f"{self.base_url}/articles"
        ]
        
        for blog_url in blog_pages:
            try:
                logger.info(f"Loading: {blog_url}")
                self.driver.get(blog_url)
                time.sleep(5)
                
                # Controlled scrolling to load more content
                for i in range(10):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    # Look for "Load More" buttons
                    try:
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons[:3]:
                            if button.text and any(word in button.text.lower() for word in ['more', 'load', 'show']):
                                if button.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", button)
                                    time.sleep(3)
                                    break
                    except:
                        pass
                
                # Extract URLs
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(self.base_url, href)
                    
                    if (self.base_url in full_url and 
                        any(pattern in full_url for pattern in ['/post/', '/blog-1/', '/blog/', '/posts/'])):
                        urls.add(full_url)
                
                if urls:
                    break
                    
            except Exception as e:
                logger.warning(f"Error with {blog_url}: {e}")
                continue
        
        return list(urls)
    
    def check_pagination_patterns(self, max_pages):
        """Check for pagination using common URL patterns"""
        urls = set()
        blog_base = f"{self.base_url}/blog-1"
        
        for page in range(1, max_pages + 1):
            page_urls = [
                f"{blog_base}?page={page}",
                f"{blog_base}&page={page}",
                f"{blog_base}/page/{page}",
                f"{blog_base}?offset={12 * (page - 1)}"
            ]
            
            for page_url in page_urls:
                try:
                    response = self.session.get(page_url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        page_urls_found = self.extract_urls_from_soup(soup)
                        if page_urls_found:
                            urls.update(page_urls_found)
                            logger.info(f"Found {len(page_urls_found)} URLs on page {page}")
                            break
                except:
                    continue
            
            time.sleep(1)  # Be respectful
        
        return list(urls)
    
    def get_urls_with_requests(self):
        """Get URLs using basic requests"""
        urls = set()
        blog_pages = [
            f"{self.base_url}/blog-1",
            f"{self.base_url}/blog",
            f"{self.base_url}/posts",
            f"{self.base_url}"
        ]
        
        for blog_url in blog_pages:
            try:
                response = self.session.get(blog_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_urls = self.extract_urls_from_soup(soup)
                    urls.update(page_urls)
            except Exception as e:
                logger.warning(f"Requests failed for {blog_url}: {e}")
        
        return list(urls)
    
    def extract_urls_from_soup(self, soup):
        """Extract blog post URLs from BeautifulSoup object"""
        urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(self.base_url, href)
            
            if (self.base_url in full_url and 
                any(pattern in full_url for pattern in ['/post/', '/blog-1/', '/blog/', '/posts/'])):
                urls.add(full_url)
        
        return urls
    
    def scrape_post(self, url):
        """
        Scrape a single blog post
        
        Args:
            url (str): URL of the blog post to scrape
            
        Returns:
            dict: Post data with title, date, category, content, and URL
        """
        try:
            # Try Selenium first if available
            if self.driver:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                except:
                    response = self.session.get(url, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
            else:
                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
            
            post_data = {
                'url': url,
                'title': self.extract_title(soup),
                'publish_date': self.extract_date(soup),
                'category': self.extract_category(soup),
                'content': self.extract_content(soup)
            }
            
            if post_data['title'] != "Untitled Post" and len(post_data['content']) > 100:
                logger.info(f"✓ Scraped: {post_data['title']}")
                return post_data
            else:
                logger.warning(f"⚠ Skipped (insufficient content): {url}")
                return None
            
        except Exception as e:
            logger.error(f"✗ Failed to scrape {url}: {e}")
            return None
    
    def extract_title(self, soup):
        """Extract post title using multiple strategies"""
        title_selectors = [
            'h1', 'h2', '.post-title', '[data-testid="post-title"]',
            'title', 'meta[property="og:title"]'
        ]
        
        for selector in title_selectors:
            if selector == 'meta[property="og:title"]':
                elem = soup.select_one(selector)
                if elem and elem.get('content'):
                    return elem.get('content').strip()
            else:
                elem = soup.select_one(selector)
                if elem and elem.get_text().strip():
                    title = elem.get_text().strip()
                    if len(title) > 3 and not title.lower().startswith(('home', 'blog', 'menu')):
                        return title
        
        return "Untitled Post"
    
    def extract_date(self, soup):
        """Extract publish date"""
        date_selectors = [
            'time[datetime]', 'time', '.post-date', '.blog-post-date', 
            '.date', '[data-testid="post-date"]', 'meta[property="article:published_time"]'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date_val = elem.get('datetime') or elem.get('content') or elem.get_text().strip()
                if date_val:
                    parsed = self.parse_date(date_val)
                    if parsed:
                        return parsed
                    return date_val
        
        return ""
    
    def extract_category(self, soup):
        """Extract post category"""
        category_selectors = [
            '.post-category', '.category', '.tag', '[data-testid="post-category"]'
        ]
        
        for selector in category_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text().strip():
                return elem.get_text().strip()
        
        return "Uncategorized"
    
    def parse_date(self, date_str):
        """Parse date string to ISO format"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d', '%B %d, %Y', '%b %d, %Y', '%m/%d/%Y', '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).isoformat()
            except ValueError:
                continue
        
        return None
    
    def extract_content(self, soup):
        """Extract post content including images"""
        content_selectors = [
            '.post-content', '.blog-post-content', '.rich-text', 'article', 
            '.content', 'main', '[data-testid="post-content"]'
        ]
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                # Remove unwanted elements but keep images
                for unwanted in elem(['script', 'style', 'nav', 'header', 'footer']):
                    unwanted.decompose()
                
                content = str(elem).strip()
                if len(content) > 100:
                    return content
        
        return ""
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

def clean_wix_content(content):
    """
    Ultimate content cleaner: Remove Wix code AND excessive divs while preserving images
    
    Args:
        content (str): Raw HTML content from Wix
        
    Returns:
        str: Cleaned HTML content ready for WordPress
    """
    if not content:
        return ""
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove scripts, styles, and unwanted elements
    for element in soup(['script', 'style', 'button', 'nav', 'header', 'footer']):
        element.decompose()
    
    # Remove SVGs that aren't images
    for svg in soup.find_all('svg'):
        if not svg.get('alt'):
            svg.decompose()
    
    # Remove ALL attributes except essential image attributes
    for element in soup.find_all():
        if element.name == 'img':
            # Keep only essential image attributes
            essential_attrs = {}
            for attr in ['src', 'alt', 'title', 'width', 'height', 'srcset', 'loading']:
                if element.has_attr(attr):
                    essential_attrs[attr] = element[attr]
            element.attrs.clear()
            element.attrs.update(essential_attrs)
        else:
            # Remove ALL attributes from other elements
            element.attrs.clear()
    
    # Clean up figures
    for figure in soup.find_all('figure'):
        if not figure.find('img'):
            figure.unwrap()
    
    # Aggressively unwrap wrapper divs
    changes_made = True
    max_iterations = 15
    iteration = 0
    
    while changes_made and iteration < max_iterations:
        changes_made = False
        iteration += 1
        
        for div in soup.find_all('div'):
            try:
                if not div.parent:
                    continue
                
                children = list(div.children)
                if len(children) <= 5:
                    has_meaningful_children = any(
                        hasattr(child, 'name') and child.name in [
                            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'figure', 'img', 
                            'ul', 'ol', 'blockquote', 'strong', 'em', 'a'
                        ]
                        for child in children
                    )
                    
                    if has_meaningful_children or len(children) == 1:
                        div.unwrap()
                        changes_made = True
            except ValueError:
                continue
    
    # Clean up spans and breaks
    for span in soup.find_all('span'):
        try:
            if span.parent:
                text = span.get_text(strip=True)
                if not text or text in ['&nbsp;', ' ', '\u00a0']:
                    span.decompose()
                elif not span.get('style') and not span.get('class'):
                    span.unwrap()
        except:
            continue
    
    # Remove empty paragraphs
    for p in soup.find_all('p'):
        try:
            if p.parent:
                text = p.get_text(strip=True)
                if not text or text in ['&nbsp;', ' ', '\u00a0']:
                    p.decompose()
        except:
            continue
    
    # Clean up links
    for link in soup.find_all('a'):
        if link.has_attr('href'):
            href = link['href']
            link.attrs.clear()
            link['href'] = href
        else:
            link.unwrap()
    
    # Remove empty elements
    for element in soup.find_all():
        try:
            if (element.name not in ['img', 'br', 'hr'] and 
                element.parent and
                not element.get_text(strip=True) and 
                not element.find(['img', 'br', 'hr'])):
                element.decompose()
        except:
            continue
    
    # Convert back to string and clean up
    clean_content = str(soup)
    clean_content = re.sub(r'<span>\s*</span>', '', clean_content)
    clean_content = re.sub(r'<span>\s*<br\s*/?>\s*</span>', '<br />', clean_content)
    clean_content = re.sub(r'<br\s*/?>\s*<br\s*/?>\s*<br\s*/?>+', '<br /><br />', clean_content)
    clean_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_content)
    clean_content = re.sub(r'<p>\s*</p>', '', clean_content)
    
    return clean_content.strip()

def create_wordpress_xml(posts, output_file, site_title="Blog Import"):
    """
    Create WordPress XML import file
    
    Args:
        posts (list): List of post dictionaries
        output_file (str): Path for output XML file
        site_title (str): Title for the import
    """
    xml_content = f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
    xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:wfw="http://wellformedweb.org/CommentAPI/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:wp="http://wordpress.org/export/1.2/"
>

<channel>
    <title>{site_title}</title>
    <description>Migrated blog posts from Wix</description>
    <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
    <language>en-US</language>
    <wp:wxr_version>1.2</wp:wxr_version>

'''

    for i, post in enumerate(posts, 1):
        title = post.get('title', f'Untitled Post {i}').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        content = post.get('content', '').strip()
        
        # Handle date
        post_date = post.get('publish_date', '')
        if post_date:
            try:
                if 'T' in post_date:
                    dt = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(post_date, '%Y-%m-%d')
            except:
                dt = datetime.now()
        else:
            dt = datetime.now()
        
        formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        slug = re.sub(r'\s+', '-', slug.strip())[:50]
        
        category = post.get('category', 'Uncategorized')
        
        xml_content += f'''
    <item>
        <title><![CDATA[{title}]]></title>
        <pubDate>{dt.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
        <dc:creator><![CDATA[admin]]></dc:creator>
        <content:encoded><![CDATA[{content}]]></content:encoded>
        <wp:post_id>{i}</wp:post_id>
        <wp:post_date><![CDATA[{formatted_date}]]></wp:post_date>
        <wp:post_date_gmt><![CDATA[{formatted_date}]]></wp:post_date_gmt>
        <wp:comment_status><![CDATA[open]]></wp:comment_status>
        <wp:ping_status><![CDATA[open]]></wp:ping_status>
        <wp:post_name><![CDATA[{slug}]]></wp:post_name>
        <wp:status><![CDATA[publish]]></wp:status>
        <wp:post_type><![CDATA[post]]></wp:post_type>
        <category domain="category" nicename="{category.lower()}"><![CDATA[{category}]]></category>
    </item>'''
    
    xml_content += '''
</channel>
</rss>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)

def main():
    """Main function to run the migration"""
    print("🚀 Wix to WordPress Blog Migrator")
    print("=" * 40)
    print("Migrates blog content from Wix websites to WordPress")
    print()
    
    # Get website URL from user
    website_url = input("Enter the Wix website URL (e.g., https://www.example.com): ").strip()
    
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    print(f"\n🔍 Starting migration for: {website_url}")
    
    scraper = WixBlogScraper(website_url)
    
    try:
        # Step 1: Find all blog post URLs
        print(f"\n📋 Step 1: Finding blog post URLs...")
        all_urls = scraper.get_all_blog_post_urls()
        
        if not all_urls:
            print("❌ No blog post URLs found")
            print("Try checking if the site has a different blog URL structure")
            return
        
        print(f"✅ Found {len(all_urls)} unique blog post URLs")
        
        # Step 2: Scrape all posts
        print(f"\n📄 Step 2: Scraping {len(all_urls)} posts...")
        all_posts = []
        
        for i, url in enumerate(all_urls, 1):
            print(f"Scraping {i}/{len(all_urls)}: {url}")
            post_data = scraper.scrape_post(url)
            if post_data:
                all_posts.append(post_data)
            time.sleep(1)  # Be respectful to the server
        
        if not all_posts:
            print("❌ No posts could be scraped successfully")
            return
        
        print(f"✅ Successfully scraped {len(all_posts)} posts")
        
        # Step 3: Clean content
        print(f"\n🧹 Step 3: Cleaning content...")
        for post in all_posts:
            original_content = post.get('content', '')
            cleaned_content = clean_wix_content(original_content)
            post['content'] = cleaned_content
        
        # Step 4: Save results
        print(f"\n💾 Step 4: Saving results...")
        
        # Save raw JSON
        json_file = 'scraped_blog_posts.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, indent=2, ensure_ascii=False)
        
        # Create WordPress XML
        xml_file = 'wordpress_import.xml'
        create_wordpress_xml(all_posts, xml_file)
        
        print(f"\n🎉 Migration complete!")
        print(f"📄 Raw data: {json_file}")
        print(f"📄 WordPress import: {xml_file}")
        print(f"\nNext steps:")
        print(f"1. Go to your WordPress admin → Tools → Import")
        print(f"2. Install the WordPress Importer")
        print(f"3. Upload {xml_file}")
        print(f"4. Consider using 'Auto Upload Images' plugin to migrate images")
        
    except KeyboardInterrupt:
        print("\n⚠️ Migration cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()
