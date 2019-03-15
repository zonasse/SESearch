from django.db import models

# Create your models here.
from elasticsearch_dsl import DocType, Completion,Keyword, Text, Integer, Boolean, Nested
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["localhost"])

class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer("ik_max_word", filter=["lowercase"])

class MovieType(DocType):
    #搜索建议词
    suggest = Completion(analyzer = ik_analyzer)
    #电影id，豆瓣电影自带id，dytt则为md5(movie_url)
    movie_id = Keyword()
    #电影标题
    movie_title = Text(analyzer = 'ik_max_word')
    #电影导演
    movie_directors = Text(analyzer = 'ik_max_word')
    #电影评分
    movie_rate = Keyword()
    #电影url
    movie_url = Keyword()
    #电影演员
    movie_casts = Text(analyzer = 'ik_max_word')
    #电影封面
    movie_cover = Keyword()
    #电影简介
    movie_abstract = Text(analyzer = 'ik_max_word')
    #电影下载链接
    movie_download_url = Keyword()
    #todo 增加电影上映时间
    class Meta:
        index = 'sesearch'
        doc_type = 'movie'

if __name__ == "__main__":
    MovieType.init()
