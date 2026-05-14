# 실행 준비 단계 라우팅 통합 보고서

## 1. 수행한 일

실행 준비 단계(marketing, image_templates)도 모델 라우터 결정을 받아
출력 머리에 라우팅 카드를 첨부하도록 확장했다.

```
사장님 → CEO 오케스트레이터 → 모델 라우터 → AI 회의 → 실행 준비 [← 이번 확장]
   ├─ 광고 패키지 (marketing.generate_ad_package)
   └─ 이미지 템플릿 (image_templates.build_image_templates)
```

회의/광고/이미지 어디서든 동일 라우터 정보가 보고서 머리에 표시되므로
사장님이 한눈에 "이 작업은 어느 모델이 1차 책임지는가"를 확인할 수 있다.

## 2. 생성/수정한 파일

- `ai_company/marketing.py`
  - `generate_ad_package(product_code, routing=None)` — routing 파라미터 추가
  - `generate_routed_ad_package(product_code)` — 라우터 자동 통과 편의 함수
  - 라우터 카드 헬퍼 `_routing_card()` 추가
- `ai_company/image_templates.py`
  - `build_image_templates(product_code, routing=None)` — routing 파라미터
  - 데이터 딕셔너리에 `routing` 키 자동 첨부
  - `write_image_templates(product_code, with_router=False)` — CLI 헬퍼
- `ai_company/main.py`
  - `ad --with-router` 플래그 추가
  - `image-templates --with-router` 플래그 추가
- `tests/test_smoke.py`
  - `test_ad_package` — 라우팅 미사용 시 카드 없음 검증
  - `test_ad_package_with_router` — 라우팅 카드 표시 검증
  - `test_image_templates` — 라우팅 미사용 시 routing 키 없음 검증
  - `test_image_templates_with_router` — 라우팅 카드 + data 검증

## 3. 사용 방법

```powershell
# 기존 동작 (라우팅 카드 없음)
python -m ai_company.main ad --product GOSTICK01
python -m ai_company.main image-templates --product GOSTICK01

# 라우터 통합 (카드 자동 첨부)
python -m ai_company.main ad --product GOSTICK01 --with-router
python -m ai_company.main image-templates --product GOSTICK01 --with-router
```

라우터 통합 시 보고서 머리에:

```markdown
## 모델 라우터 결정
- 1순위 모델: **이미지 AI (Stable Diffusion / Canva / PIL)** (광고 이미지, 썸네일, 시각 자산)
- 1순위 점수: 8
- 후순위: 없음
- dry-run: True / executed: False
```

## 4. 호환성

- 모든 변경은 Optional 파라미터로 추가됨 — 기존 호출 깨지지 않음
- `--with-router` 없이 호출하면 기존 출력과 100% 동일
- routing 미사용 시 data 딕셔너리에 `routing` 키 안 들어감

## 5. 다음 추천 작업

- 외부 dry-run(스마트스토어/네이버광고/인스타)도 라우팅 정보 수신
- 시뮬레이터 상태판에 최근 라우팅 결정 카드 누적 표시
- 실험 설계(experiment-plan)도 라우팅 통과

## 안전 확인

- 실제 API 호출 / 외부 발송 — 없음
- 모든 처리는 D:\AI_COMPANY 내부 파일 생성으로만
- 라우팅 결정은 dry_run=True / executed=False 유지
