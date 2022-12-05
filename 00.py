import os
import json
import requests
os.system('python 01ir.py')
os.system('python 02qa.py')
#os.system('python 03table.py')
#os.system('python 04.py')


#종료 메세지 제출: outj를 post방식으로 url에 제출함
url = 'https://api.github.com'
outj = {}
outj['team_id']="";
outj['hash']="";

outj['end_of_mission']="true"
payload = outj
r = requests.post(url,json=payload)
print(r.status_code)