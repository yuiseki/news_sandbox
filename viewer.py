from flask import Flask, request, send_from_directory
from flask.ext.mongoengine import MongoEngine

from bson import json_util

from models import News

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    "DB": "newsclient"
    }
db = MongoEngine()
db.init_app(app)

@app.route('/')
def root():
  return send_from_directory('static', 'index.html')

@app.route('/news')
def getnews():
  per_page = 30
  page = request.args.get('page', 0)
  result = News.objects(facebook_count__gt=0, twitter_count__gt=0, generated_summary__exists=1)\
      .exclude('id', 'html', 'extract_textmore', 'extract_textbody', 'extract_content')\
      .order_by('-published_at')\
      .limit(per_page).skip(per_page*int(page))
  news = result.to_json()
  return news


if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')
