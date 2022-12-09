import requests
import traceback
import torch
from transformers import AutoModelForQuestionAnswering, AutoTokenizer
import json
import re
from odf import text, teletype
from odf.opendocument import load
from rank_bm25 import BM25Okapi
#from rank_bm25 import BM25Plus as BM25Okapi
import OpenDocumentTextFile
from gensim import corpora
from gensim.summarization import bm25
from kiwipiepy import Kiwi
from konlpy.tag import Kkma, Komoran, Okt, Mecab
#mec = Mecab()
okt = Okt()
#kkm = Kkma()
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
                #print(pos);
                #if(not pos.find("/N")>=0 and (not pos.find("/V")>=0)):
                if(not pos.find("/N")>=0):
                    continue;
                pos = pos[:pos.find("/")]
                if(len(pos)>1):
                    newposs.append(pos)
        #print(str(newposs))
    except Exception as e:
        #print(str(sent)) 
        print(str(e)) 
        return sent.split(" ")
    
    return newposs
def lastfloat(answer):
    #문자열에서 맨 왼쪽의 실수만 추출
    #deprecated: 문자열에서 맨 오른쪽의 실수만 추출
    #부호부, 정수부, 가수부는 선택이다. 지수부 역시 선택이다. 정수부가 없으면 가수부는 필수이다. 가수부가 없으면 소수점은 선택이다.
    #answers = re.findall("[+-]?(\b[0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+\b)?",answer)
    #answers = re.findall("\b\d*\.\d+(e\d+)?",answer)
    #answers = re.findall("[+-]?\d+\.?\d*([eE]?[+-]?[0-9]+)?",answer)
    ####answers = re.findall("[+-]?\d+\.?\d*",answer)
    answers = re.findall("[+-]?\d+[,\.]?\d*",answer)
    #print(str(answers))
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
                key = key.split(" ")[0]
                keys = keys+" "+key
                #qpoint = key;
                #qsup = key+"은?"
            else:
                key = key.split(" ")[0]
                v = v.split(" ")[0]
                keys = keys+" "+key
                keys = keys+" "+v
                #multiflag = True;
                #qpre = qpre+" "+key+" "+v
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
                key = key.split(" ")[0]
                keys.append(key)
                #qpoint = key;
                #qsup = key+"은?"
            else:
                key = key.split(" ")[0]
                v = v.split(" ")[0]
                keys.append(key)
                keys.append(v)
                #multiflag = True;
                #qpre = qpre+" "+key+" "+v
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
def makesubqs(s):
    regex = r"[0-9]*\.?[0-9]+\.?[0-9]*%?"
    #regex = r"[0-9]*\.?[0-9]+\.?[0-9]*"
    r = re.compile(regex)
    
    #숫자에서 천단위 콤마 삭제
    #orgline = s;
    s = re.sub("[0-9],[0-9]",replacecomma,s);
    ####jsonl['text'] = s

    if(s.find(',')<0):
        return []
        ####continue;
    #문장 초반에(7) 콤마 나오면 삭제
    if(s.find(',')<7):
        s = s[s.find(',')+1:]
    
    coms = s.split(',');
    ccnt = len(coms);
    pre = coms[0];
    
    twlen = 0
    ncnt = 0
    for com in coms[1:-1]:
        #m = r.search(com)
        #m = re.match(regex, com)
        m = re.findall(regex,com)
        
        if(m != None):
            if(len(m)>0):
                #print(str(m.groups()))
                #####print(str(m))
                ncnt = ncnt+1
        #print(com)
        ws = com.split(' ');
        wcnt = len(ws);
        twlen = twlen+wcnt
    cccnt = ccnt - 2
    avgwlen = int(twlen/cccnt) -1
    
    #avgwlen 기준으로 접두 생성중인데, 접두에 숫자 있는경우엔 숫자기준으로 변경 필요해보임
    #접미에도 숫자있는경우엔 숫자기준으로 변경 필요해보임
    pret = coms[0].split(' ');
    pre = ' '.join(pret[0:-1*avgwlen]);
    
    #접두사에 숫자 있으면 응답 혼란 피하기 위해서 삭제
    try:
        floats = findfloats(pre)
        for f in floats:
            pre = pre.replace(f," ")
    except:
        pass;
    
    sut = coms[-1].split(' ');
    su = ' '.join(sut[avgwlen+1:]);
    #print("pre: "+ pre);
    #print("su: "+su+"\n");
    
    subqs = []
    j = 0
    for com in coms:
        j = j+1
        #com에서 가장 뒤 숫자 검색
        #m = r.search(com)
        m = re.findall(regex,com)
        ansnum = ""
        if(m != None):
            if(len(m)>0):
                ansnum = m[len(m)-1]
        
        
        
        #숫자 직후 공백 추가
        if(ansnum==""):
            continue;
        if(ansnum!=""):
            com = com.replace(ansnum,ansnum+" ");
        
        ####subq = pre+" "+com+" "+su
        subq = pre+" "+com
        
        
        
        if(j == 1):
            #접미사에 숫자 있으면 응답 혼란 피하기 위해서 삭제
            try:
                floats = findfloats(su)
                for f in floats:
                    su = su.replace(f," ")
            except:
                pass;
            ####subq = com+" "+su
            subq = pre+" "+su
        else:
            #접두사에 숫자 있으면 응답 혼란 피하기 위해서 삭제
            try:
                floats = findfloats(pre)
                for f in floats:
                    #print("F: "+str(f))
                    pre = pre.replace(f," ")
            except:
                pass;
            ####subq = com+" "+su
            subq = pre+" "+com
        '''
        if(j==len(coms)):
            subq = pre+" "+com
        '''
        qcom = com
        ansnum = ansnum.replace("%","");
        
        
        
        if(j==1):
            qcomt = com.split(' ');
            #com = ' '.join(qcomt[(-1*avgwlen)-1:]);
            com = ' '.join(qcomt[(-1*avgwlen)-2:]);
            ######print(com)
        
        
        subq_woans = pre+"|"+qcom+"| "+su
        
        
        if(j==1):
            subq_woans = qcom+"| "+su
        
        if(j==len(coms)):
            subq_woans = pre+"|"+qcom

        subqs.append(subq.replace("  "," "));
    ####print("Subqs: "+str(subqs))
    return subqs;
    
####print(torch.__version__)

url = 'https://api.github.com'
indir = '/home/agc2022/dataset'
infile = indir+"/"+"problemsheet.json"
outfile = "a2odt.json"

print("로딩 중(~5초)")
# Load fine-tuned MRC model by HuggingFace Model Hub
HUGGINGFACE_MODEL_PATH = "bespin-global/klue-bert-base-mrc"
#tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_MODEL_PATH )
tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_MODEL_PATH, local_files_only=True)
model = AutoModelForQuestionAnswering.from_pretrained(HUGGINGFACE_MODEL_PATH, local_files_only=True)
def bespin(context, question):
    # Encoding
    encodings = tokenizer(context, question, 
                          max_length=512, 
                          truncation=True,
                          padding="max_length", 
                          return_token_type_ids=False
                          )
    encodings = {key: torch.tensor([val]) for key, val in encodings.items()}             
    input_ids = encodings["input_ids"]
    attention_mask = encodings["attention_mask"]

    # Predict
    pred = model(input_ids, attention_mask=attention_mask)

    start_logits, end_logits = pred.start_logits, pred.end_logits
    token_start_index, token_end_index = start_logits.argmax(dim=-1), end_logits.argmax(dim=-1)
    pred_ids = input_ids[0][token_start_index: token_end_index + 1]

    # Decoding
    prediction = tokenizer.decode(pred_ids)
    return prediction

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
    if(task_no!=2 and task_no!="2"):
        continue;
    
    doc_file = l['doc_file']
    answer_form = l['answer_form']
    question = l['question']
    para = ""
    answers = []
    try:
        answers = l['answers']
        para = l['para']
    except:
        pass;
    outj = {}
    outj['team_id'] = ""
    outj['hash'] = ""
    outj['problem_no'] = problem_no
    outj['task_no'] = task_no
    outj['answer'] = answer_form
    
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
    for p in paras:
        if(len(p)>20 and len(p)<2000):
            for line in kiwi.split_into_sents(p):
                if(len(line.text)>20 and len(line.text)<2000):
                    newpara.append(line.text);
    paras = newpara
    try:
        #texts = [doc.split() for doc in paras] # you can do preprocessing
        #texts = [okttokenizer(doc[:2000]) for doc in paras] # you can do preprocessing
        texts = [okttokenizer(doc) for doc in paras] # you can do preprocessing
        #print("Texts: "+str(texts))
        #texts = [komoran.nouns(doc[:1000]) for doc in paras] # you can do preprocessing
        
        dictionary = corpora.Dictionary(texts)
        corpus = [dictionary.doc2bow(text) for text in texts]
        bm25_obj = bm25.BM25(corpus)
        keys = getformkeys(answer_form);
        if(len(keys)>1):
            keys=keys[:-1]
        question = question.replace("별"," 별 ").replace("("," (").replace("년"," 년")
        #query_doc = dictionary.doc2bow((question+keys).split())
        querys = okttokenizer(question)
        if(len(querys)>1):
            querys=querys[:-1]
        if(len(querys)>6):
            querys=querys[2:]
        
        keytok = list(set(okttokenizer(keys)))
        #querys = list(set(querys+keytok))
        
        
        #print(str(type(keytok)))
        #print(str(type(querys)))
        #list(set(querys.extend(keytok)))
        querys.extend(keytok)
        ####print(str(querys))
        query_doc = dictionary.doc2bow(querys)
        
        print("QUERY: "+str(querys))
        #query_doc = dictionary.doc2bow(komoran.nouns(question+keys))
        scores = bm25_obj.get_scores(query_doc)
        #best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-10:]
        best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-100:]
        '''
        for best in best_docs[:10]:
            ####print("Para "+str(best)+": "+paras[best][:50]);
            ####print("Text "+str(best)+": "+str(texts[best])[:50]);
            pass;
        '''
        
        newpara = []
        formlist = getformlist(answer_form)
        print("Formlist: "+str(formlist))
        
        if(len(formlist)<1):
            para = paras[best_docs[0]]
        elif(len(formlist)<2):
            for best_doc in best_docs:
                para = paras[best_doc]
                if(para.find(formlist[0])>=0):
                #if(para.find(formlist[1])>=0 or para.find(formlist[0])>=0 or para.find(formlist[2])>=0 or para.find(formlist[3])>=0):
                #if(para.find(formlist[1])>=0 and para.find(formlist[0])>=0):
                    print("Best: "+formlist[1]+"\t"+para);
                    newpara.append(para)
            paras = newpara
            #print(paras[0])
            para = paras[0]
        else:
            sims = []
            docs = []
            #print("Best_docs: "+str(best_docs[0]));
            for best in best_docs:
                #print("Querys: "+str(querys))
                #print("Texts: "+str(texts[best]))
                sim = onehotsim(querys,texts[best])
                sims.append(sim);
                docs.append(paras[best])
                #print("Para "+str(j)+": "+str(sim)+" "+paras[best][:70]);
                #print("Text "+str(j)+": "+str(sim)+" "+str(texts[best])[:70]);

            #sim_docs = sorted(range(len(sims)), key=lambda i: sims[i])[-5:]
            #sim_docs = sorted(range(len(sims)), key=lambda i: sims[i])[-3:]
            sim_docs = sorted(range(len(sims)), key=lambda i: sims[i])
            sim_docs.reverse();
            
            print("Sim_docs: "+str(sim_docs[0]))
            '''
            j=0;
            for simidx in sim_docs[:3]:
                j=j+1
                #para = docs[simidx];
                for p in bigparas:
                    if(p.find(docs[simidx])>=0):
                        ansp = p;
            '''
            
            #for best_doc in best_docs:
            cnt = -1;
            for idx in sim_docs:
                cnt=cnt+1;
                para = docs[idx]
                ####para = paras[best_doc]
                #print("Bestpara: "+para);
                #if(para.find(formlist[1])>=0 and para.find(formlist[0])>=0 and para.find(formlist[2])>=0):
                #if(para.find(formlist[1])>=0 and para.find(formlist[0])>=0 and para.find(formlist[2])>=0 and para.find(formlist[3])>=0):
                #if(para.find(formlist[1])>=0 and para.find(formlist[0])>=0 and para.find(formlist[2])>=0):
                
                #if(para.find(formlist[1])>=0):
                #if((para.find(formlist[1])>=0 or para.find(formlist[0])>=0 or para.find(formlist[2])>=0) and len(para)>20):
                if((para.find(formlist[1])>=0 or para.find(formlist[0])>=0 or para.find(formlist[2])>=0)):
                #if(para.find(formlist[1])>=0 and para.find(formlist[0])>=0):
                    if(cnt<1):
                        print("Best: "+formlist[1]+"\t"+para[:min(len(para),150)]);
                    newpara.append(para)
            if(len(newpara)>0):
                paras = newpara
            #print(paras[0])
            para = paras[0]

    except Exception as e:
        #print(str(e))  
        print(traceback.format_exc())
        para = "\n".join(paras);
    ####print("Para: "+str(para))
    '''
    try: 
        #subqs[]에서 q와 가까운 subq 검색
        tokenized_corpus = [tokenizer(doc) for doc in subqs]
        #print(str(tokenized_corpus))
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = tokenizer(q)
        cont = bm25.get_top_n(tokenized_query, subqs, n=1)[0]
    except Exception as e:
        print(str(e))
        para = para;
    '''
    #정답 포함 문장 검색 끝
    
    #서브지문 subqs[] 생성
    try:
        subqs = makesubqs(para);
    except:
        subqs = [para]
    ####print('Subqs: '+str(subqs))
    #for subq in subqs:
    #    print(subq);

    
    #len(subqs)이 answer_form보다 1 더 큰 경우 맨 앞 서브문제를 버려서 정렬함
    ####subqs중 q에 가장 적합한 것을 검색하는 방식으로 변경 필요
    '''
    if(len(subqs)-len(answer_form)==1):
        subqs = subqs[1:]
    '''
    if(len(subqs)-len(answer_form)==-1 and len(subqs)>0):
        subqs.append(subqs[len(subqs)-1])
    

    
    multiflag = False;
    qs = []
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
                qpoint = key;
                qsup = key+" 은?"
            else:
                multiflag = True;
                qpre = qpre+" "+key+" "+v
                #qpre = qpre+" "+v
        q = qpre +" "+qsup;
        qs.append(q);
        #print(qpre);
        #print(qsup);
        #print(q);
        #answer_form 차원인 multiflag 설정하고 q(서브질의) 준비완료
        
        #문자열 리스트 정답형이라면: 현재 정답포함 문장 검색이 거의 안되고 있음
        #if(not multiflag):
        
        
        #숫자 리스트 정답형이라면
        cont=""
        
        try:
            #subqs[]에서 q와 가까운 subq 검색
            #texts = [doc.split() for doc in subqs] # you can do preprocessing as removing stopwords
            texts = [okttokenizer(doc) for doc in subqs] # you can do preprocessing
            #texts = [komoran.nouns(doc) for doc in subqs] # you can do preprocessing
            okttokenizer
            dictionary = corpora.Dictionary(texts)
            corpus = [dictionary.doc2bow(text) for text in texts]
            bm25_obj = bm25.BM25(corpus)
            #query_doc = dictionary.doc2bow(q.split())
            query_doc = dictionary.doc2bow(okttokenizer(q))
            #query_doc = dictionary.doc2bow(komoran.nouns(q))
            scores = bm25_obj.get_scores(query_doc)
            #best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-10:]
            best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-1:]
            cont = str(subqs[best_docs[0]])
            #print("cont: "+cont)
            
            #서브문제가 정렬됐으면 검색결과 무시함
            #print(str(len(answer_form))+"\t"+str(len(subqs)))
            if(len(answer_form)==len(subqs)):
                cont = subqs[k]
            

        except Exception as e:
            print(str(e)) 
            try:
                cont = subqs[k]
            except:
                cont = para
                pass;
        
        #cont와 q에 숫자가 있는데 서로 다르면 cont=para
        if(not equaltwonums(cont,q)):
            cont = para;
        
        
        
        
        try:
            pred = bespin(cont,q);
        except:
            continue;
        if(pred.find('[SEP]')>0):
            pred = pred[0:pred.find('[SEP]')]
        pred = pred.replace("[UNK]"," ")
        pred = pred.replace("%","");
        pred = pred.replace(" ","");
        pred = pred.strip();
        
        try:
            pred = re.sub("[0-9],[0-9]",replacecomma,pred);
        except:
            pass;
        
        try:
            #print("Pred: "+pred);
            pred = lastfloat(pred);
        except Exception as e:
            print("Error: "+pred)
            print(str(e)) 
        
        answer_form[k][key]=pred
        '''
        if(pred.find(answers[k])>=0):
            acccnt = acccnt+1;
        '''
        total = total+1
        
        #out.write(question+"\t"+pred+"\t"+para+"\n");
        ####out.write(json.dumps(json_out, ensure_ascii=False, indent=4))
    
        #if(i%30==0):
        #if(i%10==0):
        try:
            if(i%1==0):
                #print(pred+"\t"+answers[k]+"\t"+question+"\t"+para+"\n");
                print(pred+"\t"+answers[k]+"\t"+qs[k]+"\t"+question+"\t[Cont]"+cont[:50]+"\n");
        except:
            pass;
    
    outj['answer'] = answer_form
    
    #answer_form == []
    if(answer_form ==[] or answer_form ==[""]):
        try:
            pred = bespin(subqs[0],question);
        except:
            continue;
        if(pred.find('[SEP]')>0):
            pred = pred[0:pred.find('[SEP]')]
        pred = pred.replace("[UNK]"," ")
        pred = pred.replace("%","");
        pred = pred.replace(" ","");
        pred = pred.strip();
        
        try:
            pred = re.sub("[0-9],[0-9]",replacecomma,pred);
        except:
            pass;
        
        try:
            pred = lastfloat(pred);
        except Exception as e:
            print("Error: "+pred)
            print(str(e))
        outj['answer'] = [pred]
    print("\n")
    print(json.dumps(outj, ensure_ascii=False))
    
    #outj를 post방식으로 url에 제출함
    payload = outj
    r = requests.post(url,json=payload)
    print(r.status_code)
    
    try:
        outj['answers'] = answers;
    except:
        pass;
    outjson.append(outj);
    
    
    
out.write(json.dumps(outjson, ensure_ascii=False, indent=4))
out.close();
#print(str(acccnt)+"\t"+str(total));
