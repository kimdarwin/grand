#!pip install sacremoses
#!git clone https://huggingface.co/facebook/m2m100_1.2B
#!git clone https://huggingface.co/facebook/m2m100_418M
from bs4 import BeautifulSoup
from transformers import TapexTokenizer, BartForConditionalGeneration
import pandas as pd
from easynmt import EasyNMT, models
import json
import time
import re
import requests
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
    return table;
def xmltabletolist(xmlstr):
    table = []
    content = load_table(xmlstr);
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
    return table;
#tablefile = "./KorWikiTQ/KorWikiTQ_ko_dev.json"
url = 'https://api.github.com'
indir = '/home/agc2022/dataset'
infile = indir+"/"+"problemsheet.json"
outfile = "a3-tapex.json"

#mt = EasyNMT(translator=models.AutoModel("facebook/m2m100_1.2B"), cache_folder='cached')
#mt = EasyNMT(translator=models.AutoModel("facebook/m2m100_418M"), cache_folder='cached') #번역 안좋음
mt = EasyNMT(translator=models.AutoModel("Helsinki-NLP/opus-mt-ko-en"), cache_folder='cached') #인명번역이 좋음..
##mt = EasyNMT('opus-mt')
##mt = EasyNMT('m2m_100_418M')
tokenizer = TapexTokenizer.from_pretrained("microsoft/tapex-large-finetuned-wtq")
model = BartForConditionalGeneration.from_pretrained("microsoft/tapex-large-finetuned-wtq")
#tokenizer = TapexTokenizer.from_pretrained("microsoft/tapex-large-finetuned-wikisql") #느림?
#model = BartForConditionalGeneration.from_pretrained("microsoft/tapex-large-finetuned-wikisql")
'''
with open(tablefile, 'r') as f:
    json_data = json.load(f)

json_data = json_data['data']
answers = []
qcnt = 0
for d in json_data:
    start = time.time();
    qcnt = qcnt+1;
    #print(str(d))
'''
with open(infile, 'r') as f:
    jsons = json.load(f)
####out = open(outfile,"w");
acccnt = 0;
total = 0;
i = 0;
outjson = []
for l in jsons:
    i = i+1;
    if(i%100==0):
        print(str(i));
    start = time.time()
    
    problem_no = l['problem_no']
    task_no = l['task_no']
    if(task_no!=3 and task_no!="3"):
        continue;
    
    #doc_file = l['doc_file']
    ref_file = l['ref_file']
    #answer_form = l['answer_form']
    question = l['question']
    para = ""
    answers = []
    #u = d['U'];
    #t = d['T']
    #qas = d['QAS'];
    #qid = qas['qid']
    #question = qas['question']
    #answer = qas['answer']
    tbl = []
    
    #테이블
    if(ref_file.find("table")>=0):
        xml = file_open(indir+"/ref/"+ref_file.replace(".xml","")+".xml");
        tbl = xmltabletolist(xml)
    #차트
    else:
        pass;
        #tbl = [ [..], [..] ]
    
    a = {}
    a['team_id']=""
    a['hash']=""
    a['problem_no']=problem_no
    a['task_no']=task_no
    
    
    
    
    newdata = {}
    newtbl = []
    cnt = 0
    ####표가 20행이상이면 표 축소
    if(len(tbl)>20):
        tbl = tbl[:20]
        
    for cells in tbl:
        cnt = cnt+1
        #opennmt때문에 셀 숫자를 문자열로 바꿈
        newcells = []
        for cell in cells:
            if(len(cell)>30):
                cell=cell[:30]
            if(cell=='비고'):
                cell='etc'
            
            cell = str(cell)
            #정수는 int로 바꿈
            num_format = re.compile(r'^\-?[0-9]+$')
            it_is = re.match(num_format,cell)

            if it_is:
                cell = int(cell)
                #print(str(cell))

            #tapex 에러나서 다시 숫자를 문자열로 바꿈
            newcells.append(str(cell))
        cells = newcells
        
        try:
            newcells = mt.translate(cells, source_lang='ko',target_lang='en')
            newcells2 = []
            for cell in newcells:
                if(len(cell)>0 and cell[-1]=='.'):
                    cell = cell[:-1]
                newcells2.append(cell.lower())
            newcells = newcells2
        except:
            newcells = cells
        newtbl.append(newcells)
        '''
        if(cnt<=2):
            print(str(cells))
            print(str(newcells))
        '''
        newkey = newcells[0]
        newcells = newcells[1:]
        newdata[newkey] = newcells
        ####print(newkey)
        ####print(str(newcells))
    data = newdata
    
    #행 길이검사 필요함
    table = pd.DataFrame.from_dict(data)
    
    
    #2대 -> 2 대
    
    #search = re.search('^\-?[1-9][0-9]*(^[1-9][0-9] )',question)
    #search = re.search(r'[0-9]^[ 0-9]',question)
    
    #num_format = re.compile('[0-9]^[ 0-9]')
    #search = re.match('[0-9]^[ 0-9]',question)
    search = re.match('[^0-9]*[0-9]+[^0-9 ]',question)
    
    
    if(search):
        num_one=search.group()
        #print(num_one)
        question = question.replace(num_one,num_one[:-1]+" "+num_one[-1])
    #print(question)
    query = question

    qs = []
    qs.append(query)
    query = mt.translate(qs, target_lang='en')[0].lower()
    query = query.replace("first","1").replace("second","2").replace("third","3").replace("fourth","4").replace("fifth","5").replace("sixth","6").replace("seventh","7").replace("eighth","8").replace("ninth","9").replace("tenth","10")
    query = query.replace(" one "," 1 ").replace(" two "," 2 ").replace(" three "," 3 ").replace(" four ","4").replace(" five"," 5 ").replace(" six"," 6 ").replace(" seven"," 7 ").replace(" eight "," 8 ").replace(" nine "," 9 ").replace(" ten ","10")


    encoding = tokenizer(table=table, query=query, return_tensors="pt")
    outputs = model.generate(**encoding)
    pred = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    pred = pred[0].strip()
    if(len(pred)>0 and pred[-1]=='.'):
        pred = pred[:-1]
    newlist=[(i,j) for i in range(len(tbl)) for j in range(len(tbl[0])) if newtbl[i][j]==pred]
    
    
    kopred = ""
    if newlist != []:
        kopred = tbl[newlist[0][0]][newlist[0][1]]
    #for cells in tbl:
        
    
    a['question']=question
    a['equestion']=query
    a['eanswer'] =pred
    a['answer'] = pred
    #a['answer_gold'] = answer
    #a['answer_right'] = answer==str(kopred)
    if(kopred!=""):
        a['answer'] = kopred
    a['TBL']=tbl
    answers.append(a)
    '''
    a['time']=time.time()-start
    a['rowsize']=len(tbl)
    a['colsize']=len(tbl[0])
    #a['T']=t
    a['ETBL']=newtbl
    
    '''
    
    
    '''
    if(a['answer_right']==True):
        print("표 제목: "+t)
        print("qid: "+qid)
        print("\n질문: "+question +" "+query)
        print("정답 출력: "+str(kopred)+" "+str(pred))
        print("실제 정답: "+answer+" "+str(a['answer_right']))
        print("\n")
    '''
    
    #outj를 post방식으로 url에 제출함
    payload = a
    r = requests.post(url,json=payload)
    print("\n"+str(a)[:350])
    print(r.status_code)
    
    #if(i%1==0):
    out=open(outfile,"w");
    out.write(json.dumps(answers, ensure_ascii=False, indent=4))
    out.close();

    ####print(str(newlist))
    print(str(i))
    #print("표 제목: "+t)
    print("qid: "+problem_no)
    print("\n질문: "+question +" "+query)
    print("정답 출력: "+str(kopred)+" "+str(pred))
    #print("실제 정답: "+answer)
    #print("실제 정답: "+answer+" "+str(a['answer_right']))
    print("\n")
    
    
    
    
