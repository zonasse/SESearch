from django.test import TestCase

# Create your tests here.
import re

str1 = "xxx出生于1995年6月1日"
str2 = "xxx出生于1995/6/1"
str3 = "xxx出生于1995-6-1"
str4 = "xxx出生于1995-06-01"
str5 = "xxx出生于1995-06"
my_tuple = (str1,str2,str3,str4,str5)

pattern = ".*出生于(\d{4}[年/-]((\d+$)|(\d+[月/-]((\d+$)|(\d+日$)))))"
for item in my_tuple:
    res = re.match(pattern,item)
    print(res.group(1))