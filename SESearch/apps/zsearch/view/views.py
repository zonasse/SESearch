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
            suggestions = s.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_datas.append(source["title"])
        return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(viewsets.ViewSet):
    def search(self, request):
        key_words = request.GET.get("key","")
        s_type = request.GET.get("key_type", "movie")

        redis_cli.zincrby("search_keywords_set", key_words)

        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        page = request.GET.get("page", "1")
        try:
            page = int(page)
        except:
            page = 1

        douban_movie_count = redis_cli.get("douban_movie_count")
        dytt_movie_count = redis_cli.get("dytt_movie_count")

        start_time = datetime.now()
        response = client.search(
            index= "sesearch",
            body={
                "query":{
                    "multi_match":{
                        "query":key_words,
                        "fields":["movie_title", "movie_directors", "movie_casts","movie_abstract"]
                    }
                },
                "from":(page-1)*10,
                "size":10,
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "title": {},
                        "content": {},
                    }
                }
            }
        )

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
            if "title" in hit["highlight"]:
                hit_dict["title"] = "".join(hit["highlight"]["title"])
            else:
                hit_dict["title"] = hit["_source"]["title"]
            if "content" in hit["highlight"]:
                hit_dict["content"] = "".join(hit["highlight"]["content"])[:500]
            else:
                hit_dict["content"] = hit["_source"]["content"][:500]

            hit_dict["create_date"] = hit["_source"]["create_date"]
            hit_dict["url"] = hit["_source"]["url"]
            hit_dict["score"] = hit["_score"]

            hit_list.append(hit_dict)

        return render(request, "result.html", {"page":page,
                                               "all_hits":hit_list,
                                               "key_words":key_words,
                                               "total_nums":total_nums,
                                               "page_nums":page_nums,
                                               "last_seconds":last_seconds,
                                               "douban_movie_count":douban_movie_count,
                                               "dytt_movie_count":dytt_movie_count,
                                               "topn_search":topn_search})
