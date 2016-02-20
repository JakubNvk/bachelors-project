from bs4 import BeautifulSoup
from parse import *
from parse import compile

soup = BeautifulSoup(open("stops.html"))
l = compile("https://tools.wmflabs.org/query2map/queryinmap.php?BBOX={}&name={}&key=public_transport&value=stop_position&types=points-lines-areas-infos")
for link in soup.find_all('a'):
    parsed_link = l.parse(link.get('href'))
    stop_name = link.string
    res = []
    res.extend(parsed_link[0].split(','))
    print stop_name.encode(encoding='UTF-8')
    print res[0] + ", " + res[1] + "\n" + res[2] + ", " + res[3] + "\n"
