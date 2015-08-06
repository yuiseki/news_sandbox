# -*- coding: utf-8 -*-
import re
from datetime import datetime

from bs4 import BeautifulSoup
import requests
import nltk
import MeCab

from mongoengine.document import Document
from mongoengine import fields

class TextBlock:
  def __init__(self, soup, index):
    self.soup = soup
    self.index = index
    self.text = ""
    self.score = 0
    self.text_ratio = 0
    self.punctuation_count = 0
    self.child_count = 0
    self.list_count = 0
    self.anchor_count = 0
    self.getScore()
  def getScore(self):
    self.text = self.soup.getText()
    # 句読点をベースのスコアとする
    self.punctuation_count += self.text.count(u'、')
    self.punctuation_count += self.text.count(u'。')
    self.score = self.punctuation_count
    # contentっぽいマークアップだったらスコアを上げる
    soup_class = self.soup.get("class")
    soup_id = self.soup.get("id")
    if soup_class:
      if "content" in soup_class:
        self.score = self.score*20
    if soup_id:
      if "content" in soup_id:
        self.score = self.score*20
    # リンクのリストっぽいのはスコアを減らす
    self.list_count = len(self.soup.select('li'))
    if self.list_count > 5:
      self.score = self.score*0.01
    if u"著作権" in self.text:
      self.score = self.score*0.01
    #self.anchor_count = len(self.soup.select('a'))
    #self.child_count = len(self.soup.findChildren())
    #self.text_density = len(self.text)*1.0/self.child_count
    # ブロック全体における文字の比率
    #self.text_ratio = len(self.text)*1.0/len(str(self.soup))
    #self.score = self.score*self.text_ratio
    # comment
    #badwords = ["javascript:", "function", "head", "foot"]
    #for word in badwords:
    #  if word in str(self.soup):
    #    self.score = self.score*0.01

class News(Document):
  url  = fields.StringField(unique=True, required=True)
  html = fields.StringField()
  html_encoding = fields.StringField()
  published_at = fields.DateTimeField()

  title = fields.StringField()
  og_title = fields.StringField()
  og_description = fields.StringField()
  og_image = fields.StringField()

  extract_category = fields.StringField()
  extract_title = fields.StringField()
  extract_content = fields.StringField()
  extract_textbody = fields.StringField()
  extract_textmore = fields.StringField()
  extract_image     = fields.StringField()
  title_noun_list   = fields.ListField(fields.StringField())
  description_noun_list   = fields.ListField(fields.StringField())
  generated_summary = fields.StringField()

  twitter_count = fields.IntField()
  facebook_count = fields.IntField()
  facebook_comment_count = fields.IntField()
  hatebu_count = fields.IntField()
  social_score = fields.FloatField()

  soup=None

  def save(self, *args, **kwargs):
    self.extract()
    super(News, self).save(*args, **kwargs)

  def extract(self):
    self.soup = BeautifulSoup(self.html, "lxml")
    if self.extract_content is None:
      self.extract_content_()
    if self.og_title is None:
      self.extract_ogp()
    if self.twitter_count is None:
      self.get_twitter_count()
    if self.facebook_count is None:
      self.get_facebook_count()
    if self.hatebu_count is None:
      self.get_hatebu_count()

  def get_twitter_count(self):
    res = requests.get("http://urls.api.twitter.com/1/urls/count.json?url="+self.url)
    json = res.json()
    self.twitter_count = json["count"]

  def get_hatebu_count(self):
    res = requests.get("http://api.b.st-hatena.com/entry.count?url="+self.url)
    if len(res.content)>1:
      self.hatebu_count = int(res.content)
    else:
      self.hatebu_count = 0

  def get_facebook_count(self):
    res = requests.get("http://graph.facebook.com/"+self.url)
    json = res.json()
    if json.has_key("shares"):
      self.facebook_count = json["shares"]
    else:
      self.facebook_count = 0
    if json.has_key("comments"):
      self.facebook_comment_count = json["comments"]
    else:
      self.facebook_comment_count = 0

  def calc_social_score(self):
    self.social_score = (self.twitter_count*0.1)\
        +(self.facebook_count*1.2)\
        +(self.facebook_comment_count*1.5)\
        +(self.hatebu_count*1.2)

  def generate_summary(self):
    def extract_words(text):
      text =  text.encode("utf-8") if isinstance(text,unicode) else text
      mecab = MeCab.Tagger("-Ochasen -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd")
      node = mecab.parseToNode(text)
      words = []
      while node:
        fs = node.feature.split(",")
        if (node.surface is None):
          node = node.next
          continue
        if node.surface == "":
          node = node.next
          continue
        if '名詞' in fs[0]:
          words.append(unicode(node.surface, 'utf-8'))
        node = node.next
      return words
    if not self.og_title is None:
      self.title_noun_list = extract_words(self.og_title)
    if not self.og_description is None:
      self.description_noun_list = extract_words(self.og_description)
    from heapq import merge
    self.frequent_noun_list = list(merge(self.title_noun_list, self.description_noun_list))

    if len(self.extract_content) is 0:
      self.generated_summary = u""
      return

    lines = self.extract_content.split(u'。')
    lines_score = {}
    # TODO 文の長さと名詞の密度を考慮すべき
    for idx, line in enumerate(lines):
      line_score = 0
      line_noun_list = extract_words(line)
      for noun in self.frequent_noun_list:
        line_score += line_noun_list.count(noun)
      lines_score[line] = line_score

    # 並び順は変えずにスコアの高い文を3個抜き出す
    sorted_lines_score = sorted(lines_score.items(), key=lambda x:-x[1])
    top_score_lines = map(lambda x:x[0], sorted_lines_score[0:3])
    summary_lines = []
    for idx, line in enumerate(lines):
      if line in top_score_lines:
        summary_lines.append(line)

    self.generated_summary = u"。\n".join(summary_lines)+u"。"

  def extract_ogp(self):
    def get_select(select):
      tags = self.soup.select(select)
      if len(tags) > 0:
        return tags[0].get("content")
      else:
        return None
    og_title = get_select('meta[property="og:title"]')
    if og_title is None:
      og_title = get_select('meta[name="title"]')
    self.og_title = og_title
    og_description = get_select('meta[property="og:description"]')
    if og_description is None:
      og_description = get_select('meta[name="description"]')
    self.og_description = og_description
    self.og_image = get_select('meta[property="og:image"]')

  def extract_content_(self):
    if self.soup is None:
      self.soup = BeautifulSoup(self.html, "lxml")

    index = 0
    targets = self.soup.findAll("div")
    text_blocks = []
    for target in targets:
      index +=1
      block = TextBlock(target, index)
      text_blocks.append(block)

    score_sorted = sorted(text_blocks, key=lambda x: -x.score)
    if len(score_sorted) is 0:
      self.extract_content = "null"
      return

    def clean_lines(text):
      lines = text.split("\n")
      body = ""
      for line in lines:
        line = unicode(line).strip()
        if re.search(u"。$", line):
          body += unicode(line).strip()
      return body

    first = score_sorted[0]
    second = score_sorted[1]
    if second.soup in first.soup.next_siblings:
      print "next siblings"
      text = clean_lines(first.text+second.text)
    elif second.soup in first.soup.previous_siblings:
      print "previous siblings"
      text = clean_lines(second.text+first.text)
    else:
      print "only child"
      text = clean_lines(first.text)
    self.extract_content = text

  def p(self):
    print "-", self.url
    print "-", self.og_title
    print "-", self.og_description
    print "-", self.og_image
    print "-", self.extract_content
