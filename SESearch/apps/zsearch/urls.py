from django.urls import re_path
from SESearch.apps.zsearch.view import views
urlpath = [
    # re_path(r'', views.IndexView.as_view({'get':'index'}))

    url(r'^suggest/$', SearchSuggest.as_view(), name="suggest"),

    url(r'^search/$', SearchView.as_view(), name="search"),
]