# 작업 보드

## NOW

- [x] Codex 로컬 작업공간 설정
- [x] Python MVP 실행 확인
- [x] AI 회의 시스템 결과 저장
- [x] 고스틱 광고 생성 결과 저장
- [x] 네이버광고 샘플 CSV 분석
- [x] 승인 대기 파일 조회/승인 기록 CLI
- [x] 승인 파일 기반 실제 실행 dry-run 플래너
- [x] AI 직원 사무실 시뮬레이터 기본 웹앱
- [x] 시뮬레이터와 실제 CLI 작업 로그 연결
- [x] 승인 기록 기반 실행 전 최종 체크리스트
- [x] 네이버광고 dry-run 결과 CSV 저장
- [x] 승인 파일 상태를 시뮬레이터 상태판에 직접 표시
- [x] 작업별 소요 시간 기록
- [x] 텔레그램/n8n/Ollama dry-run 연결 준비 CLI
- [x] 외부 연동 승인 대기 파일 생성 기능
- [x] 텔레그램 dry-run 메시지 생성기
- [x] n8n webhook payload 샘플 생성기
- [x] Ollama 로컬 모델 어댑터 dry-run
- [x] 이미지 광고 템플릿 생성
- [x] Playwright dry-run 작성
- [x] 고양이 장난감 추천 웹앱 MVP
- [x] 추천 웹앱 질문 8~12개로 확장
- [x] 시뮬레이터에 추천 웹앱 상태 카드 추가
- [x] AI 회의 결과 기반 자동 실험 설계
- [x] 추천 웹앱 결과 공유 이미지 설계
- [x] 스마트스토어/네이버광고/SNS dry-run 데이터 스키마 설계
- [x] 스마트스토어 상품 데이터 자동 가져오기 dry-run
- [x] 네이버광고 API dry-run 어댑터
- [x] 인스타 업로드 승인형 dry-run 패키지

## NEXT

- [x] AI 직원 시뮬레이터에 실시간 작업 상태 연동 설계
- [x] 스마트스토어/네이버광고/인스타 dry-run 통합 대시보드
- [x] 추천 웹앱 결과 공유 이미지 실제 캔버스 미리보기
- [x] dry-run 대시보드와 AI 사무실 시뮬레이터 상호 링크
- [x] 캔버스 공유 이미지 PNG export dry-run 파일 저장
- [x] AI 사무실 평균 소요 시간 리포트
- [x] dry-run 대시보드 승인 파일 상세 보기
- [x] 승인 파일 위험도 점수화
- [x] 대시보드 실행 전 최종 체크리스트 바로가기 연결
- [x] 승인 파일 위험도 기반 실행 우선순위 큐
- [x] 승인 파일 중복/오래된 요청 정리 리포트
- [x] 스마트스토어 상품 데이터 실제 연동 전 필드 매핑 설계
- [x] 네이버광고 API 실제 연동 전 읽기/쓰기 권한 매트릭스
- [x] 인스타 업로드 승인형 자동화 전 자산 매니페스트
- [x] 4단계 Ollama 연결 dry-run 핸드셰이크
- [x] 5단계 Claude/Gemini API 연결 dry-run
- [x] 6단계 텔레그램 연결 dry-run
- [x] 7단계 Hermes AI 연결 dry-run
- [x] 8단계 AgentAU/n8n 오케스트레이션 연결 dry-run
- [x] AI 사무실 시뮬레이터 작업 큐에 위험도/승인 큐 표시
- [x] 4~8단계 연결 상태를 시뮬레이터 앱 상태판에 표시
- [x] Ollama 로컬 모델 목록 조회 승인형 dry-run
- [x] AI 사무실 시뮬레이터 채팅형 명령 실행 UI

## LATER

- [ ] 스마트스토어 상품 데이터 자동 가져오기
- [ ] 네이버광고 API 연결
- [ ] 인스타 업로드 승인형 자동화
- [ ] Ollama 모델 목록 승인 후 읽기 전용 조회 결과 표시
- [ ] AI 직원 시뮬레이터에 실시간 작업 상태 연동
- [x] 모델 라우터(Codex/Claude/Gemini/Ollama/이미지 AI) 단계 추가
- [x] 모델 라우터 결과를 AI 회의 시스템에 직접 연결
- [x] 자연어 명령 인터페이스(nl_command) + 위험 키워드 자동 차단
- [x] 시뮬레이터 채팅에 모델 라우터 1순위 카드 표시
- [x] 실행 준비 단계(marketing, image_templates)도 라우팅 정보 수신
- [x] 텔레그램 → nl_command → 라우터 → 회의 → 승인 end-to-end dry-run
- [x] local_viewer_server의 plan_chat_command를 nl_interpret로 통합
- [ ] 외부 dry-run(스마트스토어/네이버광고/인스타)도 라우팅 정보 수신
- [ ] 시뮬레이터 상태판에 최근 라우팅 결정 누적 표시
- [x] 직원 에이전트 보기 페이지(매트릭스 + 모델 오케스트레이션 + 시스템 진단 + 리포트 자동화)
- [x] 가상 사무실 페이지(DAY/TIME · 자율 운영 · 활동/산출물/대화록 3탭 · SVG 사무실 맵)
- [x] 수영 ↔ 가상 사무실 실데이터 파이프라인(real_data.json 폴링 + 실수치 기반 발언/알림)
- [x] Ollama 실연결(ollama_runtime + meeting --live + /api/ollama/status + UI LIVE 도트)
- [x] Claude(코딩) + OpenAI(디자인) 어댑터 + routed-run --live + env-check
- [x] usage_log + usage_caps(일일 ₩1k/월 ₩30k) + Gemini 어댑터 + env-check 사용량 표시
- [x] 사장님 원본 아키텍처 7단계 통합 파이프라인(boss-command) + 모델 매핑 원복
- [x] 멀티 에이전트 3라운드 토론 + 직원별 모델·페르소나·메모리 + CEO LLM 분배 + 표결
- [x] 비디오 AI 영입(매트릭스 카드 + 페르소나 + video_editing 모듈 + boss-command 통합)
- [x] Adobe Premiere Pro 직접 컨트롤(FCPXML + ExtendScript + EDL + --launch --approve 2중 가드)
- [x] 3개 시각화 페이지 localStorage 영속화 + 더블클릭 초기화 버튼
- [x] Hermes AI 실연결(텔레그램 봇 + 메모리 + rate limit + 가상사무실 inbox 폴링)
- [x] Nous Research Hermes Agent 도입 패키지 (WSL2 설치 가이드 + 우리 회사 스킬 5종)
- [ ] 사장님 Hermes 설치 완료 후: hermes_runtime deprecated + 가상 사무실 ↔ Hermes 세션 직결
- [x] CONNECT AI LAB 영상 3편 영감 적용 — 브레인 팩 + 캐릭터화 + 목표 시스템 + 엔터프라이즈 모드 + GitHub 동기화
