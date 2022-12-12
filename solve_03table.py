#!pip install sacremoses
#!git clone https://huggingface.co/facebook/m2m100_1.2B
#!git clone https://huggingface.co/facebook/m2m100_418M
import os
import traceback
from bs4 import BeautifulSoup
from transformers import TapexTokenizer, BartForConditionalGeneration
import pandas as pd
from easynmt import EasyNMT, models
import json
import time
import re
from urllib import request
#from parse_chart2table import chart2table

def findfloats(answer):
    #문자열에서 실수들을 추출해서 리스트[]로 반환
    #부호부, 정수부, 가수부는 선택이다. 지수부 역시 선택이다. 정수부가 없으면 가수부는 필수이다. 가수부가 없으면 소수점은 선택이다.
    answers = re.findall("[+-]?\d+\.?\d*",answer)
    if(not answers or len(answers)==0):
        return [] 
    #answer = answers[-1]
    return answers
def fetaqa(question, tbl):
    outfile = "data/fetaQA-v1_test1.json"
    #infile = "checkpoints/pko-t5-base/test_preds_seq2seq.txt"
    infile = "checkpoint-7000/test_preds_seq2seq.txt"
    
    pred = ""
    fetaj = {
        'version':"v1",
        'split':"test",
    }
    d = {
        'question':question,
        'table_array':tbl,
        'source':"mturk-approved",
        'answer':"",
        'highlighted_cell_ids':[[]],
        'table_section_title':"",
        'table_page_title':"",
        'page_wikipedia_url':"",
        'table_source_json':"",
        'feta_id':1
    }
    data = []
    data.append(d)
    fetaj['data']=data
    
    with open(outfile, 'w') as out:
        out.write(json.dumps(fetaj, ensure_ascii=False, indent=4))
    
    os.system('python FeTaQA/end2end/train.py FeTaQA/end2end/configs/t5-small-test.json');
    
    with open(infile, 'r') as inf:
        line = inf.readline();
    
    floats = findfloats(line)
    if((not floats==[]) and line.find(" ")>=0):
        pred = floats[0]
    else:
        pred = line
    ####print("TableQA answer: "+ pred);
    
    return pred
def file_open(file):
    #파일 읽기
    rawdata = open(file, 'r', encoding='utf-8' )
    data = rawdata.read()
    return data
def removetags(xml):
    #xml = re.sub("\<[^\>]+\>", "", xml)
    xml = re.sub("<[^>]+>", "", xml).strip()
    return xml
def load_table(file):
    #뷰티풀 수프를 이용하여 beattiful soup 으로 읽어오는 과정
    #data = file_open(file)
    data = file
    #soup = BeautifulSoup(data, "lxml", features="xml")
    bs = BeautifulSoup(data, "lxml")
    table = bs.find('table:table')
    return table
def xmltabletolist(xmlstr):
    table = []
    content = load_table(xmlstr)
    rows = content.findAll(lambda tag: tag.name=='table:table-row')
    for row in rows:
        rowlist = []
        cells = row.findAll(lambda tag: tag.name=='table:table-cell')
        for cell in cells:
            celltxt = removetags(str(cell))
            rowlist.append(celltxt.strip())
        table.append(rowlist)
        #print(str(cells))
        #print(str(celltxt).strip())
    return table

try:
    mt = EasyNMT(translator=models.AutoModel("Helsinki-NLP/opus-mt-ko-en"), cache_folder='cached') #인명번역이 좋음..
    tokenizer = TapexTokenizer.from_pretrained("microsoft/tapex-large-finetuned-wtq")
    model = BartForConditionalGeneration.from_pretrained("microsoft/tapex-large-finetuned-wtq")
except:
    print(traceback.format_exc())
    pass

print('solve_03table Load Complete~~~~!!!!!!!!!!!!!!!!!!\n\n')

def solve(problem_json, dataset_path):    
    TEAM_ID = "khkcap"
    TEAM_HASH = "EODIdifTqaqTXqF7"
    API_URL = os.environ['REST_ANSWER_URL']

    problem_no = problem_json['problem_no']
    task_no = problem_json['task_no']    
    ref_file = problem_json['ref_file']
    question = problem_json['question']
    answers = []
    tbl = []
    
    #테이블
    if(ref_file.find("table")>=0):
        xml = file_open(dataset_path+"/ref/"+ref_file.replace(".xml","")+".xml")
        tbl = xmltabletolist(xml)
    #차트
    else:
        pass;
        '''
        image_path = dataset_path+"/ref/"+ref_file+".png"
        tbl = chart2table(image_path)
        print(tbl)
        if tbl is None:
            return
            
        if len(tbl) > 0:
            print(tbl)
            print('length result chart2table :', len(tbl))
            tbl = [o for o in tbl if o is not None]
            print(tbl)
            if len(tbl) > 0:
                print(tbl)
                tbl = tbl[0]
                print(tbl)
            else: return
        else: return
        '''
    
    answer_json = {
        'team_id': TEAM_ID,
        'hash': TEAM_HASH,
        'problem_no': problem_no,
        'task_no': task_no,
        'answer': []
    }
    
    newdata = {}
    newtbl = []
    cnt = 0
   
    print(tbl)
    kopred = fetaqa(question, tbl)
        
        
        
        
    print("\n")
    
    print('\n\n\n**********************************************************************\n\n\n')
    print('answer_json', answer_json)
    print('\n\n\n**********************************************************************\n\n\n')
    
    # post to API server
    data = json.dumps(answer_json).encode('utf-8')
    req =  request.Request(API_URL, data=data)

    '''
    # check API server return
    resp = request.urlopen(req)
    resp_json = eval(resp.read().decode('utf-8'))

    if "OK" == resp_json['status']:
        print("data requests successful!!\n\n\n\n")
    elif "ERROR" == resp_json['status']:    
        received_message=resp_json['msg']
        raise ValueError(received_message)    
    '''
    
    answer_json['question']=question    
    answers.append(answer_json)
    
    # outfile = "a3-tapex.json"
    # with open(outfile,"w") as out:
    #     out.write(json.dumps(answers, ensure_ascii=False, indent=4))
    
    print("qid: "+problem_no)
    print("\n질문: "+question)
    print("정답 출력: "+str(kopred))
    print("\n")
    
    
    
    
