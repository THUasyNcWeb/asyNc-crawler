from itemadapter import ItemAdapter


class NewsCrawlerPipeline:
    def process_item(self, item, spider):
        return item

    def open_spider(self, spider):
        self.file = open('test.html', 'w', encoding='utf-8')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        self.file.write(str(item['text']))