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

STYLE = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font:17px/1.5 Georgia,serif;max-width:1200px;margin:auto;padding:0 16px;background:#fff;color:#111}
table{border-collapse:collapse} td,th{vertical-align:top;padding:6px 10px;border-top:1px solid #ddd}
th{font:13px sans-serif} th a{color:#888;text-decoration:none} tr:target{background:#ffd}
@media(max-width:700px){td[lang]{display:none}}
@media(prefers-color-scheme:dark){body{background:#111;color:#ddd} tr:target{background:#332} a{color:#8af}}
</style>"""
CREDIT = (
    'Greek text edited by John Burnet; English translators credited with each dialogue.\n'
    'Raw TEI XML from the\n'
    '<a href="https://github.com/PerseusDL/canonical-greekLit/tree/master/data/tlg0059">\n'
    'Perseus Digital Library canonical Greek literature repository\n</a>,\n'
    '<a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>.\n'
    '<a href="sources.html">Sources, changes, and license</a>.'
)

TETRALOGIES = [
    ("Tetralogy I", ["Euthyphro", "Apology", "Crito", "Phaedo"]),
    ("Tetralogy II", ["Cratylus", "Theaetetus", "Sophist", "Statesman"]),
    ("Tetralogy III", ["Parmenides", "Philebus", "Symposium", "Phaedrus"]),
    ("Tetralogy IV", ["Alcibiades I", "Alcibiades II", "Hipparchus", "Lovers"]),
    ("Tetralogy V", ["Theages", "Charmides", "Laches", "Lysis"]),
    ("Tetralogy VI", ["Euthydemus", "Protagoras", "Gorgias", "Meno"]),
    ("Tetralogy VII", ["Hippias Major", "Hippias Minor", "Ion", "Menexenus"]),
    ("Tetralogy VIII", ["Cleitophon", "Republic", "Timaeus", "Critias"]),
    ("Tetralogy IX", ["Minos", "Laws", "Epinomis", "Letters"]),
]

DIALOGUE_INFO = {
    "Euthyphro": (
        "The porch of the King Archon in Athens, as Socrates and Euthyphro await separate court proceedings.",
        "Socrates; Euthyphro, a religious expert prosecuting his father.",
    ),
    "Apology": (
        "An Athenian court during Socrates’ trial for impiety and corrupting the young.",
        "Socrates addresses the jury; Meletus, one of his accusers, answers during cross-examination.",
    ),
    "Crito": (
        "Socrates’ prison cell in Athens, before dawn and shortly before his execution.",
        "Socrates; Crito, his old friend, who urges him to escape.",
    ),
    "Phaedo": (
        "At Phlius, where Phaedo recounts Socrates’ final day in an Athenian prison.",
        "Echecrates and Phaedo frame the account; Socrates, Simmias, Cebes, Crito, Apollodorus, and the prison servant appear in the recalled conversation.",
    ),
    "Cratylus": (
        "Athens; the precise location is not specified.",
        "Socrates; Hermogenes, who defends conventional names; Cratylus, who defends natural names.",
    ),
    "Theaetetus": (
        "A frame conversation at Megara introduces Euclides’ written account of an earlier discussion in an Athenian gymnasium.",
        "Euclides and Terpsion frame the account; Socrates questions Theaetetus in the presence of his teacher Theodorus.",
    ),
    "Sophist": (
        "Athens, on the day after the main conversation in the Theaetetus; the precise location is not named.",
        "The Eleatic Stranger leads the inquiry with Theaetetus; Theodorus and Socrates introduce and observe it.",
    ),
    "Statesman": (
        "The same Athenian gathering as the Sophist, which this dialogue immediately continues.",
        "The Eleatic Stranger leads the inquiry with Young Socrates; Theodorus and the elder Socrates are also present.",
    ),
    "Parmenides": (
        "In the frame, visitors from Clazomenae hear an account in Athens. The remembered debate took place at Pythodorus’ house in the Ceramicus during the Great Panathenaea.",
        "Cephalus, Adeimantus, Glaucon, and Antiphon frame the account; Pythodorus, a young Socrates, Zeno, Parmenides, and a young Aristoteles take part in the remembered meeting.",
    ),
    "Philebus": (
        "The dialogue gives no precise dramatic location, though the conversation is understood to be in Athens.",
        "Socrates and Protarchus conduct most of the inquiry; Philebus and a group of young followers are present.",
    ),
    "Phaedrus": (
        "Outside the walls of Athens, beside the Ilissus, under a plane tree.",
        "Socrates; Phaedrus, who carries and reads Lysias’ speech.",
    ),
    "Meno": (
        "Athens; the precise location is not specified.",
        "Socrates; Meno, a visiting Thessalian; one of Meno’s enslaved boys; Anytus, an Athenian politician.",
    ),
    "Hippias Major": (
        "A public place in Athens.",
        "Socrates; Hippias of Elis, a sophist, diplomat, and polymath.",
    ),
    "Hippias Minor": (
        "Athens, immediately after Hippias has given a public display; the precise venue is not named.",
        "Socrates; Hippias of Elis; Eudicus, who prompts their discussion.",
    ),
    "Menexenus": (
        "Athens, as Menexenus returns from the agora and Council Chamber; their exact meeting place is not specified.",
        "Socrates; Menexenus, a young Athenian considering a political career. Aspasia appears only in Socrates’ reported account.",
    ),
    "Cleitophon": (
        "Athens; the precise location is not specified, and the two speakers happen to be alone.",
        "Socrates; Cleitophon, who explains both his admiration for and dissatisfaction with Socratic teaching.",
    ),
    "Timaeus": (
        "An Athenian gathering on the day after the conversation Socrates summarizes at the opening; the precise location is not named.",
        "Socrates, Timaeus of Locri, Critias, and Hermocrates; an unnamed fourth guest from the previous day is absent through illness.",
    ),
    "Critias": (
        "The same Athenian gathering as the Timaeus, which this dialogue immediately continues.",
        "Critias leads the unfinished account; Socrates, Timaeus, and Hermocrates are present.",
    ),
    "Laws": (
        "A summer walk on Crete from Cnossos toward the cave and sanctuary of Zeus on Mount Ida.",
        "An unnamed Athenian Stranger; Clinias of Crete; Megillus of Sparta.",
    ),
    "Letters": (
        "No single dramatic setting: this is a collection of thirteen letters attributed to Plato.",
        "The attributed sender is Plato. Recipients include Dionysius II, Dion and his associates, Perdiccas, Hermeias, Erastus, Coriscus, Archytas, Aristodorus, and Laodamas.",
    ),
}

index = {}
for eng in sorted(glob.glob("src/*eng*.xml")):
    grc = glob.glob(eng.split(".perseus")[0] + ".perseus-grc*.xml")[0]
    title = field(eng, r"<title>([^<]+)")
    translator = field(eng, r'role="translator">([^<]+)')
    setting, people = DIALOGUE_INFO[title]
    slug = title.lower().replace(" ", "-")
    e, g = sections(eng), sections(grc)
    rows = "\n".join(
        f'<tr id="{n}">\n'
        f'<th><a href="#{n}">{n}</a></th>\n'
        f'<td>{e.get(n, "")}</td>\n'
        f'<td lang="grc">{g.get(n, "")}</td>\n'
        f'</tr>'
        for n in dict.fromkeys(list(e) + list(g)))
    open(f"{slug}.html", "w", encoding="utf-8").write(
        f"<!doctype html>{STYLE}\n<title>{title}</title>\n"
        f"<p>\n<a href=\"./\">← All dialogues</a> |\n"
        f"<a href=\"sources.html\">Sources &amp; license</a>\n</p>\n"
        f"<h1>Plato, {title}</h1>\n<p>\nTranslation: {translator}.\n</p>\n"
        f"<p>\n"
        f"<strong>Setting:</strong> {setting}\n</p>\n"
        f"<p><strong>People:</strong></p>\n<ul>\n"
        + "\n".join(f"<li>{person}</li>" for person in people.split("; "))
        + "\n</ul>\n"
        f"<table>\n{rows}\n</table>\n")
    index[title] = f'<li><a href="{slug}.html">{title}</a> <small>({translator})</small></li>'
    print(f"{slug}: {len(e)} eng / {len(g)} grc sections")

groups = []
listed = set()
for group, titles in TETRALOGIES:
    dialogues = [index[title] for title in titles if title in index]
    if dialogues:
        groups.append(f"<h2>{group}</h2>\n<ul>\n" + "\n".join(dialogues) + "\n</ul>")
        listed.update(title for title in titles if title in index)
unclassified = [item for title, item in index.items() if title not in listed]
if unclassified:
    groups.append("<h2>Other works</h2>\n<ul>\n" + "\n".join(unclassified) + "\n</ul>")

open("index.html", "w", encoding="utf-8").write(
    f"<!doctype html>{STYLE}\n<title>Plato</title>\n<h1>Plato</h1>\n"
    f"<p>\nEnglish and Greek side by side by Stephanus section,\n"
    f"grouped by the traditional tetralogies.\n</p>\n"
    f"<p>\n<strong>About.</strong>\nThis is an unofficial, independently generated mirror.\n"
    f"The texts and translations are not original to this site. Raw TEI XML comes from the\n"
    f"<a href=\"https://github.com/PerseusDL/canonical-greekLit/tree/master/data/tlg0059\">Perseus Digital Library</a>\n"
    f"under <a href=\"https://creativecommons.org/licenses/by-sa/4.0/\">CC BY-SA 4.0</a>.\n"
    f"<a href=\"sources.html\">Sources &amp; license</a> |\n"
    f"<a href=\"https://github.com/cb341/plato\">GitHub</a>\n</p>\n"
    + "\n".join(groups) + "\n")

open("sources.html", "w", encoding="utf-8").write(
    f'''<!doctype html>{STYLE}
<title>Sources &amp; license | Plato</title>
<p><a href="./">← All dialogues</a></p>
<h1>Sources &amp; license</h1>
<h2>About this site</h2>
<p>This is an unofficial, independently generated mirror for convenient parallel reading. The
Greek text, English translations, and scholarly editions are not the work of this site’s
maintainer. This site is not affiliated with or endorsed by the Perseus Digital Library, Tufts
University, Harvard University Press, or the Loeb Classical Library. The source code for this
mirror is available in the <a href="https://github.com/cb341/plato">project repository on
GitHub</a>.</p>
<h2>Raw data and editions</h2>
<p>The raw data is TEI XML from the Perseus Digital Library’s
<a href="https://github.com/PerseusDL/canonical-greekLit/tree/master/data/tlg0059">Plato files
in <code>PerseusDL/canonical-greekLit</code></a>. The XML headers identify the English source as
<cite>Plato in Twelve Volumes</cite>, translated by Harold North Fowler, Robert Gregg Bury (also
credited as R. G. Bury), and Walter Rangeley Maitland Lamb. They identify the Greek source as
John Burnet’s <cite>Platonis Opera</cite>, published by Clarendon Press.</p>
<h2>Changes made here</h2>
<p>The build script extracts the English and Greek text from the source XML, removes notes and
most TEI markup, groups both texts by Stephanus section, and generates the HTML presentation and
index. The wording of the Perseus texts is not intentionally revised. The grouping, navigation,
and page layout are additions made by this mirror.</p>
<h2>License</h2>
<p>Perseus publishes the upstream repository under the
<a href="https://creativecommons.org/licenses/by-sa/4.0/">Creative Commons
Attribution-ShareAlike 4.0 International license (CC BY-SA 4.0)</a>. The repository’s own
<a href="https://github.com/PerseusDL/canonical-greekLit/blob/master/license.md">license file</a>
contains the complete legal text. The source XML and derived text pages in this mirror are
redistributed under the same license. See also this project’s local <a href="LICENSE">license
and attribution notice</a>.</p>
<p>Under CC BY-SA 4.0, reuse requires attribution, a license link, an indication of changes, and
distribution of adaptations under the same or a compatible license. No endorsement by the
original authors, editors, translators, publishers, or data providers is implied.</p>
''')
