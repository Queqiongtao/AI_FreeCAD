"""读取官方资料并保留来源快照，用于供电与硬件选型。"""
import argparse
import html
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {
    'waveshare_board': 'https://www.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-3.4C',
    'board_schematic': 'https://files.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-XC/ESP32-P4-WIFI6-Touch-LCD-XC-Schematic.pdf',
    'powerboost': 'https://www.adafruit.com/product/2465',
    'battery': 'https://www.adafruit.com/product/328',
    'dfrobot_product': 'https://www.dfrobot.com/product-1613.html',
    'mp2636_schematic': 'https://raw.githubusercontent.com/Arduinolibrary/DFR0446_MP2636_Power_Booster_Charger_Module/master/MP2636%20Schematic.pdf',
    'mp2636_datasheet': 'https://raw.githubusercontent.com/Arduinolibrary/DFR0446_MP2636_Power_Booster_Charger_Module/master/MP2636%20Datasheet.pdf',
}


class ExtractText(HTMLParser):
    def __init__(self):
        super().__init__(); self.ignore=0; self.parts=[]

    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript'):
            self.ignore+=1
        if tag in ('p','li','h1','h2','h3','tr','br'):
            self.parts.append('\n')

    def handle_endtag(self,tag):
        if tag in ('script','style','noscript'):
            self.ignore=max(0,self.ignore-1)

    def handle_data(self,data):
        if not self.ignore and data.strip():
            self.parts.append(data.strip()+' ')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('names', nargs='*', default=list(SOURCES))
    args = parser.parse_args()
    target = ROOT / 'reference' / 'sources'
    target.mkdir(parents=True, exist_ok=True)
    for name in args.names:
        url = SOURCES[name]
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            payload=urllib.request.urlopen(request, timeout=25).read()
            if payload.startswith(b'%PDF'):
                (target/(name+'.pdf')).write_bytes(payload)
                print(name,'PDF已下载',len(payload),flush=True)
                continue
            raw = payload.decode('utf-8', errors='replace')
            archive=ROOT/'archive'/'source_downloads';archive.mkdir(parents=True,exist_ok=True)
            (archive / (name + '.html')).write_text(raw, encoding='utf-8')
            extractor=ExtractText();extractor.feed(raw)
            text='\n'.join(line.strip() for line in ''.join(extractor.parts).splitlines() if line.strip())
            (target / (name + '.txt')).write_text(url + '\n' + text, encoding='utf-8')
            found = re.findall(r'.{0,100}(?:[Bb]attery|[Cc]harging|[Pp]ower [Ss]upply|[Mm]icrophone|[Dd]imensions|5V|2A|2500|RTC|mm|8Ω).{0,180}', text)
            print(name, url, '\n' + '\n'.join(found[:35]), flush=True)
        except Exception as exc:
            print(name, type(exc).__name__, str(exc), flush=True)


if __name__ == '__main__':
    main()
