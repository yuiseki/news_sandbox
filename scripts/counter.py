import time

from mongoengine import connect
connect('newsclient')

from models import News

#for news in News.objects(facebook_count__gte=800).limit(1000):
for news in News.objects(hatebu_count__exists=0).limit(1000):
  if "rssad" in news.url:
    continue

  if news.twitter_count is None:
    news.get_twitter_count()
  if news.facebook_count is None:
    news.get_facebook_count()
  if news.hatebu_count is None:
    news.get_hatebu_count()

  if news.hatebu_count > 100 or\
      news.facebook_count > 800 or\
      news.twitter_count > 1200:
    print "tw", news.twitter_count
    print "fb", news.facebook_count
    print "hatebu", news.hatebu_count
    print news.og_title
    print news.url
  news.save()
  time.sleep(1)
