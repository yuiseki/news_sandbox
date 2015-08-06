import time
from mongoengine import connect
from mongoengine import Q
from models import News
connect('newsclient')

queryset = News.objects(\
    Q(generated_summary__exists=0) &\
    Q(url__not__contains="rssad") )#  &\
    #Q(url__not__contains="nhk") ).limit(50)

for news in queryset:
  print ">>>>>>>>>>-------------------"
  print news.url
  print news.og_title
  news.extract_content_()
  news.generate_summary()
  print news.generated_summary
  news.save()
  #time.sleep(5)
  print "-------------------<<<<<<<<<<\n"
