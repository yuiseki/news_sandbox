from flask import Flask, request, send_from_directory, jsonify
from flask.ext.mongoengine import MongoEngine
from mongoengine import Q

import datetime
from bson import json_util
import json
import re

from models import News, Tweets

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    "DB": "newsclient"
    }
db = MongoEngine()
db.init_app(app)

@app.route('/')
def root():
  return send_from_directory('static', 'index.html')

@app.route('/rank')
def getrank():
  print "----------------"
  end = datetime.datetime.now()
  print end
  start = end - datetime.timedelta(hours=6)
  cursor = Tweets._get_collection().aggregate([\
      {"$match": { "url":{"$not":re.compile("^https?://(live.nicovideo.jp|www.ustream.tv)/")}, "created_at": {"$gte":start, "$lte":end} } },\
      {"$group":{"_id":{"url":"$url", "user":"$screen_name"}, "count":{"$sum": 1} }},\
      {"$group":{"_id":"$_id.url", "count":{"$sum": 1} }},\
      {"$sort":{"count":-1}}, {"$limit":30}\
    ])
  rank = list(cursor)
  results = []
  for r in rank:
    print r
    news = News.objects(url=r["_id"])\
      .exclude('id', 'html', 'extract_textmore', 'extract_textbody', 'extract_content', 'title_noun_list', 'description_noun_list')
    if len(news) is 0:
      continue
    new = news[0]
    obj = new.to_mongo().to_dict()
    obj["day_count"] = r["count"]
    results.append(obj)
  return jsonify({"results":results})

@app.route('/news')
def getnews():
  per_page = 10
  page = request.args.get('page', 0)
  result = News.objects(\
        Q(hatebu_count__gt=0) |\
        Q(twitter_count__gt=10)\
      )\
      .exclude('id', 'html', 'extract_textmore', 'extract_textbody', 'extract_content')\
      .order_by('-published_at')\
      .limit(per_page).skip(per_page*int(page))
  news = result.to_json()
  return news


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')
