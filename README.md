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

