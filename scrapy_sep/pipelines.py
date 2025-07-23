import re
import os
import json
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class ParsingPipeline:
    """
    PIPELINE STAGE 1 (Priority: 200)
    Takes the initial response and performs basic parsing to extract
    the title, preamble, main body text, and related entries.
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        response = adapter.get('response')
        if not response:
            raise DropItem("Item is missing the 'response' object.")

        # Populate the item with initial data from the response.
        adapter['url'] = response.url
        adapter['title'] = response.css('#aueditable h1::text').get(default='Untitled').strip()
        
        # Extract preamble, main text, and related links separately.
        adapter['preamble_text'] = " ".join(response.css('#preamble *::text').getall()).strip()
        adapter['body_text'] = " ".join(response.css('#main-text *::text').getall()).strip()
        
        related_links = response.css('#related-entries a::attr(href)').getall()
        adapter['related_entries'] = [response.urljoin(link) for link in related_links]

        # We no longer need the full response object, so we can remove it.
        del adapter['response']

        spider.crawler.stats.inc_value('articles_parsed')
        
        return item

class LatexProcessingPipeline:
    """
    PIPELINE STAGE 2 (Priority: 300)
    Takes the 'body_text' field, finds all unique LaTeX expressions,
    and replaces them with indexed placeholders.
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        raw_text = adapter.get('body_text')

        if not raw_text:
            adapter['text_with_placeholders'] = ''
            adapter['math_expressions'] = []
            if 'body_text' in adapter:
                del adapter['body_text']
            return item

        # --- NEW DEDUPLICATION LOGIC ---
        unique_expressions = []
        expression_to_id = {}

        def latex_replacer(match):
            expression = match.group(0)
            
            # Check if we've seen this expression before.
            if expression in expression_to_id:
                # If yes, get its existing ID.
                expr_id = expression_to_id[expression]
            else:
                # If no, add it to our list of unique expressions and assign a new ID.
                expr_id = len(unique_expressions)
                unique_expressions.append(expression)
                expression_to_id[expression] = expr_id
            
            # Return a placeholder with the unique ID.
            return f"[MATH_{expr_id}]"

        latex_pattern = re.compile(r'(\\\(.*?\\\)|\\\[.*?\\\])', re.DOTALL)
        text_with_placeholders = latex_pattern.sub(latex_replacer, raw_text)

        # Add the new processed fields to the item.
        adapter['text_with_placeholders'] = text_with_placeholders
        adapter['math_expressions'] = unique_expressions # This is now a list of unique strings.
        
        spider.logger.info(f"Processed LaTeX for '{adapter['title']}', found {len(unique_expressions)} unique expressions.")
        
        # Remove the temporary body_text field as it's now processed.
        if 'body_text' in adapter:
            del adapter['body_text']
        
        spider.crawler.stats.inc_value('latex_processed')

        return item

class SepStoragePipeline:
    """
    PIPELINE STAGE 3 (Priority: 400)
    Takes the final, fully processed item and saves it as a single,
    structured JSON file.
    """
    def open_spider(self, spider):
        self.output_dir = "processed_articles"
        os.makedirs(self.output_dir, exist_ok=True)
        spider.logger.info(f"Saving processed articles to '{self.output_dir}/'")

    def clean_for_filename(self, text: str) -> str:
        if not text: return "untitled"
        text = re.sub(r'[^a-zA-Z0-9_.-]+', '_', text)
        return text.lower().strip('_')

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        base_filename = self.clean_for_filename(adapter.get('title', 'untitled'))
        output_filepath = os.path.join(self.output_dir, f"{base_filename}.json")

        try:
            # ItemAdapter.asdict() gives a clean dictionary representation of the item.
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(adapter.asdict(), f, indent=4, ensure_ascii=False)
            spider.logger.info(f"Successfully saved article to {output_filepath}")
            spider.crawler.stats.inc_value('articles_saved')
        except Exception as e:
            spider.logger.error(f"Failed to save item to {output_filepath}: {e}")
            spider.crawler.stats.inc_value('save_errors')
            
        return item
