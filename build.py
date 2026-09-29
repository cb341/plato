"""Build one offline HTML page per Plato dialogue from Perseus TEI (English + Greek, by Stephanus section).
Usage: python3 build.py            (reads src/*.xml, writes *.html + index.html)
"""
import re, glob, os

def sections(path):
    body = open(path, encoding="utf-8").read().split("<body", 1)[1].split("</body>")[0]
    body = re.sub(r'<milestone[^>]*n="(\d+[a-e])"[^>]*unit="section"[^>]*/>|<milestone[^>]*unit="section"[^>]*n="(\d+[a-e])"[^>]*/>',
                  lambda m: "\0" + (m[1] or m[2]) + "\0", body)
    body = re.sub(r"<note.*?</note>", "", body, flags=re.S)
    body = body.replace("<label>", "\1").replace("</label>", "\2").replace("</p>", "\3")
    body = re.sub(r"<[^>]+>", "", body)
    body = re.sub(r"\s+", " ", body)
    body = body.replace("\1", "<b>").replace("\2", "</b>").replace("\3", "<br>")
    parts = body.split("\0")[1:]
    out = {}
    for n, text in zip(parts[::2], parts[1::2]):
        out[n] = out.get(n, "") + re.sub(r"^(\s*<br>)+|(<br>\s*)+$", "", text.strip())
    return out

def field(path, pattern):
    return re.search(pattern, open(path, encoding="utf-8").read())[1].strip()

STYLE = """<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font:17px/1.5 Georgia,serif;max-width:1200px;margin:auto;padding:0 16px;background:#fff;color:#111}
table{border-collapse:collapse} td,th{vertical-align:top;padding:6px 10px;border-top:1px solid #ddd}
th{font:13px sans-serif} th a{color:#888;text-decoration:none} tr:target{background:#ffd}
@media(max-width:700px){td[lang]{display:none}}
@media(prefers-color-scheme:dark){body{background:#111;color:#ddd} tr:target{background:#332} a{color:#8af}}
</style>"""
CREDIT = "Greek: Burnet. Source: Perseus Digital Library, licensed CC BY-SA 4.0."

index = []
for eng in sorted(glob.glob("src/*eng*.xml")):
    grc = glob.glob(eng.split(".perseus")[0] + ".perseus-grc*.xml")[0]
    title = field(eng, r"<title>([^<]+)")
    translator = field(eng, r'role="translator">([^<]+)')
    slug = title.lower().replace(" ", "-")
    e, g = sections(eng), sections(grc)
    rows = "\n".join(
        f'<tr id="{n}"><th><a href="#{n}">{n}</a></th><td>{e.get(n, "")}</td><td lang="grc">{g.get(n, "")}</td></tr>'
        for n in dict.fromkeys(list(e) + list(g)))
    open(f"{slug}.html", "w", encoding="utf-8").write(
        f"<!doctype html>{STYLE}<title>{title}</title>\n<p><a href=\"./\">← All dialogues</a></p>\n"
        f"<h1>Plato, {title}</h1>\n<p>Trans. {translator}. {CREDIT} Link a passage as <code>#10a</code>.</p>\n"
        f"<table>\n{rows}\n</table>\n")
    index.append(f'<li><a href="{slug}.html">{title}</a> <small>({translator})</small></li>')
    print(f"{slug}: {len(e)} eng / {len(g)} grc sections")

open("index.html", "w", encoding="utf-8").write(
    f"<!doctype html>{STYLE}<title>Plato</title>\n<h1>Plato</h1>\n<p>English and Greek side by side, "
    f"by Stephanus section. {CREDIT}</p>\n<ul>\n" + "\n".join(index) + "\n</ul>\n")
