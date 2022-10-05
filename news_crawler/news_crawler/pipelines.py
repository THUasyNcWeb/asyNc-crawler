from scrapy.exporters import JsonItemExporter


class NewsCrawlerPipeline:
    def process_item(self, item, spider):
        pass

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        pass


class JsonExporterPipleline(object):
    def __init__(self):
        self.file = open('test.json', 'wb')
        self.exporter = JsonItemExporter(
            self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item
