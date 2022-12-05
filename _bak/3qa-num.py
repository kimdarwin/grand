import requests
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

def tokenizer(sent):
  return sent.split(" ")
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
                #multiflag = True;
                #qpre = qpre+" "+key+" "+v
    return keys;
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
        
        subq = pre+" "+com+" "+su
        
        if(j == 1):
            subq = com+" "+su
        if(j==len(coms)):
            subq = pre+" "+com
        qcom = com
        ansnum = ansnum.replace("%","");
        
        
        
        if(j==1):
            qcomt = com.split(' ');
            #qcom = qcom[len(qcom)-avgwlen:]
            #pre = ' '.join(pret[0:-1*avgwlen]);
            ######print(com)
            ####com = ' '.join(qcomt[len(qcomt)-avgwlen-1:-1*avgwlen]);
            #com = ' '.join(qcomt[-2:-1]);
            #com = ' '.join(qcomt[(-1*avgwlen)-1:]);
            com = ' '.join(qcomt[(-1*avgwlen)-2:]);
            ######print(com)
        
        
        subq_woans = pre+"|"+qcom+"| "+su
        
        
        if(j==1):
            subq_woans = qcom+"| "+su
        
        if(j==len(coms)):
            subq_woans = pre+"|"+qcom

        subqs.append(subq.replace("  "," "));
    return subqs;
    
####print(torch.__version__)
#infile = "papersubq.tsv"
#outfile = "3paper_bespin.tsv"
#infile = "problemsheet2num.json"

url = 'https://api.github.com'
indir = '/home/agc2022/dataset'
infile = indir+"/"+"problemsheet.json"
outfile = "a2odt.json"

print("로딩 중(~5초)")
# Load fine-tuned MRC model by HuggingFace Model Hub
HUGGINGFACE_MODEL_PATH = "bespin-global/klue-bert-base-mrc"
tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_MODEL_PATH )
model = AutoModelForQuestionAnswering.from_pretrained(HUGGINGFACE_MODEL_PATH )
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
    
    doc_num = doc_file[9:11]
    #print(doc_num)
    doc_num = int(doc_num)
    in_file = indir+"/doc/"+str(doc_num)+"/"+doc_file+".odt"
    print("in_file: "+in_file)
    ####paras = readparas(in_file);

    odt = OpenDocumentTextFile.OpenDocumentTextFile(in_file);
    paras = odt.tolist();
    try:
        texts = [doc.split() for doc in paras] # you can do preprocessing as removing stopwords
        dictionary = corpora.Dictionary(texts)
        corpus = [dictionary.doc2bow(text) for text in texts]
        bm25_obj = bm25.BM25(corpus)
        
        keys = getformkeys(answer_form);
        
        query_doc = dictionary.doc2bow((question+keys).split())
        scores = bm25_obj.get_scores(query_doc)
        #best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-10:]
        best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-1:]
        
        para =str(paras[best_docs[0]]) 
        print(para)

    except Exception as e:
        print(str(e))  
        para = "\n".join(paras);
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
    
    
    try:
        subqs = makesubqs(para);
    except:
        subqs = [para]
    #for subq in subqs:
    #    print(subq);

    
    #len(subqs)이 answer_form보다 1 더 큰 경우 맨 앞 서브문제를 버려서 정렬함
    ####subqs중 q에 가장 적합한 것을 검색하는 방식으로 변경 필요
    if(len(subqs)-len(answer_form)==1):
        subqs = subqs[1:]
    if(len(subqs)-len(answer_form)==-1):
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
                qsup = key+"은?"
            else:
                multiflag = True;
                qpre = qpre+" "+key+" "+v
        q = qpre +" "+qsup;
        qs.append(q);
        #print(qpre);
        #print(qsup);
        #print(q);
        
        
        cont=""
        
        try:
            #subqs[]에서 q와 가까운 subq 검색
            texts = [doc.split() for doc in subqs] # you can do preprocessing as removing stopwords
            dictionary = corpora.Dictionary(texts)
            corpus = [dictionary.doc2bow(text) for text in texts]
            bm25_obj = bm25.BM25(corpus)
            query_doc = dictionary.doc2bow(q.split())
            scores = bm25_obj.get_scores(query_doc)
            #best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-10:]
            best_docs = sorted(range(len(scores)), key=lambda i: scores[i])[-1:]
            cont = str(subqs[best_docs[0]])
            #print("cont: "+cont)
            
            '''
            tokenized_corpus = [tokenizer(doc) for doc in subqs]
            #print(str(tokenized_corpus))
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = tokenizer(q)
            cont = bm25.get_top_n(tokenized_query, subqs, n=1)[0]
            #doc_scores = bm25.get_scores(tokenized_query)
            #print(str(doc_scores))
            #print("bm25query: "+q);
            #print("bm25cont: "+cont);
            #print(str(subqs))
            '''
        except:
            print(str(e)) 
            try:
                cont = subqs[k]
            except:
                cont = para
                pass;
        
        
        
        
        try:
            pred = bespin(cont,q);
        except:
            continue;
        
        if(pred.find('[SEP]')>0):
            pred = pred[0:pred.find('[SEP]')]
        pred = pred.replace("%","");
        pred = pred.replace(" ","");
        pred = pred.strip();
        
        answer_form[k][key]=pred
        
        if(pred.find(answers[k])>=0):
            acccnt = acccnt+1;
        total = total+1
        
        #out.write(question+"\t"+pred+"\t"+para+"\n");
        ####out.write(json.dumps(json_out, ensure_ascii=False, indent=4))
    
        #if(i%30==0):
        #if(i%10==0):
        if(i%1==0):
            print("\n\n")
            #print(pred+"\t"+answers[k]+"\t"+question+"\t"+para+"\n");
            print(pred+"\t"+answers[k]+"\t"+qs[k]+"\t"+question+"\n");
    outj['answer'] = answer_form
    
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
