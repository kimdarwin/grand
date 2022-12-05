# run - batch
$python 00.py  
[00.py]  
import os  
import requests  
os.system('python 01ir.py')  
os.system('python 02qa.py')  
#os.system('python 03table.py')  
#os.system('python 04.py')  

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

# requirements.txt  
gensim==3.8.3  
konlpy  
transformers  
pyodf  
kiwipiepy  

# flow
[01ir.py]  
![image](https://user-images.githubusercontent.com/2725508/205603901-c3fa110e-4864-450a-a8b7-8c5ba3491cee.png)

[02qa.py]  
![image](https://user-images.githubusercontent.com/2725508/205603936-fa8128b0-0304-47a1-86c7-e467b5b68463.png)

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

