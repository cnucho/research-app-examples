# 정책 데이터 분석: 문제 발견·예측·원인과 효과

핵심 개념과 사례논문 | 별도 실습자료와 독립적으로 읽는 강의자료

## 1. 문제 발견: 비교로 차이를 드러낸다

누가, 어디서, 언제 다른가? 평균 뒤의 분포와 자료의 빈틈까지 본다.

정책 데이터 분석은 **어디가 문제인가 → 앞으로 어떻게 될까 → 왜 발생하며 무엇이 효과가 있는가**를 묻는다. 문제 발견의 출발점은 비교다. 차이를 찾은 뒤, 목표·권리·형평성 등의 기준으로 정책적 의미를 판단한다.

| 비교할 것 | 간단한 기법 | 정책에서 묻는 질문 |
| --- | --- | --- |
| 사람·집단·지역 | 평균·비율 비교, 박스플롯 | 어느 집단의 대기시간이 더 길고 불안정한가? |
| 시간 | 추세·증감률·변곡점 살펴보기 | 청년의 구직 중단 비율이 계속 높아지는가? |
| 비슷한 특성의 유형 | 교차분류, 군집분석 | 주거비 부담형·이동 불편형·복합 취약형으로 나뉘는가? |
| 목표·기준 | 목표 대비 격차, 기준 초과 비율 | 서비스 처리기한을 넘긴 사람은 얼마나 되는가? |

**유형화**는 비슷한 대상을 묶어 집단의 차이를 잘 보이게 한다. 군집은 선택한 변수·척도·집단 수에 따라 달라지며, 그 자체가 원인이나 객관적으로 정해진 계층은 아니다. 위 유형명은 설명용 가상 예시다.

### 평균이 같아도 경험은 다르다

**수업용 가상자료.** 두 지역 모두 평균 11일이지만, 중앙값은 A 11일·B 7일이다. B에는 매우 오래 기다린 사례가 있다. 상자는 가운데 50%, 굵은 선은 중앙값, 별도 점은 긴 처리시간 사례를 보여준다.

### 사례논문: 차이와 사각지대를 발견하기

**경제적 기회의 격차 [1]** Chetty 외(2020)는 부모의 소득 수준에 따른 자녀의 성인 소득을 인종·성별·지역별로 비교했다. 이 연구에서 수업에 가져올 부분은 **비교 조건과 집단을 나누면 가려진 격차가 드러난다**는 점이다. 격차의 발견과 원인 규명은 구별한다.

**민원이 적으면 문제가 적은가? [2]** Kontokosta·Hong(2021)은 캔자스시티의 311 민원과 주민 설문·지역 상태를 함께 살폈다. 일부 취약지역의 신고가 필요를 충분히 반영하지 못했다. **민원 건수는 문제의 크기와 동일하지 않다.**

읽는 순서: 비교 기준 → 평균과 분포 → 시간 변화 → 자료에서 빠진 사람. 건수와 비율을 구분하고, 같은 정의·대상·기간으로 비교한다.

## 2. 예측: 근거와 조건을 함께 말한다

미래를 한 숫자로 확정하기보다, 전망·시나리오·조짐을 구분한다.

예측은 **“어떤 조건에서 무엇이 일어날 가능성이 있는가”**를 따진다. 아래 접근은 함께 사용할 수 있다. 특히 디지털 트윈은 하나의 예측 기법이라기보다 현실 자료와 여러 모형을 연결하는 체계다.

### 델파이: 전문가의 판단과 근거

**전문가에게 반복해서 묻고, 응답과 근거를 피드백한다.** Tapio(2003)는 핀란드 교통정책에서 경제·교통량·배출의 가능한 미래와 바람직한 미래를 물어 여러 시나리오를 구성했다. 이 방식은 의견 차이도 보존했다. 전문가 선정·질문 방식에 영향을 받으며, 합의가 정확성을 보장하지 않는다. [3]

### 통계·기계학습: 관찰된 패턴

**과거 자료에서 이후 결과와 연결되는 패턴을 학습한다.** 회귀·시계열 모형, 랜덤포리스트·부스팅 등이 쓰인다. Kleinberg 외(2018)는 재판 전 석방 판단과 위험 예측을 연구했다. 석방된 사람의 결과만 관찰되는 선택 문제를 함께 다뤘다. 과거와 미래의 조건이 달라지면 성능도 달라진다. [4]

### 시뮬레이션: 작동 규칙과 가정

**사람·자원·제도의 작동 규칙을 정하고 대안을 계산한다.** 미시모의실험·행위자 기반 모형·시스템다이내믹스 등이 있다. ITF(2015)는 리스본에서 공유 자율주행차 시나리오를 모의실험했다. 필요한 차량 수가 줄어도 공차 이동 등으로 총 주행거리는 늘 수 있다. 이는 가정 아래의 계산이다. [5]

### 디지털 트윈: 현실 자료와 모형의 연결

**도시·시설의 자료를 모형과 연결해 상태와 대안을 살핀다.** Dembski 외(2020)는 독일 헤렌베르크의 3차원 도시·교통·바람·시민 자료를 연결한 프로토타입을 제시했다. 현실과의 연결·보정·검증이 중요하며, 정교한 화면이 사람의 미래 행동까지 보장하지는 않는다. [6]

### 잡음 속의 조짐, 그리고 달라지는 사람

“나뭇잎 하나가 떨어졌다”는 것은 계절 변화의 단서일 수 있지만 바람이나 손상 때문일 수도 있다. **약한 신호 탐색**은 작은 변화·현장 관찰·뉴스·전문가 판단을 모아 추가 확인할 대상을 찾는 일이다. 드문 단서를 놓치거나 잡음을 신호로 오인할 수 있다. Hiltunen(2008)은 신호·현상·해석의 구별을 제안했다. [7]

예측이 의사결정에 쓰이면 사람의 행동과 다음 자료가 달라질 수 있다. Perdomo 외(2020)의 **수행적 예측**은 이 문제를 다룬다. 따라서 예측은 조건·오차·갱신 시점을 함께 제시한다. **확정적 예언의 어려움이 조건부 예측의 무용함을 뜻하지는 않는다.** [8]

같은 청년고용 문제라도 “실업률 전망”, “지원제도 변경 시나리오”, “새로운 구직행태의 조짐”은 서로 다른 질문이다.

## 3. 원인과 효과: 설득력 있는 비교를 만든다

상관관계의 발견에서 한 걸음 더 나아가, 다른 설명을 얼마나 배제했는지 묻는다.

원인진단은 **무엇이 결과를 바꾸는가**, 효과분석은 **정책을 했을 때와 하지 않았을 때 얼마나 달라지는가**를 묻는다. 공통 과제는 관찰되지 않은 다른 상태, 즉 **반사실**에 설득력 있는 비교 근거를 만드는 것이다.

| 방법 | 비교하는 방식 | 해석을 위한 핵심 조건 |
| --- | --- | --- |
| 회귀·ANCOVA | 관측한 공변량을 조정한 집단 차이 | 적절한 모형·비교 가능성, 관련 교란의 조정 |
| 매칭·PSM | 처치 전 특성이 비슷한 대상을 비교 | 겹치는 대상이 있어야 함; 미관측 교란은 남을 수 있음 |
| 고정효과(FE) | 같은 대상의 여러 시점을 비교 | 일정한 모형 조건에서 시간 불변 요인 제거; 시간 가변 교란은 남음 [13] |
| DID | 처치·비교집단의 전후 변화 차이 | 정책이 없었으면 추세가 평행했을 것이라는 가정 |
| RD | 정책 배정 기준선 바로 양옆을 비교 | 경계 부근의 비교 가능성; 효과는 경계 주변에 해당 |

연구설계와 계산 방법은 결합할 수 있다. 예컨대 무작위실험에서도 회귀로 사전 차이를 조정할 수 있다. DID는 여러 시점과 반복횡단면에도 가능하며, 자료 구조에 맞는 비교 조건을 확인한다.

### 사례논문: 무엇을 누구와 비교했는가?

**DID [9]** Card·Krueger(1994): 뉴저지·펜실베이니아 패스트푸드점의 최저임금 인상 전후 고용 비교.

**PSM [10]** Dehejia·Wahba(2002): 취업훈련 자료에서 관측 특성이 비슷한 비실험 비교대상을 구성.

**RD [11]** Jacob·Lefgren(2004): 시카고의 성적 기준과 여름학교·진급 규칙 주변에서 교육 성과 비교.

### 매개와 조절: 경로와 조건은 다르다

**매개: 어떤 경로로?**

가상 예: 취업상담 → 구직 자신감 → 취업.

Imai 외(2011)는 뉴스 메시지·불안·이민 태도의 매개 경로 등을 재분석했다. 처치의 무작위배정만으로 매개 경로까지 입증되지는 않는다. [12]

**조절: 누구에게·언제 더 큰가?**

가상 예: 취업상담의 효과가 기존 경력에 따라 다른가?

집단별 효과의 차이를 직접 비교한다. 한 집단에서만 유의하다는 이유로 집단 간 효과가 다르다고 단정하지 않는다.

“영향요인 연구”에서 회귀계수나 변수 중요도가 크다는 것만으로 원인을 찾았다고 할 수 없다. 또한 통계의 “요인분석”은 여러 문항의 구조를 요약하는 방법으로, 인과적 원인을 찾는 것과 다르다.

## 4. 참고문헌과 원문 링크

본문의 대괄호 번호와 대응한다. 제목을 누르면 논문 또는 원저자·기관 페이지가 열린다.

처음 읽을 자료: **[2] 민원 자료의 편향**, **[3] 델파이 시나리오**, **[5] 교통 시뮬레이션**, **[9] DID 비교 논리**. 논문 전체를 가르치기보다 질문·자료·비교 방식·해석의 한계를 읽는다.

**[1]** [Chetty, Raj, Nathaniel Hendren, Maggie R. Jones, and Sonya R. Porter. 2020. "Race and Economic Opportunity in the United States: An Intergenerational Perspective." Quarterly Journal of Economics 135(2): 711–783.](https://opportunityinsights.org/paper/race/)

**[2]** [Kontokosta, Constantine E., and Boyeong Hong. 2021. "Bias in Smart City Governance: How Socio-Spatial Disparities in 311 Complaint Behavior Impact the Fairness of Data-Driven Decisions." Sustainable Cities and Society 64: 102503.](https://marroninstitute.nyu.edu/papers/bias-in-smart-city-governance-how-socio-spatial-disparities-in-311-complaint-behavior-impact-the-fairness-of-data-driven-decisions)

**[3]** [Tapio, Petri. 2003. "Disaggregative Policy Delphi: Using Cluster Analysis as a Tool for Systematic Scenario Formation." Technological Forecasting and Social Change 70(1): 83–101.](https://www.sciencedirect.com/science/article/abs/pii/S0040162501001779)

**[4]** [Kleinberg, Jon, Himabindu Lakkaraju, Jure Leskovec, Jens Ludwig, and Sendhil Mullainathan. 2018. "Human Decisions and Machine Predictions." Quarterly Journal of Economics 133(1): 237–293.](https://cs.stanford.edu/~jure/pubs/bail-qje17.pdf)

**[5]** [International Transport Forum. 2015. Urban Mobility System Upgrade: How Shared Self-Driving Cars Could Change City Traffic. International Transport Forum Policy Papers, No. 6. Paris: OECD Publishing.](https://www.oecd.org/en/publications/urban-mobility-system-upgrade_5jlwvzdk29g5-en.html)

**[6]** [Dembski, Fabian, Uwe Wössner, Mike Letzgus, Michael Ruddat, and Claudia Yamu. 2020. "Urban Digital Twins for Smart Cities and Citizens: The Case Study of Herrenberg, Germany." Sustainability 12(6): 2307.](https://www.mdpi.com/2071-1050/12/6/2307)

**[7]** [Hiltunen, Elina. 2008. "The Future Sign and Its Three Dimensions." Futures 40(3): 247–260.](https://www.sciencedirect.com/science/article/pii/S0016328707001085)

**[8]** [Perdomo, Juan, Tijana Zrnic, Celestine Mendler-Dünner, and Moritz Hardt. 2020. "Performative Prediction." ICML, Proceedings of Machine Learning Research 119: 7599–7609.](https://proceedings.mlr.press/v119/perdomo20a.html)

**[9]** [Card, David, and Alan B. Krueger. 1994. "Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania." American Economic Review 84(4): 772–793.](https://davidcard.berkeley.edu/papers/min-wage-ff-nj.pdf)

**[10]** [Dehejia, Rajeev H., and Sadek Wahba. 2002. "Propensity Score-Matching Methods for Nonexperimental Causal Studies." Review of Economics and Statistics 84(1): 151–161.](https://users.nber.org/~rdehejia/papers/matching.pdf)

**[11]** [Jacob, Brian A., and Lars Lefgren. 2004. "Remedial Education and Student Achievement: A Regression-Discontinuity Analysis." Review of Economics and Statistics 86(1): 226–244.](https://edpolicy.umich.edu/research/epi-working-papers/remedial-education-and-student-achievement-regression-discontinuity)

**[12]** [Imai, Kosuke, Luke Keele, Dustin Tingley, and Teppei Yamamoto. 2011. "Unpacking the Black Box of Causality: Learning about Causal Mechanisms from Experimental and Observational Studies." American Political Science Review 105(4): 765–789.](https://imai.sites.fas.harvard.edu/research/files/mediationP.pdf)

**[13]** [Imai, Kosuke, and In Song Kim. 2019. "When Should We Use Unit Fixed Effects Regression Models for Causal Inference with Longitudinal Data?" American Journal of Political Science 63(2): 467–490.](https://imai.fas.harvard.edu/research/fematch/)

**읽을 때 구분할 것** [1][2][4][9][10][11]은 실증자료를 다룬 연구, [3]은 델파이 방법·정책 사례, [5]는 조건부 시뮬레이션 보고서, [6]은 디지털 트윈 구현 사례, [7][8][12][13]은 개념·방법론 및 적용 연구다. 본문의 박스플롯과 별도 표시된 정책 예시는 수업용 가상 사례이며, 논문의 수치를 재현한 그림이 아니다.
