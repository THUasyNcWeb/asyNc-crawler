# asyNc-crawler

> 小组：转生成为异世界贤者之魔王竟是我的队友

本仓库为2022-2023秋季学期软件工程课程新闻搜索系统项目子模块

项目[父模块](https://gitlab.secoder.net/asyNc/asyNc-web)

## 环境配置

本仓库使用 python3.9，我们建议您使用 conda 进行虚拟环境的创建：

```shell
conda create -n site python=3.9
conda activate site
```

之后使用 pip3 安装依赖：

```shell
pip install -r requirements.txt
```

## 数据库配置

应依次创建如下文件：
- 配置 PostgreSQL 数据库
  
  `config/config.json`
  ```json
  {
      "hostname": "127.0.0.1",
      "port": "5432",
      "username": "postgres",
      "password": "kming",
      "database": "web"
  }
  ```
- 配置 Redis 数据库
  
  `config/redis.json`
  ```json
  {
      "host": "127.0.0.1",
      "port": 6379,
      "password": "123456"
  }
  ```
  同时将 `news_crawler/news_crawler/settings.py` 第 108 - 112 行修改为相应的 redis 数据库配置
- 配置 ES 数据库
  
  `config/es.json`
  ```json
  {
      "url": "43.143.147.5",
      "port": 9200
  }
  ```

## 使用方式

首先切换目录至 news_crawler 文件夹下

```shell
cd news_crawler
```

全量爬虫：

```shell
scrapy crawl TencentNewsAllQuantity [-a begin_date='20220101'] [-a end_data='20221031'] [-a data_table='news']

scrapy crawl XinhuaNewsAllQuantity [-a begin_date='20220101'] [-a end_data='20221031'] [-a data_table='news']

scrapy crawlall # 同时启动腾讯新网&新华网的全量爬虫
```

增量爬虫：

```shell
scrapy crawl TencentNewsIncre [-a data_table='news'] [-a attribution='main']

scrapy crawl XinhuaNewsIncre [-a data_table='news'] [-a attribution='main']

scrapy crawl WangyiNewsIncre [-a data_table='news'] [-a attribution='main']

scrapy crawl ChinaDailyNewsIncre [-a data_table='news'] [-a attribution='main']

scrapy crawl XinhuaEngNewsIncre [-a data_table='news'] [-a attribution='main']
```