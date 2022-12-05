#!pip install beautifulsoup
#!pip install lxml
#!pip install odfpy
import os
from bs4 import BeautifulSoup
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties
from odf.text import H, P, Span

def file_open(file):
    #파일 읽기
    rawdata = open(file, 'r', encoding='utf-8' )

    data = rawdata.read()
    return data

def load_content(file):
    #뷰티풀 수프를 이용하여 beattiful soup 으로 읽어오는 과정
    data = file_open(file)
    #soup = BeautifulSoup(data, "lxml", features="xml")
    soup = BeautifulSoup(data, "lxml")
    data = soup.select('paragraph')
    #data = soup.select('p')
    #for item in data :
    #    print(item.text)
    return data;

def write_odt(data, file):
    textdoc = OpenDocumentText()
    for item in data:
        para = item.text
        p = P(text=para)
        #p.addText("This is after bold.")
        textdoc.text.addElement(p)
    textdoc.save(file)    
    return;

#if __name__ == '__main__':
#    file = r'D:\Data\example1.xml'
#    load_content(file)
indir = 'report_xml'
outdir = 'report_odt'

files = os.listdir(indir)
i = 0
for file in files:
    i = i+1;
    if(i%1000==0):
        print(str(i));
    infile = indir+"/"+file
    data = load_content(infile)
    
    if(len(data)<3):
        continue;
    outfile = outdir+"/"+file.replace(".xml",".odt")
    write_odt(data,outfile);
    
    