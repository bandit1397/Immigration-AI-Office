"""사건 보고서(.md)를 PDF로 변환한다. Chrome(없으면 Edge) 헤드리스 인쇄를 사용한다(외부 서버 없음).

사용법: python tools/md_to_pdf.py cases/TEST-002/final-report.md [다른 .md ...]
결과: 같은 폴더에 같은 이름의 .pdf
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

EDGE_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 15mm 12mm; }
body { font-family: 'Malgun Gothic', sans-serif; font-size: 10pt; line-height: 1.5; color: #111; }
h1 { font-size: 17pt; border-bottom: 2px solid #333; padding-bottom: 4px; }
h2 { font-size: 13pt; border-bottom: 1px solid #999; margin-top: 18px; }
h3 { font-size: 11pt; }
table { border-collapse: collapse; width: 100%; margin: 6px 0; font-size: 8.5pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #888; padding: 3px 5px; vertical-align: top; word-break: break-all; }
th { background: #eee; }
blockquote { border-left: 3px solid #c00; margin: 6px 0; padding: 2px 8px; color: #600; background: #fff5f5; }
code { font-family: Consolas, monospace; font-size: 9pt; }
.footer-note { margin-top: 24px; font-size: 8pt; color: #666; border-top: 1px solid #ccc; padding-top: 4px; }
"""


def find_browser() -> str:
    for p in EDGE_CANDIDATES:
        if Path(p).exists():
            return p
    sys.exit("Edge/Chrome을 찾지 못했습니다.")


def convert(md_path: Path, browser: str) -> Path:
    text = md_path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->\s*", "", text, flags=re.S)  # 저장자 주석 제거
    body = markdown.markdown(text, extensions=["tables", "sane_lists"])
    html = (
        f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
        f"<title>{md_path.parent.name} {md_path.stem}</title><style>{CSS}</style></head>"
        f"<body>{body}<div class='footer-note'>원본: {md_path.parent.name}/{md_path.name} · "
        f"가상(테스트) 사건 · 대표 행정사 승인 전 문서는 외부 제출 금지</div></body></html>"
    )
    pdf_path = md_path.with_suffix(".pdf")
    with tempfile.TemporaryDirectory() as tmp:
        html_file = Path(tmp) / "report.html"
        html_file.write_text(html, encoding="utf-8")
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--user-data-dir={Path(tmp) / 'profile'}",
             f"--print-to-pdf={pdf_path.resolve()}", html_file.resolve().as_uri()],
            check=True, capture_output=True, timeout=120,
        )
    return pdf_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    browser = find_browser()
    for arg in sys.argv[1:]:
        out = convert(Path(arg), browser)
        print(f"생성: {out} ({out.stat().st_size:,} bytes)")
