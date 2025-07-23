import os
import re

class SepStoragePipeline:
    def clean_for_filename(self, text: str) -> str:
        # Should this throw an error if not text?
        if not text: return f"untitled_{hash(text)}"
        text = re.sub(r'https?://', '', text)
        text = re.sub(r'[^a-zA-Z0-9_.-]+', '_', text)
        return text.lower().strip('_')

    def process_item(self, item, spider):
        base_filename = self.clean_for_filename(item['title'])
        if item.get('preamble_text'):
            dir_path = os.path.join(os.curdir, 'scraped_preambles')
            os.makedirs(dir_path, exist_ok=True)
            path = os.path.join(dir_path, base_filename + '.txt')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(item['preamble_text'])
        if item.get('body_text'):
            dir_path = os.path.join(os.curdir, 'scraped_article_bodies')
            os.makedirs(dir_path, exist_ok=True)
            path = os.path.join(dir_path, base_filename + '.txt')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(item['body_text'])
        if item.get('related_entries'):
            dir_path = os.path.join(os.curdir, 'scraped_link_refs')
            os.makedirs(dir_path, exist_ok=True)
            path = os.path.join(dir_path, base_filename + '.txt')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"ROOT: {item['url']}\n")
                f.write("\n".join(item['related_entries']))
        return item