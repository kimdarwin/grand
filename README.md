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
mkdir /home/agc2022 #문제 파일(problemsheet.json) 및 문서 파일 복사  
cp -r ./dataset /home/agc2022

pip install --upgrade pip   
pip install -r requirements.txt  
apt install default-jdk  
pip install torch==1.7.1+cu110 torchvision==0.8.2+cu110 -f https://download.pytorch.org/whl/torch_stable.html  

# requirements.txt  
gensim==3.8.3  
konlpy  
transformers  
pyodf  
kiwipiepy  

# screenshot
![image](https://user-images.githubusercontent.com/2725508/205593856-6c7ad268-b22d-4296-be1a-d0fe7dd244dc.png)  

