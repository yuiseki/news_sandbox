from datetime import datetime, timedelta
import time

import feedparser
import requests

from mongoengine.queryset import DoesNotExist
from mongoengine import fields
from mongoengine import connect

from models import News

connect('newsclient')

"""
items = feedparser.parse("http://b.hatena.ne.jp/yuiseki/favorite.rss")
for entry in items.entries:
  title = entry.title
  dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
  print dt, title
  link = entry.link
  hres = requests.head(link)
  if hres.status_code == 302:
    link = hres.headers["location"]
    link = link.replace("?ref=rss", "")
  print link
  try:
    news = News.objects.get(url=link)
  except DoesNotExist, e:
    res = requests.get(link)
    res.encoding = res.apparent_encoding
    html = unicode(res.content, res.apparent_encoding)
    news = News(url=link, html=html, title=title, published_at=dt)
    news.extract()
    news.p()
    time.sleep(1)
    #news.save()
"""


feeds = []
# impress
feeds.extend([
  "http://rss.rssad.jp/rss/internetwatch/internet.rdf",
  "http://rss.rssad.jp/rss/cloudwatch/cloud.rdf",
  "http://rss.rssad.jp/rss/dcwatch/digicame.rdf",
  "http://rss.rssad.jp/rss/avwatch/av.rdf",
  "http://rss.rssad.jp/rss/k-taiwatch/k-tai.rdf",
  "http://rss.rssad.jp/rss/gamewatch/index.rdf"
  ])
# mynavi
feeds.extend([
  "http://feeds.journal.mycom.co.jp/haishin/rss/index",
  "http://feeds.journal.mycom.co.jp/haishin/rss/pc",
  "http://feeds.journal.mycom.co.jp/haishin/rss/keitai",
  "http://feeds.journal.mycom.co.jp/haishin/rss/kaden",
  "http://feeds.journal.mycom.co.jp/haishin/rss/life",
  "http://feeds.journal.mycom.co.jp/haishin/rss/hobby",
  "http://feeds.journal.mycom.co.jp/haishin/rss/enterprise",
  "http://feeds.journal.mycom.co.jp/haishin/rss/marketing",
  "http://feeds.journal.mycom.co.jp/haishin/rss/devse",
  "http://feeds.journal.mycom.co.jp/haishin/rss/technology"
  ])
for url in feeds:
  print url
  items = feedparser.parse(url)
  for entry in items.entries:
    title = entry.title
    dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
    print dt, title
    link = entry.link
    hres = requests.head(link)
    if hres.status_code == 302:
      link = hres.headers["location"]
      link = link.replace("?ref=rss", "")
    print link
    try:
      news = News.objects.get(url=link)
    except DoesNotExist, e:
      res = requests.get(link)
      res.encoding = res.apparent_encoding
      html = unicode(res.content, res.apparent_encoding)
      time.sleep(1)
      news = News(url=link, html=html, title=title, published_at=dt)
      news.save()

# fetch nhk
for cat in range(1, 7):
  for day in range(7):
    target = datetime.now() - timedelta(day)
    date =  target.strftime("%Y%m%d")
    unixtime = str(int(time.time()))
    cat = str(cat)
    url = "http://www3.nhk.or.jp/news/html/{date}/xml/cat{cat}.xml?t={unixtime}".format(date=date, unixtime=unixtime, cat=cat)
    print url
    news = feedparser.parse(url)
    for entry  in news.entries:
      print entry.title
      print entry.link
      link = entry.link
      try:
        news = News.objects.get(url=link)
      except DoesNotExist, e:
        res = requests.get(link)
        html = res.content
        time.sleep(1)
        news = News(url=link, html=html, title=entry.title)
        news.save()
"""
"""
