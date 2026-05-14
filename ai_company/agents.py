from dataclasses import dataclass

@dataclass(frozen=True)
class AgentRole:
    name: str
    mission: str
    perspective: str

AGENTS = [
    AgentRole(
        name="데이터 AI",
        mission="숫자로 문제 원인을 찾는다.",
        perspective="CTR, CPC, 전환율, ROAS, 매출, 광고비 관점"
    ),
    AgentRole(
        name="고객심리 AI",
        mission="집사가 왜 구매하거나 이탈하는지 분석한다.",
        perspective="고민, 감정, 공감, 구매동기 관점"
    ),
    AgentRole(
        name="SNS AI",
        mission="인스타/릴스/쇼츠에서 반응이 나오는 포맷을 제안한다.",
        perspective="후킹 2초, 자막, 썸네일, 공유성 관점"
    ),
    AgentRole(
        name="상품 AI",
        mission="상품의 장점, 옵션, 세트, 리필 전략을 제안한다.",
        perspective="고양이 성향, 재구매, 번들, 상세페이지 관점"
    ),
    AgentRole(
        name="네이버광고 AI",
        mission="광고비 효율과 키워드 전략을 개선한다.",
        perspective="키워드, 입찰가, ROAS, 낭비 클릭 관점"
    ),
    AgentRole(
        name="검수 AI",
        mission="위험한 표현과 실행 리스크를 막는다.",
        perspective="과장광고, 저작권, 개인정보, 실제 실행 승인 관점"
    ),
]
