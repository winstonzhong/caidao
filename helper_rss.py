import feedparser


def parse_rss_feed(url):
    # 解析RSS订阅源
    feed = feedparser.parse(url)

    # 检查是否解析成功
    if feed.bozo:
        print(f"解析失败：{feed.bozo_exception}")
        return

    # # 获取订阅源的元数据
    # print(f"订阅源标题：{feed.feed.title}")
    # print(f"订阅源链接：{feed.feed.link}")
    # print(f"订阅源描述：{feed.feed.description}")
    # print(f"订阅源更新时间：{feed.feed.updated}")

    # 遍历文章列表
    print("\n文章列表：")
    for entry in feed.entries:
        print(f"标题：{entry.title}")
        print(f"链接：{entry.link}")
        print(f"发布时间：{entry.published}")
        print(f"摘要：{entry.summary}")
        print("-" * 50)
        yield {'Title': entry.title, '外部url': entry.link, '文章内容概要': entry.summary}


if __name__ == "__main__":
    # 示例：解析一个RSS订阅源
    rss_url = "https://feed.cnblogs.com/news/rss"
    for x in parse_rss_feed(rss_url):
        print(x)
