1. 스플릿 팟(Split Pot) 대응 (Critical)
winner 필드를 String에서 List[String]으로 변경해야 합니다.

이유: 메인 이벤트 후반부나 캐시 게임에서는 찹(Chop/Split)이 빈번합니다.

변경: winner: Optional[str] → winners: List[str]

2. 오디오 트랙 및 타임코드 기준점 추가 (MAM 호환성)
MAM에서 편집기로 내보낼 때(Export to Premiere), 오디오 채널 매핑과 원본 타임코드가 필수적입니다.

변경 (Asset Level):

start_timecode: 영상 파일의 시작 타임코드 (예: 01:00:00:00) - 이게 없으면 초 단위 시간을 타임코드로 역산할 때 오차가 발생합니다.

audio_layout: (선택) 예: {"ch1": "Program L", "ch2": "Program R", "ch3": "Caster Clean"}

3. 카드 데이터의 구조화 (검색 고도화)
hand_matchup ("AA vs KK")은 사람에게는 좋지만, 시스템 검색("Ace를 들고 있는 핸드 찾기")에는 불리합니다. 가벼운 구조화를 제안합니다.

추가 (Segment Level):

hole_cards: [{"player": "Daniel", "cards": ["Ah", "Ad"]}, ...] 형태로 저장하면 나중에 "A가 포함된 모든 핸드" 검색이 가능해집니다. (OHH만큼 복잡하지 않게 핵심만 저장)

4. 버전 관리 (Concurrency)
여러 명이 메타데이터를 수정하거나, Converter가 재실행될 때를 대비해야 합니다.

추가 (Segment Level):

last_modified_at: datetime

version: int (수정될 때마다 +1)

🛠️ Revised Schema (수정된 스키마 예시)
위 제안을 반영하여 수정한 Segment Entity와 Asset Entity의 핵심 부분입니다.

3.1 Level 1: Asset Entity (Revised)
Python

class Asset(BaseModel):
    # ... 기존 필드 ...

    # [New] 편집 및 싱크를 위한 필수 기술 정보
    tc_start: str = Field(default="00:00:00:00", description="Source start timecode")
    audio_channels: Optional[dict[str, str]] = None # {"1": "PGM_L", "2": "PGM_R"}
3.2 Level 2: Segment Entity (Revised)
Python

class Segment(BaseModel):
    # ... 기존 필드 ...

    # [Modified] 스플릿 팟 대응
    winners: List[str] = Field(default_factory=list) 

    # [New] 검색을 위한 최소한의 카드 구조화 (선택 사항)
    # 복잡한 OHH 대신, 검색 인덱싱용 단순 리스트
    key_cards: Optional[List[str]] = Field(None, description="['Ah', 'Ad', 'Ks']")

    # [New] 데이터 관리
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    data_version: int = 1
    
    # [Validation Logic]
    @property
    def is_split_pot(self) -> bool:
        return len(self.winners) > 1
📊 업데이트된 JSON Golden Record (부분)
JSON

{
  "segment": {
    "segment_uuid": "...",
    "winners": ["Daniel Negreanu", "Phil Hellmuth"], // 스플릿 팟 예시
    "hand_matchup": "AKo vs AKs",
    
    "situation_flags": {
       "is_chop": true, // 스플릿 여부 플래그 추가 권장
       "is_cooler": false
    },
    
    "asset_metadata_ref": {
       "tc_start": "10:00:00:00" // 이 값이 있어야 정확한 편집점 계산 가능
    }
  }
}