import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOT_NAME = "scrapy_sep"

SPIDER_MODULES = ["scrapy_sep.spiders"]
NEWSPIDER_MODULE = "scrapy_sep.spiders"

ADDONS = {}

LOG_LEVEL = "INFO"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "scrapy_sep (+MY LEARNING PROJECT)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 5
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = os.path.join(BASE_DIR, 'sep_html_cache')
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "scrapy_sep.pipelines.ParsingPipeline": 200,
    "scrapy_sep.pipelines.LatexProcessingPipeline": 300,
    "scrapy_sep.pipelines.SepStoragePipeline": 400,
}

EXTENSIONS = {
   'scrapy_sep.extensions.ProgressMonitor': 500,
}

# Optional: You can configure the total articles and interval here
TOTAL_ARTICLES = 1800
PROGRESS_INTERVAL = 30.0 # seconds

# --- Enable the Pipeline ---
# ITEM_PIPELINES is defined below

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "scrapy_sep.middlewares.ScrapySepSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "scrapy_sep.middlewares.ScrapySepDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False
