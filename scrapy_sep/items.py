import scrapy

class SepArticleItem(scrapy.Item):
    # The structured data container for a single article.
    
    # Metadata
    url = scrapy.Field()
    title = scrapy.Field()
    
    # Content Payloads
    preamble_text = scrapy.Field()
    body_text = scrapy.Field()
    
    # Graph Structure
    related_entries = scrapy.Field()