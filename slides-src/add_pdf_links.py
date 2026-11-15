from pathlib import Path
import fitz

path = Path('/root/work/slides/Walkback-Envelope-7-slides.pdf')
doc = fitz.open(path)
page = doc[6]
sx, sy = page.rect.width / 1920, page.rect.height / 1080
links = [
    ((68, 300, 1040, 355), 'https://ordinatum.github.io/walkback-envelope/'),
    ((68, 456, 1040, 508), 'https://github.com/ordinatum/walkback-envelope'),
]
for old in list(page.get_links()):
    page.delete_link(old)
for box, uri in links:
    rect = fitz.Rect(box[0]*sx, box[1]*sy, box[2]*sx, box[3]*sy)
    page.insert_link({'kind': fitz.LINK_URI, 'from': rect, 'uri': uri})
out = path.with_name('Walkback-Envelope-7-slides-linked.pdf')
doc.save(out)
doc.close()
out.replace(path)
with fitz.open(path) as checked:
    actual = checked[6].get_links()
    assert len(checked) == 7
    assert {x['uri'] for x in actual} == {x[1] for x in links}
    print('Verified: 7 pages; clickable repository and live-demo links on page 7')
