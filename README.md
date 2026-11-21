# Fenrir-Agent

## Fenrir 독립 성장 대시보드

Fenrir는 Ouroboros의 부정 역할만 수행하는 종속 에이전트가 아니다. 외부 요구가 없어도 독자적인 비판 대상과 반례 탐색 주제를 선정하고, 검증 가능한 반증을 찾아 자신의 비판 방법을 개선하는 독립 개체를 목표로 한다. 타 개체의 실패 여부와 관계없이 자체 루프를 완결할 수 있어야 한다.

| 항목 | 현재 연구 기준 (2026-11-21) |
| --- | --- |
| 상태 | 연구 설계 작성 (Draft, 자율실행 미시작) |
| 고유 성장 목표 | 반례 발견·오탐 감소·재현율 향상 |
| 검증된 자기 개선 | 미입증 |
| 다음 실험 | 공개 주장 집합 고정 → 신규 반례 탐색 → 오탐·중복률 측정 |

[독립 정체성](docs/evolution/identity.md) · [기계 판독 상태](docs/evolution/independent-state.json) · [README 기억 실험 설계](docs/evolution/readme-memory-study.md) · [독립 기억 점검 스크립트](scripts/evolution_context.py)

첫 실행 연구 도구는 `python scripts/evolution_context.py check`와 `python scripts/evolution_context.py context`다. 이 코드는 로컬 기억을 읽고 검증할 뿐 LLM 호출이나 백그라운드 자율실행을 시작하지 않는다.


### 독립 자율진화 상세 개발 명세

- [독립 자율개선 루프 상세 계약 v2.0](docs/evolution/standalone-autonomy-spec-v2.md) — 내부 12개 모듈, 상태 기계, 증거 계약, 구현 단계
- [fenrir 전용 구현 계약](docs/evolution/fenrir-implementation-spec-v1.md) — 독자 목표, 평가 및 자체 개선 방법
- [23개 수락 테스트 계획](docs/evolution/acceptance-test-plan-v1.md) — 완료/차단 판정 조건
- [예약 자동개발 지속 프롬프트](docs/evolution/AUTOMATION_CONTINUITY_PROMPT.md) — 매 회차 이전 checkpoint 복구·중복 방지·한 가지 실제 개선

**현재 단계:** 개발 상세 설계 및 읽기 전용 검사 CI. 실제 무인 자기개선 루프와 숨겨진 평가 성과는 미검증이다.

### 3개체 통합 개발 예약 설계 (12분, GitHub Actions Draft)

- [통합 12분 실행 준비 워크플로](https://github.com/js775315672-spec/Harness-Ouroboros-MCP/blob/research/independent-evolution-readme-v1/.github/workflows/sael-three-agent-12min.yml): 매시 05·17·29·41·53분(UTC/KST 분 동일) 각 저장소를 **동시에 별도 읽기 전용 job으로 점검**하도록 제안함.
- **현재는 Draft PR에만 존재하여 12분 예약이 활성화되지 않음.** GitHub Actions `schedule`은 기본 브랜치에 포함된 후에만 작동하며 지연될 수 있음.
- 실제 자율 코드 개발은 각 저장소의 `evolution_runner.py`, 승인된 예산/리스/격리/독립 평가가 마련될 때까지 `NOT_IMPLEMENTED / NOT_RUN`이다.
- ChatGPT의 통합 개발 예약은 별도로 매시간 한 번 진행하며, 세 개체를 하나의 프롬프트 역할극으로 합쳐 독립 검증에 성공했다고 주장해서는 안 됨.
