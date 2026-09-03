import json, re, time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

UA='The-Radar-Feed-Updater/1.0 (+GitHub Actions)'
RSS=[
 ('Nature','SCIENCE','https://www.nature.com/nature.rss'),
 ('IEEE Spectrum','TECH','https://spectrum.ieee.org/feeds/feed.rss'),
 ('STAT','HEALTHCARE','https://www.statnews.com/feed/'),
 ('Reddit · MachineLearning','SCIENCE','https://www.reddit.com/r/MachineLearning/.rss'),
 ('Reddit · Robotics','ROBOTICS','https://www.reddit.com/r/robotics/.rss'),
 ('Reddit · Hardware','CHIPS','https://www.reddit.com/r/hardware/.rss'),
 ('TechCrunch','TECH','https://techcrunch.com/feed/'),
 ('Ars Technica','TECH','https://feeds.arstechnica.com/arstechnica/index'),
 ('Wired','TECH','https://www.wired.com/feed/rss'),
]

def get(url):
    req=Request(url,headers={'User-Agent':UA,'Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'})
    with urlopen(req,timeout=25) as r: return r.read()

def clean(s):
    s=re.sub(r'<[^>]+>',' ',s or '')
    return re.sub(r'\s+',' ',s).strip()[:500]

def tag(el,n):
    for c in list(el):
        if c.tag.split('}')[-1].lower()==n.lower(): return (c.text or '').strip()
    return ''

def parse_xml(data,source,base):
    root=ET.fromstring(data); out=[]
    for n in root.iter():
        if n.tag.split('}')[-1].lower() not in ('item','entry'): continue
        title=tag(n,'title') or 'Untitled'; text=clean(tag(n,'description') or tag(n,'summary') or tag(n,'content'))
        link=tag(n,'link')
        if not link:
            for c in list(n):
                if c.tag.split('}')[-1].lower()=='link' and c.attrib.get('href'): link=c.attrib['href']; break
        date=tag(n,'pubDate') or tag(n,'published') or tag(n,'updated') or datetime.now(timezone.utc).isoformat()
        out.append({'title':title,'text':text,'link':link or base,'date':date,'source':source,'cat':base})
        if len(out)>=18: break
    return out

def hn():
    ids=json.loads(get('https://hacker-news.firebaseio.com/v0/topstories.json'))[:24]
    out=[]
    for i in ids:
        try:
            x=json.loads(get(f'https://hacker-news.firebaseio.com/v0/item/{i}.json'))
            if x.get('title'): out.append({'title':x['title'],'text':'Hacker News discussion and source.','link':x.get('url') or f'https://news.ycombinator.com/item?id={i}','date':datetime.fromtimestamp(x.get('time',time.time()),timezone.utc).isoformat(),'source':'Hacker News','cat':'TECH','points':x.get('score',0),'kindLabel':'HN API'})
        except Exception: pass
    return out

def arxiv(query,name,cat):
    url='https://export.arxiv.org/api/query?'+urlencode({'search_query':query,'start':0,'max_results':15,'sortBy':'submittedDate','sortOrder':'descending'})
    root=ET.fromstring(get(url)); out=[]
    for n in root.iter():
        if n.tag.split('}')[-1]!='entry': continue
        title=tag(n,'title'); summary=clean(tag(n,'summary')); ident=tag(n,'id'); pub=tag(n,'published')
        if title: out.append({'title':title,'text':summary,'link':ident,'date':pub,'source':name,'cat':cat,'kindLabel':'ARXIV'})
    return out

def main():
    items=[]; health=[]
    try:
        x=hn(); items+=x; health.append({'name':'Hacker News','ok':True,'count':len(x)})
    except Exception as e: health.append({'name':'Hacker News','ok':False,'count':0,'error':str(e)})
    for query,name,cat in [('cat:cs.LG OR cat:cs.AI','arXiv · AI/ML','SCIENCE'),('cat:cs.DC OR cat:eess.SY','arXiv · Systems','TECH')]:
        try:
            x=arxiv(query,name,cat); items+=x; health.append({'name':name,'ok':True,'count':len(x)})
        except Exception as e: health.append({'name':name,'ok':False,'count':0,'error':str(e)})
    for name,cat,url in RSS:
        try:
            x=parse_xml(get(url),name,cat); items+=x; health.append({'name':name,'ok':True,'count':len(x)})
        except Exception as e: health.append({'name':name,'ok':False,'count':0,'error':str(e)})
    # De-duplicate exact titles, keep first source.
    seen=set(); ded=[]
    for x in items:
        k=re.sub(r'\W+',' ',x['title'].lower()).strip()
        if k and k not in seen: seen.add(k); ded.append(x)
    payload={'generated_at':datetime.now(timezone.utc).isoformat(),'items':ded[:220],'health':health}
    p='data/feeds.json'; open(p,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2))
    print('Wrote',p,'with',len(ded),'items')

if __name__=='__main__': main()
