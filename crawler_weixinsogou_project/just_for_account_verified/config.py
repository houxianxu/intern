import redis
# Redis host address
REDIS_HOST_ADDRESS = 'localhost'
r = redis.StrictRedis(host=REDIS_HOST_ADDRESS, port=6379, db=0)


# The parameter of MySQL 
MYSQL_HOST = "192.168.1.187"
MYSQL_USER = "houxianxu"
MYSQL_PASSWD = "houxianxu"
MYSQL_DB = "babysitter_simple"
MYSQL_CHARSET = "utf8"


# ip available
proxy_list = [
               {'http':"http://qwby:qwby99233@192.168.1.17:54321"},
               {'http':"http://qwby:qwby99233@192.168.1.18:54321"},
               {'http':"http://qwby:qwby99233@192.168.1.19:54321"},
               {'http':"http://qwby:qwby99233@192.168.1.20:54321"},
               {'http':"http://qwby:qwby99233@192.168.1.22:54321"}

]


# fake ua
USER_AGENT_LIST = [
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) )",
	"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) )",
	"Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.79 Safari/535.11",
	"Opera/9.80 (Windows NT 5.1; U; Edition IBIS; zh-cn) Presto/2.10.229 Version/11.62",
	"Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko/20100101 Firefox/11.0",
	"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; 360SE)",
	"Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ;  QIHU 360EE)",
	"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; Maxthon/3.0)",
	"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; TencentTraveler 4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) )",
	"Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.5 Safari/534.55.3"
]

# The max number of nav_pages 
MAX_NAV_PAGE = 20