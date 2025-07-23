import scrapy
import pandas as pd
import re
from scrapy_sep.items import SepArticleItem

class SepSpider(scrapy.Spider):
    name = 'sep'
    allowed_domains = ['plato.stanford.edu']

    async def start(self):
        """
        The modern entry point for spiders. It now supports two modes:
        1. Full scrape: Reads from sep_articles.csv (default).
        2. Single URL scrape: If a 'url' is passed via the command line.
        """
        # Check if a single URL was passed as an argument
        url = getattr(self, "url", None)
        if url is not None:
            self.logger.info(f"--- Running in single-URL mode for: {url} ---")
            yield scrapy.Request(url, callback=self.parse_article)
        else:
            self.logger.info("--- Running in full-scrape mode from CSV ---")
            try:
                df_index = pd.read_csv('sep_articles.csv') 
                for url in df_index['url'].unique().tolist():
                    yield scrapy.Request(url=url, callback=self.parse_article)
            except FileNotFoundError:
                self.logger.error("The index file 'sep_articles.csv' was not found in the project root directory.")

    def parse_article(self, response):
        """
        Parses the article response. Now supports a 'dry_run' mode.
        """
        item = SepArticleItem()
        item['url'] = response.url
        
        aueditable_div = response.css('#aueditable')
        if not aueditable_div:
            self.logger.warning(f"Could not find #aueditable div in {response.url}")
            return

        item['title'] = aueditable_div.css('h1::text').get(default='Untitled').strip()
        
        # For preamble, get all text within the div, then join.
        preamble_div = aueditable_div.css('#preamble')
        if preamble_div:
            item['preamble_text'] = " ".join(preamble_div.css('::text').getall()).strip()
        
        # For body, get the text of the whole div, then split into paragraphs.
        # This is much more reliable than trying to select individual tags.
        main_text_div = aueditable_div.css('#main-text')
        if main_text_div:
            full_text = " ".join(main_text_div.css('::text').getall())
            # Split by multiple newlines to recreate paragraphs, filtering out empty ones.
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', full_text) if p.strip()]
            item['body_text'] = "\n\n".join(paragraphs)

        related_links = aueditable_div.css('#related-entries a::attr(href)').getall()
        item['related_entries'] = [response.urljoin(link) for link in related_links]
        
        if getattr(self, "dry_run", "false").lower() == 'true':
            self.logger.info("--- Dry Run Mode: Scraped Item ---")
            print(dict(item))
            return
        
        yield item