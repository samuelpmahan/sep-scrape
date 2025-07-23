import logging
from scrapy import signals
from scrapy.utils.log import failure_to_exc_info
from twisted.internet import task

logger = logging.getLogger(__name__)

class ProgressMonitor:
    def __init__(self, stats, total_articles=1800, interval=30.0):
        self.stats = stats
        self.total_articles = total_articles
        self.interval = interval
        self.task = None

    @classmethod
    def from_crawler(cls, crawler):
        # The total number of articles can be passed via settings if you want.
        total_articles = crawler.settings.getint('TOTAL_ARTICLES', 1800)
        interval = crawler.settings.getfloat('PROGRESS_INTERVAL', 30.0)
        
        ext = cls(crawler.stats, total_articles, interval)
        
        # Connect the extension to the signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        
        return ext

    def spider_opened(self, spider):
        logger.info(f"OPENED {spider.name}, starting progress monitor.")
        self.task = task.LoopingCall(self.log_progress)
        self.task.start(self.interval)

    def spider_closed(self, spider, reason):
        logger.info(f"CLOSED {spider.name}, reason: {reason}")
        if self.task and self.task.running:
            self.task.stop()
        # Log final stats one last time
        self.log_progress()

    def log_progress(self):
        # Get the current stats
        items_scraped = self.stats.get_value('item_scraped_count', 0)
        parsed = self.stats.get_value('articles_parsed', 0)
        processed = self.stats.get_value('latex_processed', 0)
        saved = self.stats.get_value('articles_saved', 0)
        
        # Calculate percentage
        percent_complete = (saved / self.total_articles) * 100 if self.total_articles > 0 else 0
        
        # Log the progress line
        logger.info(
            f"PROGRESS: [{percent_complete:.2f}%] "
            f"Scraped: {items_scraped} | Parsed: {parsed} | Processed: {processed} | Saved: {saved} "
            f"of {self.total_articles}"
        )
