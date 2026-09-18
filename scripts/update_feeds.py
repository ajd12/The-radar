import json, os, re, time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

UA = "The-Radar-Feed-Updater/4.0 (+GitHub Actions)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
REGISTRY_PATH = os.path.join(DATA_DIR, "source-registry.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "feeds.json")

def get(url):
    req = Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, application/json, */*"
    })
    with urlopen(req, timeout=25) as response:
        return response.read()

def clean(value, limit=650):
    value = value or ""
    value = re.sub(r"<script.*?</script>|<style.*?</style>", " ", value, flags=re.I|re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]

def local_name(tag):
    return tag.split("}")[-1].lower()

def child_text(node, names):
    names = {n.lower() for n in names}
    for child in list(node):
        if local_name(child.tag) in names:
            return "".join(child.itertext()).strip()
    return ""

def parse_xml(data, source, category, base_url, kind_label="RSS"):
    root = ET.fromstring(data)
    output = []
    for node in root.iter():
        if local_name(node.tag) not in ("item", "entry"):
            continue
        title = child_text(node, ["title"]) or "Untitled signal"
        summary = child_text(node, ["description", "summary", "content", "encoded"])
        link = child_text(node, ["link"])
        if not link:
            for child in list(node):
                if local_name(child.tag) == "link" and child.attrib.get("href"):
                    link = child.attrib["href"]
                    break
        date = child_text(node, ["pubDate", "published", "updated", "date"]) or datetime.now(timezone.utc).isoformat()
        output.append(normalize(title, summary, link or base_url, date, source, category, kind_label))
        if len(output) >= 24:
            break
    return output

def normalize(title, summary, link, date, source, category, kind_label):
    text = clean(summary)
    tags = infer_tags(title + " " + text, category)
    novelty = min(98, 35 + len(tags)*7 + (10 if kind_label in ("ARXIV", "PATENT") else 0))
    momentum = min(98, 40 + (hash(title) % 45))
    confidence = 78 if kind_label in ("ARXIV", "RSS", "HN API") else 62
    signal = round(0.4*novelty + 0.35*momentum + 0.25*confidence)
    ident = re.sub(r"[^a-z0-9]+", "-", (source + "-" + title).lower()).strip("-")[:150]
    return {
        "id": ident,
        "title": clean(title, 300),
        "summary": text or "Source item available; open the source for details.",
        "text": text,
        "link": link,
        "date": date,
        "source": source,
        "category": category,
        "topic": topic_for(category, tags),
        "kind_label": kind_label,
        "tags": tags,
        "novelty_score": novelty,
        "momentum_score": momentum,
        "confidence_score": confidence,
        "signal_score": signal
    }

def infer_tags(text, category):
    t = text.lower()
    candidates = [
        ("SDV", ["software-defined vehicle", "sdv", "vehicle compute", "zonal"]),
        ("HPC", ["high-performance compute", "hpc", "central compute", "accelerator"]),
        ("AUTOSAR", ["autosar"]),
        ("FOTA", ["fota", "over-the-air", "ota update"]),
        ("Chiplets", ["chiplet", "chiplet"]),
        ("Packaging", ["advanced packaging", "2.5d", "3d integration"]),
        ("Robotics", ["robot", "robotics", "manipulation"]),
        ("AI", ["artificial intelligence", "machine learning", "foundation model", "neural"]),
        ("Semiconductors", ["semiconductor", "chip", "transistor", "gpu", "npu"]),
        ("Energy", ["battery", "solar", "nuclear", "hydrogen", "energy"]),
        ("Digital Twins", ["digital twin"]),
        ("Cybersecurity", ["cybersecurity", "security", "vulnerability"]),
        ("Biotech", ["biotech", "gene", "crispr", "clinical"]),
        ("Control", ["control system", "lqr", "pid", "autonomous"]),
        ("Materials", ["material", "graphene", "catalyst", "alloy"])
    ]
    tags = [label for label, words in candidates if any(w in t for w in words)]
    if category not in ("TECH", "SCIENCE") and category.title() not in tags:
        tags.insert(0, category.title())
    return tags[:7] or [category.title()]

def topic_for(category, tags):
    if "SDV" in tags or "AUTOSAR" in tags or "FOTA" in tags or "HPC" in tags: return "Automotive"
    if "Chiplets" in tags or "Packaging" in tags or "Semiconductors" in tags: return "Semiconductors"
    if "Robotics" in tags: return "Robotics"
    if "Energy" in tags: return "Energy"
    if "Biotech" in tags: return "Healthcare"
    if "Materials" in tags: return "Materials"
    return category.title()

def hacker_news():
    ids = json.loads(get("https://hacker-news.firebaseio.com/v0/topstories.json"))[:30]
    output = []
    for story_id in ids:
        try:
            item = json.loads(get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"))
            if item.get("title"):
                output.append(normalize(
                    item["title"], "Hacker News discussion and linked source.",
                    item.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                    datetime.fromtimestamp(item.get("time", time.time()), timezone.utc).isoformat(),
                    "Hacker News", "TECH", "HN API"
                ))
        except Exception:
            continue
    return output

def arxiv(query, source, category):
    url = "https://export.arxiv.org/api/query?" + urlencode({
        "search_query": query, "start": 0, "max_results": 18,
        "sortBy": "submittedDate", "sortOrder": "descending"
    })
    return parse_xml(get(url), source, category, "https://arxiv.org", "ARXIV")

def main():
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)
    items, health = [], []
    for source in registry["sources"]:
        if not source.get("enabled", True):
            continue
        name, category, kind = source["name"], source["category"], source["kind"]
        try:
            if kind == "api" and name == "Hacker News":
                batch = hacker_news()
            elif kind == "rss":
                batch = parse_xml(get(source["url"]), name, category, source["url"], "RSS")
            elif kind == "arxiv":
                batch = arxiv(source["query"], name, category)
            else:
                batch = []
            items.extend(batch)
            health.append({"name": name, "ok": True, "count": len(batch)})
        except Exception as exc:
            health.append({"name": name, "ok": False, "count": 0, "error": str(exc)[:220]})
    dedup, seen = [], set()
    for item in items:
        key = item["link"] or item["title"].lower()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    dedup.sort(key=lambda x: x.get("date", ""), reverse=True)
    payload = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": dedup[:300],
        "health": health
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUTPUT_PATH} with {len(dedup[:300])} items")

if __name__ == "__main__":
    main()
