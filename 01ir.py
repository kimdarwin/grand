import requests
import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer
import json
import re
from odf import text, teletype
from odf.opendocument import load
#from rank_bm25 import BM25Okapi
import OpenDocumentTextFile
from gensim import corpora
from gensim.summarization import bm25
from kiwipiepy import Kiwi
from konlpy.tag import Kkma, Komoran, Okt, Mecab
#okt = Okt()
komoran = Komoran()
kiwi = Kiwi()
def onehotsim(test_list1,test_list2):
    #res = len(set(test_list1) & set(test_list2)) / float(len(set(test_list1) | set(test_list2)))
    res = len(set(test_list1) & set(test_list2)) / float(len(set(test_list1)))
    return res
def okttokenizer(sent):
    try:
        toks = sent.split(' ');
        newtoks = []
        for t in toks:
            if(t.find('무엇인가')>=0 or t.find('가지')>=0 or t.find('얼마인가')>=0 or t=="별"):
                continue;
            else:
                newtoks.append(t);
        sent = " ".join(newtoks);
    except:
        pass;
    
    poss = []
    newposs = []
    try:
        #poss = okt.pos(sent,norm=True, stem=True, join=True) #okt
        poss = komoran.pos(sent,flatten=False, join=True) #komoran
        #print(str(poss))
        for p in poss:
            for pos in p:
                if(not pos.find("/N")>=0 and (not pos.find("/V")>=0)):
                    continue;
                pos = pos[:pos.find("/")]
                if(len(pos)>1):
                    newposs.append(pos)
        
    except Exception as e:
        print(str(e)) 
        return sent.split(" ")
    
    return newposs
def lastfloat(answer):
    #문자열에서 맨 왼쪽의 실수만 추출
    #deprecated: 문자열에서 맨 오른쪽의 실수만 추출
    #부호부, 정수부, 가수부는 선택이다. 지수부 역시 선택이다. 정수부가 없으면 가수부는 필수이다. 가수부가 없으면 소수점은 선택이다.
    answers = re.findall("[+-]?\d+\.?\d*",answer)
    if(not answers or len(answers)==0):
        return answer 
    #answer = answers[-1]
    answer = answers[0]
    return answer
def equaltwonums(cont, q):
    flag = False
    anss1 = re.findall("[+-]?\d+\.?\d*",cont)
    anss2 = re.findall("[+-]?\d+\.?\d*",q)
    if(not anss1 or len(anss1)==0):
        return False
    if(not anss2 or len(anss2)==0):
        return False
    if(anss1[0]==anss2[0]):
        #print("Twonums: "+anss1[0]+" "+anss2[0])
        return True
    else:
        return False
    
def replacecomma(m):        # 매개변수로 매치 객체를 받음
    n = m.group().replace(",","")    # 매칭된 문자열
    return str(n)
def readparas(in_file):
    textdoc = load(infile)
    paras = textdoc.getElementsByType(text.P)
    newparas = []
    for para in paras:
        paratext = teletype.extractText(para)
        newparas.append(paratext);
    return newparas
def getformkeys(answer_form):
    keys = ""
    k = -1
    for f in answer_form:
        k = k+1
        qpre = "";
        qsup = "";
        qpoint = "";
        for key in f:
            v = f[key];
            #print(key+"\t"+v);
            if(v==""):
                keys = keys+" "+key
                #qpoint = key;
                #qsup = key+"은?"
            else:
                keys = keys+" "+key
                keys = keys+" "+v
    return keys;
def getformlist(answer_form):
    keys = []
    k = -1
    for f in answer_form:
        k = k+1
        qpre = "";
        qsup = "";
        qpoint = "";
        for key in f:
            v = f[key];
            #print(key+"\t"+v);
            if(v==""):
                keys.append(key)
            else:
                keys.append(key)
                keys.append(v)
    #keys = list(set(keys)) #순서 섞임
    keys = list(dict.fromkeys(keys))
    if ("" in keys):
        keys.remove("");
    return keys;
def findfloats(answer):
    #문자열에서 실수들을 추출해서 리스트[]로 반환
    #부호부, 정수부, 가수부는 선택이다. 지수부 역시 선택이다. 정수부가 없으면 가수부는 필수이다. 가수부가 없으면 소수점은 선택이다.
    answers = re.findall("[+-]?\d+\.?\d*",answer)
    if(not answers or len(answers)==0):
        return [] 
    #answer = answers[-1]
    return answers



####print(torch.__version__)
url = 'https://api.github.com'
indir = '/home/agc2022/dataset'
infile = indir+"/"+"problemsheet.json"
outfile = "a1odt.json"

'''
print("로딩 중(~5초)")
# Load fine-tuned MRC model by HuggingFace Model Hub
HUGGINGFACE_MODEL_PATH = "bespin-global/klue-bert-base-mrc"
tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_MODEL_PATH )
model = AutoModelForQuestionAnswering.from_pretrained(HUGGINGFACE_MODEL_PATH )
'''

with open(infile, 'r') as f:
    jsons = json.load(f)

out = open(outfile,"w");

acccnt = 0;
total = 0;
i = 0;
outjson = []
for l in jsons:
    i = i+1;
    if(i%100==0):
        print(str(i));
    
    problem_no = l['problem_no']
    task_no = l['task_no']
    if(task_no!=1 and task_no!="1"):
        continue;
    
    doc_file = l['doc_file']
    #answer_form = l['answer_form']
    question = l['question']
    para = ""
    answers = []
    try:
        #answers = l['answers']
        para = l['para']
    except:
        pass;
    outj = {}
    outj['team_id'] = ""
    outj['hash'] = ""
    outj['problem_no'] = problem_no
    outj['task_no'] = task_no
    #outj['answer'] = answer_form
    outj['answer'] = []
    
    #doc_file에서 p 검색
    
    print(doc_file)
    doc_num = doc_file[9:11]
    #print(doc_num)
    doc_num = int(doc_num)
    in_file = indir+"/doc/"+str(doc_num)+"/"+doc_file+".odt"
    print("in_file: "+in_file)
    ####paras = readparas(in_file);

    odt = OpenDocumentTextFile.OpenDocumentTextFile(in_file);
    paras = odt.tolist();
    newpara = []
    bigparas = []
    for p in paras:
        bigparas.append(p);
        if(len(p)>20 and len(p)<2000):
            for line in kiwi.split_into_sents(p):
                if(len(line.text)>20 and len(line.text)<2000):
                    newpara.append(line.text);

    paras = newpara
    try:
        texts = [okttokenizer(doc) for doc in paras] # you can do preprocessing
        
        dictionary = corpora.Dictionary(texts)
        corpus = [dictionary.doc2bow(text) for text in texts]
        bm25_obj = bm25.BM25(corpus)
        question = question.replace("별"," 별 ").replace("("," (").replace("년"," 년")
        q_poss = okttokenizer(question)
        query_doc = dictionary.doc2bow(q_poss)
        
        print("QUERY: "+str(q_poss))
        sim = onehotsim(q_poss,okttokenizer(para))
        print("Golden Para: "+str(sim)+str(okttokenizer(para)));
        
        scores = bm25_obj.get_scores(query_doc)
        #best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-100:]
        #best_docs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[-500:]
        #best_docs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[-5:]
        #best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-500:]
        best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-200:]
        
        
        
        j=-1;
        sims = []
        docs = []
        for best in best_docs:
            j=j+1
            sim = onehotsim(q_poss,texts[best])
            sims.append(sim);
            docs.append(paras[best])
            #print("Para "+str(j)+": "+str(sim)+" "+paras[best][:70]);
            #print("Text "+str(j)+": "+str(sim)+" "+str(texts[best])[:70]);
        
        #sim_docs = sorted(range(len(sims)), key=lambda i: sims[i])[-5:]
        sim_docs = sorted(range(len(sims)), key=lambda i: sims[i])[-3:]
        sim_docs.reverse();
        ####print("Sim_docs: "+str(sim_docs))
        
        j=0;
        for simidx in sim_docs[:3]:
            j=j+1
            #para = docs[simidx];
            for p in bigparas:
                if(p.find(docs[simidx])>=0):
                    ansp = p;
                
            
            
            ans = {}
            ans['rank']=j
            #ans['paragraph']=docs[simidx]
            ans['paragraph']=ansp
            outj['answer'].append(ans)
            
            print("Para "+str(simidx)+": "+str(sims[simidx])+" "+docs[simidx][:70]);
            #print("Text "+str(simidx)+": "+str(sims[simidx])+" "+str(texts[simidx])[:70]);
            #print("Para "+str(simidx)+": "+str(sims[simidx])+" "+paras[simidx][:70]);
            #print("Text "+str(simidx)+": "+str(sims[simidx])+" "+str(texts[simidx])[:70]);
            #print("Para "+str(j)+": "+str(sim)+" "+paras[best][:70]);
            #print("Text "+str(j)+": "+str(sim)+" "+str(texts[best])[:70]);
            #pass;
        
        
    except Exception as e:
        print(str(e))  
        #para = "\n".join(paras);
        continue;

    #정답 포함 문장 검색 끝
    print("\n")
    print(str(json.dumps(outj, ensure_ascii=False))[:300])
    
    #outj를 post방식으로 url에 제출함
    payload = outj
    r = requests.post(url,json=payload)
    print(r.status_code)
    
    try:
        #outj['answers'] = answers;
        outj['answers'] = para;
    except:
        pass;
    
    outjson.append(outj);
    
    
out.write(json.dumps(outjson, ensure_ascii=False, indent=4))
out.close();
#print(str(acccnt)+"\t"+str(total));
