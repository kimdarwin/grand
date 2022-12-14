# run - batch
$python 00.py  
  
[00.py]  
import os  
import requests  
os.system('python 01ir.py')  
os.system('python 02qa.py')  
os.system('python 03table.py')  
os.system('python 04.py')  

# install  
python 3.8~3.9  
git clone https://github.com/kimdarwin/grand  
cd grand  
mkdir /home/agc2022  
cp -r ./dataset /home/agc2022  
#테스트용 문제 파일(problemsheet.json) 및 문서 복사  

pip install --upgrade pip   
pip install torch==1.7.1+cu110 torchvision==0.8.2+cu110 -f https://download.pytorch.org/whl/torch_stable.html  
pip install -r requirements.txt  
apt install default-jdk  
apt install git-lfs  

# requirements.txt  
gensim==3.8.3  
konlpy  
transformers  
pyodf  
kiwipiepy  
easynmt  
sacremoses  

# 각 파일 구조  
[01ir.py]  
import ...  
def ... #주요 함수  

url = 'https://api.github.com' #제출할 url 설정  

outj['team_id'] = "" #팀명 설정  
outj['hash'] = "" #팀 해쉬 설정  

... #나머지 코드 및 제출  


# flow
[01ir.py]  
![image](https://user-images.githubusercontent.com/2725508/205604135-740ab851-3f1c-4877-97fc-8bb4ac9cc8b2.png)

[02qa.py]  
![image](https://user-images.githubusercontent.com/2725508/205604198-7c57d153-70dc-484f-8d00-af752a2f0518.png)

[04.py]  
![image](https://user-images.githubusercontent.com/2725508/207591586-27d668bd-9b6a-4a48-acf7-097dc1d9e661.png)


# output  
Restful 통신과 파일출력을 같이 수행함  

(json을 post방식으로 url에 제출함)  
r = requests.post(url,json=payload)  
print(r.status_code)  

[a1odt.json]
![image](https://user-images.githubusercontent.com/2725508/205597441-6b1036b4-cf6c-4779-a3ee-36c91b64c80d.png)


[a2odt.json]  
![image](https://user-images.githubusercontent.com/2725508/205597549-7d4ee6f3-e3a5-4684-9579-633a566bbda2.png)


# screenshot
![image](https://user-images.githubusercontent.com/2725508/205593856-6c7ad268-b22d-4296-be1a-d0fe7dd244dc.png)  

