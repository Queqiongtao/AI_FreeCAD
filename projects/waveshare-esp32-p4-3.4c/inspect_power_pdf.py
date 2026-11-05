"""提取和渲染官方MP2636原理图及相关数据手册页，输出仅供工程核对。"""
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'archive'/'pdf_dependencies'))
sys.stdout.reconfigure(encoding='utf-8')
from pypdf import PdfReader
import pypdfium2 as pdfium

target=ROOT/'archive'/'power_review';target.mkdir(parents=True,exist_ok=True)
for stem in ('mp2636_schematic','mp2636_datasheet'):
    source=ROOT/'reference'/'sources'/(stem+'.pdf')
    reader=PdfReader(source);pdf=pdfium.PdfDocument(str(source))
    for i,page in enumerate(reader.pages):
        text=page.extract_text() or ''
        (target/(stem+'_%02d.txt'%(i+1))).write_text(text,encoding='utf-8')
        if stem.endswith('schematic') or 'ISET' in text or 'charge current setting' in text.lower():
            print(stem,'第',i+1,'页\n',text[:18000],flush=True)
            pdf[i].render(scale=1.8).to_pil().save(target/(stem+'_%02d.png'%(i+1)))
