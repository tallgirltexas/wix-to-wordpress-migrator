# Wix to WordPress Blog Migrator

A comprehensive Python tool for migrating blog content from Wix websites to WordPress. This tool scrapes blog posts from Wix sites, cleans the HTML content, and creates WordPress-compatible import files.

## 🌟 Features

- **Complete Blog Scraping**: Automatically finds and scrapes all blog posts from Wix sites
- **Pagination Support**: Handles sites with multiple pages of blog posts
- **JavaScript Rendering**: Uses Selenium for sites with dynamic content loading
- **Content Cleaning**: Removes Wix-specific HTML/CSS clutter and excessive div wrappers
- **Image Preservation**: Maintains all images and essential formatting
- **WordPress Ready**: Creates XML files compatible with WordPress import tools
- **Robust Error Handling**: Continues processing even if individual posts fail

## 🛠️ What It Does

### Extraction
- **Titles**: Post titles with fallback strategies
- **Dates**: Publication dates in various formats
- **Categories**: Post categories and tags
- **Content**: Full post content including images
- **URLs**: Original post URLs for reference

### Cleaning
- Removes Wix-specific attributes (`data-hook`, cryptic classes, etc.)
- Eliminates excessive `<div>` wrapper elements
- Cleans up empty `<span>` tags and unnecessary `<br>` elements
- Preserves essential formatting (bold, italic, links, lists)
- Maintains image integrity with proper attributes

## 📋 Prerequisites

- Python 3.7 or higher
- Google Chrome browser (for Selenium functionality)

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tallgirltexas/wix-to-wordpress-migrator.git
   cd wix-to-wordpress-migrator
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install optional packages for enhanced functionality**:
   ```bash
   pip install selenium webdriver-manager
   ```

## 📦 Requirements

Create a `requirements.txt` file with:
```
requests>=2.25.0
beautifulsoup4>=4.9.0
selenium>=4.0.0
webdriver-manager>=3.8.0
```

## 💻 Usage

### Basic Usage

1. **Run the script**:
   ```bash
   python wix_to_wordpress_migrator.py
   ```

2. **Enter your Wix website URL** when prompted:
   ```
   Enter the Wix website URL: https://www.example.com
   ```

3. **Wait for the migration to complete**. The script will:
   - Find all blog post URLs
   - Scrape each post's content
   - Clean the HTML
   - Create output files

### Output Files

- `scraped_blog_posts.json`: Raw scraped data
- `wordpress_import.xml`: WordPress-compatible import file

### Advanced Usage

You can also use the classes directly in your own scripts:

```python
from wix_migrator import WixBlogScraper, clean_wix_content

# Initialize scraper
scraper = WixBlogScraper("https://www.example.com")

# Get all blog URLs
urls = scraper.get_all_blog_post_urls()

# Scrape individual posts
posts = []
for url in urls:
    post = scraper.scrape_post(url)
    if post:
        # Clean the content
        post['content'] = clean_wix_content(post['content'])
        posts.append(post)

# Clean up
scraper.cleanup()
```

## 📝 WordPress Import Instructions

1. **Log into your WordPress admin panel**
2. **Go to Tools → Import**
3. **Install the WordPress Importer** (if not already installed)
4. **Upload the generated XML file** (`wordpress_import.xml`)
5. **Follow the import wizard**:
   - Assign posts to an existing user or create a new author
   - Choose whether to download and import file attachments
   - Click "Submit" to start the import

### Importing Images

Images will still be hosted on the original Wix site after import. To migrate images to your WordPress site:

1. **Install the "Auto Upload Images" plugin**
2. **Go to Settings → Auto Upload Images**
3. **Click "Import External Images"**
4. The plugin will download all external images to your WordPress media library

## 🔧 Configuration Options

### Common Wix Blog URL Patterns

The script automatically checks these common patterns:
- `/blog-1` (most common)
- `/blog`
- `/posts`
- `/articles`

### Customizing for Your Site

If your site uses a different blog URL structure, you can modify the `blog_pages` list in the `get_urls_with_selenium()` method:

```python
blog_pages = [
    f"{self.base_url}/your-custom-blog-path",
    f"{self.base_url}/blog-1",
    # ... other patterns
]
```

## 🐛 Troubleshooting

### Common Issues

**1. "No blog post URLs found"**
- Check if your site uses a non-standard blog URL
- Verify the site is publicly accessible
- Try running with `--verbose` for more detailed logging

**2. "Selenium setup failed"**
- Make sure Google Chrome is installed
- Try installing/updating Chrome WebDriver manually
- Run without Selenium (basic mode) if needed

**3. "Few posts scraped compared to expected"**
- The site might use heavy JavaScript loading
- Try increasing the scroll iterations in `get_urls_with_selenium()`
- Some posts might be in draft mode or password protected

**4. "Content appears messy after import"**
- Run the content through the cleaner function again
- Check if your WordPress theme has conflicting CSS
- Consider using a "Convert to Blocks" plugin for Gutenberg

### Debug Mode

Enable verbose logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make your changes**
4. **Add tests** if applicable
5. **Commit your changes**: `git commit -m "Add new feature"`
6. **Push to the branch**: `git push origin feature/new-feature`
7. **Submit a pull request**

### Areas for Improvement

- Support for additional Wix site structures
- Better handling of complex media content
- Integration with WordPress REST API for direct posting
- GUI interface for non-technical users
- Support for other website builders (Squarespace, Weebly, etc.)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

- This tool is for migrating content you own or have permission to migrate
- Always respect robots.txt and website terms of service
- The tool makes HTTP requests to the target website - use responsibly
- Large sites may take considerable time to scrape
- Always backup your WordPress site before importing content

## 📊 Success Stories

This tool has been successfully used to migrate:
- Personal blogs with 50-125 posts
- Sites with embedded images and media


## 🔗 Related Tools

- [WordPress Importer Plugin](https://wordpress.org/plugins/wordpress-importer/)
- [Auto Upload Images Plugin](https://wordpress.org/plugins/auto-upload-images/)
- [WP All Import](https://www.wpallimport.com/) (Premium alternative)

## 💡 Tips for Best Results

1. **Test with a few posts first** before running the full migration
2. **Check your WordPress theme** compatibility with imported content
3. **Use a staging site** for testing the import process
4. **Consider SEO implications** when changing URLs
5. **Set up proper redirects** from old Wix URLs to new WordPress URLs

## 📞 Support

If you encounter issues:

1. **Check the [Issues](../../issues) page** for similar problems
2. **Create a new issue** with detailed information about your problem
3. **Include the website URL structure** and any error messages
4. **Specify your Python version** and operating system

---

**Made with ❤️ by the community for easier website migrations**
