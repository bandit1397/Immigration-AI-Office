# Immigration AI Office (1단계: 최소 구성 테스트)

Claude Pro + Claude Code만으로 운영하는 **가상 이민행정사 AI 사무실**입니다.
API 키·유료 API·외부 서버를 쓰지 않습니다. (모든 작업은 Pro 사용량을 공유합니다.)

## 조직 (최소 2명 + 사람 1명)

```
대표 행정사 (사용자, 최종 승인)
   └─ AI 사무장 (메인 Claude Code, CLAUDE.md)
         └─ AI 이민행정 전문 직원 (immigration-specialist Subagent)
               └─ 보유 능력(Skills): visa-review · legal-research · document-prep · case-report
```

직원을 업무별로 쪼개지 않고, **한 직원이 사건 하나를 처음부터 끝까지** 처리합니다.
"자기 오류를 못 보는" 문제는 **사무장 검수(체크리스트) → 재검토 지시 → 대표 행정사 승인**으로 보완합니다.

## 파일 구조

| 경로 | 역할 |
|---|---|
| `CLAUDE.md` | AI 사무장 업무 규칙 (사건번호, 절차, 기록, 승인 규칙) |
| `.claude/agents/immigration-specialist.md` | 전문 직원의 직무기술서 (역할·도구·권한·보고 방식) |
| `.claude/skills/*/SKILL.md` | 직원의 업무 능력 4종 (요건검토·법령조사·서류·보고서 양식) |
| `.claude/settings.json` | 권한 설정 (공식 사이트 조회 허용, 메일 발송 차단) |
| `cases/<사건번호>/` | 사건별 공통정보 + 직원 보고서 + 검수기록 + 종합보고서 |
| `logs/work-log.md` | 호출 시작/종료, 재검토, 승인 요청 업무기록 |
| `knowledge/` | 공식 출처 목록, 확인된 법령 메모 |
| `templates/` | 사건정보·검수·종합보고서 양식 |
| `tools/build_dashboard.py` → `dashboard/index.html` | 브라우저 진행 현황 대시보드 (`--watch` 로 실시간 갱신) |

## 테스트 방법

1. VS Code에서 이 폴더를 열고 터미널에서 `claude` 실행 (이미 실행 중이었다면 **재시작**해야 새 에이전트·스킬이 인식됩니다).
2. `/agents` 입력 → **Project agents** 에 `immigration-specialist` 가 보이는지 확인.
3. 아래 프롬프트 입력:

```
TEST-001 사건을 CLAUDE.md 표준 업무 절차대로 처리하라.
cases/TEST-001/case-info.md 에 가상 고객정보가 있다.
immigration-specialist 를 실제로 호출하고, 검수 후 부족하면 재검토를 1회 이상 요청하라.
각 단계를 logs/work-log.md 에 기록하고, 마지막에 나에게 승인을 요청하라.
```

4. 결과 확인
   - 화면에 `immigration-specialist` Agent 호출 표시가 나타나는지 (흉내가 아닌 실제 호출)
   - `cases/TEST-001/` 에 `report-v1.md`, `review-v1.md`, (`report-v2.md`), `final-report.md` 생성
   - 보고서 상단 `작성자: immigration-specialist`
   - `logs/work-log.md` 에 호출 시작/종료/재검토/승인 요청 기록
   - 법령 인용마다 출처·기준일, 모르는 것은 `[확인 필요]`
5. 승인/반려: `TEST-001 승인한다` 또는 `TEST-001 반려, 사유: …` 라고 입력.

### 재검토 기능만 따로 시험하기

```
TEST-001 report-v1.md 를 검수하면서, 법령 인용 중 기준일이 없는 것을 모두 지적해 재검토를 요청하라.
수정 전/후 의견과 수정 이유가 report-v2.md 11번 항목에 기록되는지 확인하라.
```

## 직원 추가 방법 (향후)

1. `.claude/agents/` 에 새 파일 추가 (예: `work-visa-specialist.md`, `auditor.md`) — 기존 Skills를 `skills:` 로 재사용
2. `CLAUDE.md` "4. 배정 규칙" 표에 한 줄 추가

## 주의

- 가상 고객정보만 사용. 실무 사건 폴더(`cases/IMM-*`)는 `.gitignore` 로 GitHub 업로드가 차단됩니다.
- AI 결과는 초안입니다. 최종 판단과 제출은 대표 행정사가 합니다.
