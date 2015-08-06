# -*- coding: utf-8 -*-
import re
import time
from datetime import datetime
from mongoengine.queryset import DoesNotExist
from mongoengine import fields
from mongoengine import connect

from bs4 import BeautifulSoup

from models import News

connect('newsclient')



def extract_nhk_news(news, soup):
  title = soup.select("span.contentTitle")[0].string
  print title
  date = soup.select("span#news_date")[0].string
  time = soup.select("span#news_time")[0].string
  strdt = u"2015年"+date+time
  print strdt
  dt = datetime.strptime(strdt.encode('utf-8'), '%Y年%m月%d日%H時%M分')
  print dt
  textbody = soup.select("div#news_textbody")[0].string
  textmore = soup.select("div#news_textmore")[0].getText()
  news.extract_title = title
  news.extract_textbody = textbody
  news.extract_textmore = textmore
  news.extract_image = image
  news.published_at = dt


for news in News.objects(extract_content__exists=0):
#for news in News.objects.all().limit(10):
#for news in News.objects.filter(url__contains="impress").limit(5).order_by("-published_at"):
#for news in News.objects.all():
  print ">>>>>>>>>>-------------------"
  print news.extract_content
  soup = BeautifulSoup(news.html, "lxml")
  extract_ogp(news, soup)
  extract_content(news, soup)
  print_news(news)
  news.save()
  time.sleep(1)
  print "-------------------<<<<<<<<<<\n"



