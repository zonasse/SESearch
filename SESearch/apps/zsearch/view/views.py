from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets
from datetime import datetime
from elasticsearch import Elasticsearch
from SESearch.apps.zsearch.model.models import *
import json
import redis
# Create your views here.
redis_cli = redis.StrictRedis()
client = Elasticsearch(hosts=["127.0.0.1"])


class IndexView(viewsets.ViewSet):
    def index(self,request):
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        topn_search = [ search_word.decode() for search_word in topn_search]
        return render(request,'index.html',{"topn_search":topn_search})

# Create your views here.
class SuggestView(viewsets.ViewSet):
    def suggest(self, request):
        key_words = request.GET.get('key','')
        re_datas = []
        if key_words:
            s = MovieType.search()
            s = s.suggest('my_suggest', key_words, completion={
                "field":"suggest", "fuzzy":{
                    "fuzziness":2
                },
                "size": 10,
            })
            # todo 处理无搜索建议时的异常

            suggestions = s.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_datas.append(source["movie_title"])
        return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(viewsets.ViewSet):
    def search(self, request):
        key_word = request.GET.get("key","")
        s_type = request.GET.get("key_type", "movie")

        redis_cli.zincrby("search_keywords_set", 1,key_word)

        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        topn_search = [ search_word.decode() for search_word in topn_search]

        page = request.GET.get("page", "0")
        try:
            page = int(page)
        except:
            page = 0

        douban_movie_count = int(redis_cli.get("douban_movie_count"))
        dytt_movie_count = int(redis_cli.get("dytt_movie_count"))

        start_time = datetime.now()
        response = client.search(
            index= "sesearch",
            body={
                "query":{
                    "multi_match":{
                        "query":key_word,
                        "fields":["movie_title","movie_abstract"]
                    }
                },
                "from":(page)*10,
                "size":10,
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "movie_title": {},
                        "movie_abstract": {},
                    }
                }
            }
        )


        page += 1
        end_time = datetime.now()
        last_seconds = (end_time-start_time).total_seconds()
        total_nums = response["hits"]["total"]
        if (page%10) > 0:
            page_nums = int(total_nums/10) +1
        else:
            page_nums = int(total_nums/10)
        hit_list = []
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            if "movie_title" in hit["highlight"]:
                hit_dict["movie_title"] = "".join(hit["highlight"]["movie_title"])
            else:
                hit_dict["movie_title"] = hit["_source"]["movie_title"]
            if "movie_abstract" in hit["highlight"]:
                hit_dict["movie_abstract"] = "".join(hit["highlight"]["movie_abstract"])[:500]
            else:
                hit_dict["movie_abstract"] = hit["_source"]["movie_abstract"][:500]

            # hit_dict["create_date"] = hit["_source"]["create_date"]
            hit_dict["movie_url"] = hit["_source"]["movie_url"]
            hit_dict["movie_score"] = hit["_score"]

            hit_list.append(hit_dict)
        return render(request, "result.html", {"page":page,
                                               "all_hits":hit_list,
                                               "key_word":key_word,
                                               "total_nums":total_nums,
                                               "page_nums":page_nums,
                                               "last_seconds":last_seconds,
                                               "douban_movie_count":douban_movie_count,
                                               "dytt_movie_count":dytt_movie_count,
                                               "topn_search":topn_search})
