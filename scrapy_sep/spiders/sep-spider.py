import scrapy
import pandas as pd
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
            yield scrapy.Request(url, callback=self.parse)
        else:
            self.logger.info("--- Running in full-scrape mode from CSV ---")
            try:
                df_index = pd.read_csv('sep_articles.csv') 
                for url in df_index['url'].unique().tolist():
                    yield scrapy.Request(url=url, callback=self.parse)
            except FileNotFoundError:
                self.logger.error("The index file 'sep_articles.csv' was not found in the project root directory.")

    def parse(self, response):
        """
        This method is now only responsible for passing the response to the pipeline.
        The parsing logic will be handled by a dedicated pipeline.
        """
        yield {'response': response}