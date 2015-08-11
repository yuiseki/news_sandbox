# -*- coding: utf-8 -*-
from multiprocessing import Pool
import time
import datetime

import requests
from twitter import *

from mongoengine.queryset import DoesNotExist
from mongoengine import connect

connect('newsclient')
from models import News, Tweets

import yaml

f = open("config/default.yaml", 'r')
config = yaml.load(f)
f.close()

ACCESS_TOKEN = config["twitter"]["access_token"]
ACCESS_TOKEN_SECRET = config["twitter"]["access_token_secret"]
CONSUMER_KEY = config["twitter"]["consumer_key"]
CONSUMER_SECRET = config["twitter"]["consumer_secret"]

def watch_stream():
  auth = OAuth(ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
  stream = TwitterStream(auth=auth, domain="userstream.twitter.com")
  for msg in stream.user():
    if msg.has_key('text'):
      if len(msg['entities']['urls']) > 0:
        user_id = msg['user']['id_str']
        user_name = msg['user']['name']
        screen_name = msg['user']['screen_name']
        text = msg['text']
        tweet_id = msg['id_str']
        timestamp = msg['timestamp_ms']
        created_dt =  datetime.datetime.fromtimestamp(int(timestamp)/1000.0)
        for eurl in msg['entities']['urls']:
          link = eurl['expanded_url']
          if "flic.kr" in link or "twitter.com" in link:
            continue
          try:
            hres = requests.head(link, timeout=3)
            if hres.status_code == 301 or hres.status_code == 302:
              link = hres.headers.get("location", link)
            for s in ["?utm_", "&utm_", "%26utm_", "?from=", "?ref=", "&ref=" "?ncid=rss", "?n_cid="]:
              if s in link:
                idx = link.find(s)
                link = link[:idx]
            if link == "h":
              print ">>", link
              print ">>", eurl['expanded_url']
            tweet = Tweets(
                url=link, text=text,
                tweet_id=tweet_id,
                user_id=user_id,
                user_name=user_name,
                screen_name=screen_name,
                created_at=created_dt
                )
            tweet.save()
            fetch(link, created_dt)
          except requests.exceptions.Timeout, e:
            print ">>", "error", link, e
          except requests.exceptions.SSLError, e:
            print ">>", "error", link, e
          except requests.exceptions.ConnectionError ,e:
            print ">>", "error", link, e
          #pool.apply_async(fetch, [link, created_dt])
  print "stream end"

def fetch(link, dt):
  try:
    news = News.objects.get(url=link)
    news = None
    print ">>", "exists", link
  except DoesNotExist, e:
    print ">>", "fetch", link
    try:
      res = requests.get(link, timeout=3)
      print ">>", "get done", link
      res.encoding = res.apparent_encoding
      if not "text" in res.headers.get("content-type", "none"):
        return
      if res.apparent_encoding is not None:
        html = unicode(res.content, res.apparent_encoding)
        news = News(url=link, html=html, published_at=dt)
        news.save()
        news = None
    except UnicodeDecodeError, e:
      print ">>", "error", link, e
    except requests.exceptions.Timeout, e:
      print ">>", "error", link, e
    except requests.exceptions.MissingSchema, e:
      print ">>", "error", link, e
    except requests.exceptions.SSLError, e:
      print ">>", "error", link, e
    print ">>", "extract done", link
  print "\n------------------------\n"


if __name__ == '__main__':
  try:
    while(True):
      watch_stream()
  except Exception, e:
    pass

