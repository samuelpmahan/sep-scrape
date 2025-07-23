import scrapy

class SepArticleItem(scrapy.Item):
    # Fields that will be saved to the JSON file.
    url = scrapy.Field()
    title = scrapy.Field()
    preamble_text = scrapy.Field()
    related_entries = scrapy.Field()
    text_with_placeholders = scrapy.Field()
    math_expressions = scrapy.Field()

    # --- Temporary fields used during processing ---
    # The spider passes the response object.
    response = scrapy.Field() 
    # This holds the main text before LaTeX processing.
    body_text = scrapy.Field()