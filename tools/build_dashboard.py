"""AI 사무실 진행 현황 대시보드 생성기 (표준 라이브러리만 사용, 비용 없음)

사용법:  python tools/build_dashboard.py          → dashboard/index.html 생성
         python tools/build_dashboard.py --watch  → 3초마다 다시 생성 (작업 중 실시간 보기)
브라우저에서 dashboard/index.html 을 열어 두면 5초마다 자동 새로고침됩니다.
"""
import html, re, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard" / "index.html"
STAGES = ["접수", "호출 시작", "호출 종료", "검수", "재검토 요청", "종합보고", "승인 요청", "승인"]
STAGE_LABEL = {"접수": "접수", "호출 시작": "직원 배정", "호출 종료": "직원 보고", "검수": "사무장 검수",
               "재검토 요청": "재검토", "종합보고": "종합보고", "승인 요청": "승인 요청", "승인": "승인"}
WHO_CLASS = {"사무장": "boss", "immigration-specialist": "staff", "대표 행정사": "chief"}


def esc(s):
    return html.escape(str(s))


def read(p):
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def parse_log():
    rows = []
    for line in read(ROOT / "logs" / "work-log.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
            rows.append(dict(zip(["time", "case", "who", "stage", "text"], cells)))
    return rows


def field(text, name):
    m = re.search(rf"^- {re.escape(name)}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def cell(text, name):
    m = re.search(rf"^\|\s*{re.escape(name)}\s*\|\s*(.+?)\s*\|", text, re.M)
    return m.group(1).strip() if m else ""


def cases(log):
    out = []
    for d in sorted((ROOT / "cases").glob("*/")):
        info = read(d / "case-info.md")
        evs = [r for r in log if r["case"] == d.name]
        done = {r["stage"] for r in evs}
        rejected = "반려" in done
        calls = sum(1 for r in evs if r["stage"] == "호출 시작")
        reviews = sum(1 for r in evs if r["stage"] == "재검토 요청")
        files = sorted(p.name for p in d.glob("*.md"))
        final = read(d / "final-report.md")
        verdict = ""
        m = re.search(r"종합 판단:\s*\*\*(.+?)\*\*", read(d / sorted([f for f in files if f.startswith("report-v")] or ["_"])[-1]))
        if m:
            verdict = m.group(1)
        out.append(dict(id=d.name, task=field(info, "의뢰 업무"), status=field(info, "진행 상태"),
                        client=cell(info, "고객명(가명)"), cur=cell(info, "현재 체류자격"),
                        want=cell(info, "희망 체류자격"), done=done, rejected=rejected, calls=calls,
                        reviews=reviews, files=files, verdict=verdict,
                        approved="[x] 승인" in final, last=evs[-1] if evs else None))
    return out


def render():
    log = parse_log()
    cs = cases(log)
    knowledge = sorted(p.name for p in (ROOT / "knowledge").glob("*.md") if p.name not in ("README.md",))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    staff_calls = sum(1 for r in log if r["stage"] == "호출 시작")

    case_html = []
    for c in cs:
        steps = []
        for s in STAGES:
            cls = "on" if s in c["done"] else ""
            if s == "재검토 요청" and s not in c["done"] and "종합보고" in c["done"]:
                cls = "skip"
            steps.append(f'<li class="{cls}"><span></span>{esc(STAGE_LABEL[s])}</li>')
        badge = "승인" if c["approved"] else ("반려" if c["rejected"] else c["status"] or "진행 중")
        bcls = "ok" if c["approved"] else ("bad" if c["rejected"] else "wait")
        links = " ".join(f'<a href="../cases/{esc(c["id"])}/{esc(f)}">{esc(f)}</a>' for f in c["files"])
        last = c["last"]
        case_html.append(f"""
<section class="card">
  <div class="row"><h2>{esc(c['id'])}</h2><span class="badge {bcls}">{esc(badge)}</span></div>
  <p class="sub">{esc(c['client'])} · {esc(c['cur'])} → {esc(c['want'])} · {esc(c['task'])}</p>
  <ol class="pipe">{''.join(steps)}</ol>
  <div class="stats">
    <div><b>{c['calls']}</b><small>직원 호출</small></div>
    <div><b>{c['reviews']}</b><small>재검토</small></div>
    <div><b>{esc(c['verdict'] or '—')}</b><small>종합 판단</small></div>
  </div>
  <p class="files">{links}</p>
  {f'<p class="last">최근: {esc(last["time"])} · {esc(last["who"])} · {esc(last["text"])}</p>' if last else ''}
</section>""")

    tl = []
    for r in reversed(log):
        who = r["who"]
        k = next((v for key, v in WHO_CLASS.items() if who.startswith(key)), "boss")
        if "→" in who:
            k = "handoff"
        tl.append(f'<li class="{k}"><time>{esc(r["time"][11:])}<br><small>{esc(r["time"][:10])}</small></time>'
                  f'<div><span class="who">{esc(who)}</span> <span class="stage">{esc(r["stage"])}</span>'
                  f'<span class="case">{esc(r["case"])}</span><p>{esc(r["text"])}</p></div></li>')

    kn = "".join(f'<li><a href="../knowledge/{esc(k)}">{esc(k)}</a></li>' for k in knowledge) or "<li>없음</li>"

    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="5">
<title>AI 사무실 현황</title>
<style>
:root{{--bg:#f6f5f1;--card:#fff;--ink:#1d1d1b;--mute:#6b6a65;--line:#e4e2dc;--boss:#2f5d8a;--staff:#2e7d5b;--chief:#9a5b13;--hand:#6a4c93;--ok:#2e7d5b;--wait:#9a5b13;--bad:#b3261e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161614;--card:#211f1d;--ink:#ecebe6;--mute:#a19f98;--line:#35332f;--boss:#7fb0e0;--staff:#6cc79e;--chief:#e0a560;--hand:#b79be0;--ok:#6cc79e;--wait:#e0a560;--bad:#f08a80}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif}}
header{{padding:24px 16px 8px;max-width:1100px;margin:auto}}h1{{margin:0;font-size:22px}}header p{{margin:4px 0 0;color:var(--mute);font-size:13px}}
main{{max-width:1100px;margin:auto;padding:8px 16px 40px;display:grid;grid-template-columns:1.1fr 1fr;gap:16px}}
@media (max-width:820px){{main{{grid-template-columns:1fr}}}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}}
.row{{display:flex;justify-content:space-between;align-items:center}}h2{{margin:0;font-size:18px}}h3{{margin:0 0 10px;font-size:15px}}
.sub{{color:var(--mute);margin:4px 0 12px;font-size:13px}}
.badge{{font-size:12px;padding:2px 10px;border-radius:99px;border:1px solid currentColor}}.ok{{color:var(--ok)}}.wait{{color:var(--wait)}}.bad{{color:var(--bad)}}
.pipe{{list-style:none;padding:0;margin:0 0 14px;display:flex;flex-wrap:wrap;gap:4px}}
.pipe li{{font-size:12px;color:var(--mute);display:flex;align-items:center;gap:5px;padding:3px 8px;border:1px solid var(--line);border-radius:6px}}
.pipe li span{{width:8px;height:8px;border-radius:50%;background:var(--line)}}
.pipe li.on{{color:var(--ink);border-color:var(--staff)}}.pipe li.on span{{background:var(--staff)}}.pipe li.skip{{opacity:.45;text-decoration:line-through}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:10px}}
.stats div{{border:1px solid var(--line);border-radius:8px;padding:8px;text-align:center}}.stats b{{display:block;font-size:17px}}.stats small{{color:var(--mute)}}
.files a{{font-size:12px;margin-right:8px;color:var(--boss)}}.last{{font-size:12px;color:var(--mute);margin:6px 0 0}}
.org{{display:grid;gap:8px}}.org div{{border-left:4px solid;padding:6px 10px;border-radius:4px;background:color-mix(in srgb,var(--card) 92%,var(--ink))}}
.org .c{{border-color:var(--chief)}}.org .b{{border-color:var(--boss)}}.org .s{{border-color:var(--staff)}}.org small{{color:var(--mute);display:block}}
ul.tl{{list-style:none;margin:0;padding:0}}ul.tl li{{display:grid;grid-template-columns:70px 1fr;gap:10px;padding:10px 0;border-top:1px solid var(--line)}}
ul.tl time{{font-variant-numeric:tabular-nums;font-size:13px}}ul.tl time small{{color:var(--mute)}}ul.tl p{{margin:2px 0 0;font-size:13px;color:var(--mute);overflow-wrap:anywhere}}
.who{{font-weight:600;font-size:13px}}.boss .who{{color:var(--boss)}}.staff .who{{color:var(--staff)}}.chief .who{{color:var(--chief)}}.handoff .who{{color:var(--hand)}}
.stage{{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:0 6px;margin-left:4px}}.case{{font-size:11px;color:var(--mute);margin-left:6px}}
.kn li{{font-size:13px}}.kn a{{color:var(--boss)}}
</style></head><body>
<header><h1>Immigration AI Office — 진행 현황</h1>
<p>갱신 {esc(now)} · 5초마다 자동 새로고침 · 사건 {len(cs)}건 · 직원 호출 누계 {staff_calls}회 · 가상 고객 테스트</p></header>
<main>
<div>
  <section class="card"><h3>조직</h3><div class="org">
    <div class="c"><b>대표 행정사</b><small>최종 승인 (사람)</small></div>
    <div class="b"><b>AI 사무장</b><small>메인 Claude Code · 접수·배정·검수·재검토·승인 요청</small></div>
    <div class="s"><b>immigration-specialist</b><small>Subagent · Skills: visa-review · legal-research · document-prep · case-report</small></div>
  </div></section>
  {''.join(case_html) or '<section class="card">사건 없음</section>'}
  <section class="card kn"><h3>확인된 지식 (knowledge)</h3><ul>{kn}</ul></section>
</div>
<section class="card"><h3>업무기록 (최신순)</h3><ul class="tl">{''.join(tl) or '<li>기록 없음</li>'}</ul></section>
</main></body></html>"""


def build():
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    build()
    print(f"생성: {OUT}")
    if "--watch" in sys.argv:
        print("실시간 갱신 중 (Ctrl+C 로 종료)")
        while True:
            time.sleep(3)
            build()
