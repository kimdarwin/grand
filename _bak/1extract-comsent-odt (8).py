#!sudo pip install kss
#!pip install kss
import json
import os
import re
import sys
from odf import text, teletype
from odf.opendocument import load
from kiwipiepy import Kiwi
#import kss
def isEng(text):
    if not text:
        return
    if len(text)==0:
        return
    engCount = len(re.findall(u'[a-zA-Z]+', text[0]))
    return engCount > 0
def isHangul(text):
    #Check the Python Version
    pyVer3 =  sys.version_info >= (3, 0)

    if pyVer3 : # for Ver 3 or later
        encText = text
    else: # for Ver 2.x
        if type(text) is not unicode:
            encText = text.decode('utf-8')
        else:
            encText = text
    hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', encText))
    return hanCount > 0
def replacecomma(m):        # 매개변수로 매치 객체를 받음
    n = m.group().replace(",","")    # 매칭된 문자열
    return str(n)
kiwi = Kiwi()
#indir = 'report_odt_small10'
#outfile = 'q1.json'
#indir = 'odtsmall'
#outfile = 'q1sents.json'
indir = 'odtsubset'
outfile = 'q1sents.json'
out = open(outfile,"w");
#문장에서 첫쉼표 앞 허용 글자{16,100}, 쉼표 사이 허용 글자{25,50}, 쉼표 개수{3,4}, 마지막쉼표 뒤 허용 글자{1,100}
#p = re.compile('[^,]{15,20}([^,]{4,10},){2,3}[^,]{2,10}')
#p = re.compile('[^,]{15,20}([^,]{6,10},){2,3}[^,]{2,10}')

#p = re.compile('[^,]{10,15}([^,]{8,9},){3,4}[^,]{2,8}')
#p2 =re.compile('[^,]{10,15}([^,]{10,11},){3,4}[^,]{2,8}')
#p3 =re.compile('[^,]{10,15}([^,]{6,7},){3,4}[^,]{2,8}')

#ptext = '[^,]{11,13}([^,]{10,12},){3,4}[^,]{2,5}'
####ptext = '[^,]{10,14}([^,]{9,12},){3,4}[^,]{2,6}'
ptext = '[^,]{8,30}([^,]{9,12},){3,6}[^,]{2,6}'
p = re.compile(ptext)
p2 =re.compile('[^,]{11,13}([^,]{10,12},){5,6}[^,]{2,5}')
p3 =re.compile('[^,]{11,13}([^,]{6,7},){3,4}[^,]{2,5}')


questions = []
files = os.listdir(indir)
j = 0
problem_no = 0;
for file in files:
    j = j+1;
    if(j%1000==0):
        print(str(j))
    if(j>20):
        break;
    
    infile = indir+"/"+file;
    if(os.path.isdir(infile)):
        continue;
    print(infile);
    
    textdoc = load(infile)
    paras = textdoc.getElementsByType(text.P)
    for para in paras:
        paratext = teletype.extractText(para)
        paratext = paratext.replace("\n"," ");
        #print(paratext)
        #for line in kss.split_sentences(paratext):
        for line in kiwi.split_into_sents(paratext):
            #kiwi Sentence(text='이걸', start=17, end=24, tokens=None)]
            line = line.text
            if(len(line)<30):
                continue;
            if(len(line)>200):
                continue;
            ####print(line);
            #한글검사
            if(isHangul(line)==False):
                continue;
            #첫글자 영어검사
            if(isEng(line[0])):
                continue;
            
            #숫자에서 천단위 콤마 삭제
            orgline = line;
            #line = line.strip();
            line = re.sub("[0-9],[0-9]",replacecomma,line);
                        
            '''
            if(i>6000):
                break;
            '''
            #m = p.match(line)
            s = p.search(line)
            #s2 = p2.search(line);
            #s3 = p3.search(line);
            flag = 0;
            flag2 = 0;
            flag3 = 0;

            if s:
                #print(line+"\t"+paratext+"\n");
                print(line+"\t"+ptext+"\n");
                question = line[0:line.find(",")-1] #쉼표 많은문장의 첫 쉼표 앞까지만 질문으로 취급
                problem_no = problem_no + 1
                q = {}
                q['problem_no'] = problem_no
                q['task_no'] = 1
                q['doc_file'] = file
                q['question'] = question
                q['sent'] = orgline
                q['para'] = paratext
                q['pat'] = ptext
                questions.append(q);
                
                #out.write(line+"\t"+paratext+"\n");
                flag = 1;
    
    
out.write(json.dumps(questions, ensure_ascii=False, indent = 4))            
out.close();