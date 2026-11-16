# 자연어로 하는 정책연구 실습: 학생 안내

구체적인 정책 질문과 여러 개의 자료 파일을 분석 AI에 제공하고, 비교 방법의 선택부터 표·그림·보고서 작성까지 진행하는 실습이다. 통계 명령어를 외우는 것보다 **어떤 정책 질문에, 어떤 자료로, 어디까지 답할 수 있는지 설명하는 것**이 목표다.

데이터는 모두 가상이다. 사람·지역·사업·관측값·문항을 새로 만들었으며 실제 응답자나 행정기록을 변형한 자료가 아니다. 실제 공공자료의 파일 구성과 변수 설명 관행을 참고했지만, 실습 결과를 실제 사업의 성과로 인용해서는 안 된다.

## 1. 자료 받기와 시작하기

데이터 ZIP은 수업에서 제공하는 **Dropbox 다운로드 링크**로 받는다. 아래 실습 문서와 자료 설명은 GitHub에서 읽을 수 있다.

<!-- 배포 담당자가 이 위치에 실제 Dropbox 학생용 데이터 링크를 추가한다. -->

- [정책연구 실습 문제집](PRACTICE_PROBLEMS_KO.md): 사례별 질문, 제공 자료, 시작 대화, 제출물.
- [자료 이용허락 — GitHub](https://github.com/cnucho/research-app-examples/blob/main/mcp-special-analysis-tools/policy-benchmark-v1/LICENSE-DATA.md): 합성자료와 새 문항·설명의 이용조건. 오프라인에서는 데이터 ZIP의 `user/LICENSE-DATA.md`를 연다.
- [구조 참고자료 목록 — GitHub](https://github.com/cnucho/research-app-examples/blob/main/mcp-special-analysis-tools/policy-benchmark-v1/sources.json): 실제 자료에서 참고한 범위와 출처. 오프라인에서는 선택한 세트의 `user/<사례>/<변형>/sources.json`과 `source_crosswalk.csv`를 확인한다.

압축파일의 데이터 경로는 `user/`로 시작한다. 먼저 사례 하나와 변형 하나를 고른다. 예를 들어 청년 교통비 사례의 첫 번째 변형은 `user/c02_youth_transport/v01/`이다. 다른 사례나 변형의 파일을 한 분석에 섞지 않는다.

한 폴더 안에서 다음 순서로 읽고 제공하면 된다.

1. `README.md`로 정책 질문, 대상, 관측 단위와 조사시점을 확인한다.
2. `codebook.csv` 또는 `codebook.json`, `datapackage.json`을 AI에 함께 제공한다.
3. 그 폴더의 `data/`에 있는 관측자료를 제공한다. 같은 표의 CSV와 SAV 중 한 형식을 선택한다.
4. [문제집](PRACTICE_PROBLEMS_KO.md)의 시작 대화를 사용하거나 자신의 정책 질문으로 바꿔 요청한다.
5. AI가 설명한 비교대안과 자료 처리 내용을 읽고, 모호한 부분을 자연어로 질문한다. 분석이 끝나면 실제 결과 파일을 내려받아 연다.

사용하는 앱이 ZIP을 직접 읽지 못하면 압축을 풀고 선택한 폴더의 파일을 첨부한다. 파일을 여러 번 나눠 올릴 때는 “자료를 모두 올릴 때까지 분석하지 말고 목록만 확인해 줘”라고 말할 수 있다. CSV와 SAV는 같은 관측자료를 담는 대체 형식이다. 둘을 서로 다른 표본으로 합치지 않는다.

## 2. 여섯 정책 사례와 열두 자료 세트

각 사례에 `v01`, `v02` 두 변형이 있다. 같은 주제와 파일 구조를 공유하면서 관측값이나 정책·표본의 조건이 다를 수 있다. **버전 번호가 난이도 순서나 효과 유무를 뜻하지 않는다.** 각 변형을 별도의 연구 자료로 검토한다. 어느 쪽이 더 다루기 쉬운지, 분석계획을 같게 적용해도 되는지는 자료와 설명서를 근거로 판단한다.

| 사례 | 연구 주제 | 주자료의 관측 단위·규모, 변형당 | 자료 폴더 |
| --- | --- | --- | --- |
| 01 | 무더위쉼터 야간·휴일 운영지원과 온열질환 신고 | 동일 48개 지역의 2017~2024년 자료, 지역·연도 384행 | `user/c01_heat_shelters/v01/`, `user/c01_heat_shelters/v02/` |
| 02 | 청년 교통·구직지원과 월 근로소득 | 40개 지역에서 4개 반기마다 새로 조사한 청년, 3,200행 | `user/c02_youth_transport/v01/`, `user/c02_youth_transport/v02/` |
| 03 | 디지털 재취업교육과 6개월 뒤 근로소득 | 기초조사·사업명부·추적조사의 동일한 성인 900명 | `user/c03_training/v01/`, `user/c03_training/v02/` |
| 04 | 주거환경 개선지원과 전력사용량 | 신청가구 1,200가구 및 사업별 공개 규칙 | `user/c04_home_insulation/v01/`, `user/c04_home_insulation/v02/` |
| 05 | 디지털 민원교육·자기효능감·과제 수행 | 사전조사부터 후속 평가까지 연결되는 신청자 800명 | `user/c05_digital_service/v01/`, `user/c05_digital_service/v02/` |
| 06 | 폭염 안전교육 시간·옥외근무·열부담 | 기초조사·교육기록·30일 후속관측의 동일한 작업자 900명 | `user/c06_heat_safety/v01/`, `user/c06_heat_safety/v02/` |

전체는 **12세트, 관측자료 표 38개**다. 각 표에 정본 `.csv`와 대응 `.sav`가 있어 **관측자료 CSV 38개, SAV 38개**가 제공된다. `codebook.csv`, `questionnaire.csv` 같은 설명용 CSV는 이 38개에 포함하지 않는다. 여러 파일이 같은 사람이나 지역을 담으므로 파일별 행수를 더해서 표본수로 보고하지 않는다.

## 3. 한 세트 안의 파일을 읽는 법

모든 세트는 다음 상대경로 규칙을 쓴다. `<사례>`와 `<변형>`에는 위 표의 폴더명을 넣는다.

| 경로 | 내용 | 실습에서 하는 일 |
| --- | --- | --- |
| `user/<사례>/<변형>/README.md` | 정책 질문, 조사 범위, 파일 간 관계 | 연구 대상과 자료 구조를 먼저 파악한다. |
| `user/<사례>/<변형>/data/` | 관측자료 CSV와 SAV | 실제 분석에 사용한다. |
| `user/<사례>/<변형>/codebook.csv` | 변수별 설명, 단위, 시점, 결측, 출처 | 스프레드시트나 텍스트로 확인한다. |
| `user/<사례>/<변형>/codebook.json` | 같은 변수 설명의 구조화된 형식 | AI와 분석 도구에 제공할 수 있다. |
| `user/<사례>/<변형>/datapackage.json` | 파일명, 열 자료형, 기본키, 결합 관계 | 파일 읽기와 결합 계획을 점검한다. |
| `user/<사례>/<변형>/questionnaire.csv` | 자체 작성 문항과 응답 형식 | 설문 문항이 무엇을 측정하는지 확인한다. |
| `user/<사례>/<변형>/value_labels.csv` | 범주형 변수의 값과 의미 | 숫자 코드의 뜻을 확인한다. |
| `user/<사례>/<변형>/source_crosswalk.csv` | 실제 자료와 개념·구조가 대응하는 범위 | 원자료 항목과 자체 설계를 구분한다. |
| `user/<사례>/<변형>/sources.json` | 구조를 참고한 자료의 출처 | 출처와 이용 범위를 기록한다. |

CSV는 UTF-8 BOM 형식이다. ID는 코드북의 자료형에 맞춰 읽고, 문자열의 앞자리 0을 보존한다. 빈 셀과 숫자 결측코드는 변수 설명을 확인한다. `0`, `-1` 같은 숫자를 모든 변수에서 일괄 결측 처리하지 않는다. 필요한 값 처리나 제외는 적용한 규칙과 바뀐 행수를 기록한다.

이 안내는 분석계획이나 결과의 정답표를 제공하지 않는다. 입력 폴더의 설명과 관측자료를 근거로 연구를 진행한다.

## 4. AI와 대화하며 진행하는 방식

처음부터 통계방법 이름을 지정할 필요는 없다. 정책의 대상, 개입, 알고 싶은 결과, 비교하고 싶은 상황을 말한다. 다음은 어느 사례에나 적용할 수 있는 시작 문장이다.

> 나는 [정책]이 [대상]의 [결과]를 얼마나 바꾸었는지 알고 싶다. 자료와 설명서를 올렸다. 먼저 파일과 변수의 뜻을 확인하고 가능한 비교대안과 각각 답할 수 있는 범위를 설명해 줘. 권하는 선택에는 이유를 붙이고, 추가로 알아야 할 내용만 질문해 줘. 필요한 파일 결합이나 새 변수 계산은 근거와 확인 결과를 남겨 줘. 분석 후에는 정책 담당자용 설명과 전문가가 확인할 표·그림·기록을 함께 만들어 줘.

판단과 설명은 AI가 맡고, 수치 계산·자료 처리·저장·재현성 확인은 실행한 코드로 남기도록 요청한다. 학생은 모든 옵션을 직접 정할 필요가 없지만, 연구 대상과 비교의 의미를 자신의 말로 설명할 수 있어야 한다.

| 진행 중 상황 | 사용할 수 있는 후속 질문 |
| --- | --- |
| 선택 이유가 어렵다 | “다른 선택과 비교해서 이 대안을 권한 이유를 쉬운 말로 설명해 줘.” |
| 파일을 합쳤다 | “무슨 키로 합쳤고, 합치기 전후 행수와 연결되지 않은 기록은 어떤지 보여 줘.” |
| 새 변수를 만들었다 | “정의와 단위, 계산식, 원자료와 대조한 확인 기록을 보여 줘.” |
| 결과가 나왔다 | “이 수치가 누구에게, 어느 기간에 대한 답인지 설명해 줘.” |
| 결과의 확실성이 궁금하다 | “효과 크기의 불확실성과 해석에 필요한 조건을 구분해서 설명해 줘.” |
| 보고서를 받았다 | “요약과 상세 표가 같은 실행 결과인지 확인하고 내려받을 수 있게 해 줘.” |
| 대화를 나중에 이어 간다 | “이 연구를 다시 열 때 사용할 식별정보를 알려 주고, 계획과 결과를 저장해 줘.” |

사용하는 환경에서 실행할 수 없는 작업이 있으면 무엇이 미완료인지 기록한다. 출력되지 않은 계산이나 검증을 수행한 것으로 적지 않는다.

## 5. 공통 제출물

수업에서 별도 분량을 지정하지 않으면 다음 묶음으로 제출한다.

1. **정책 메모 1~2쪽.** 연구질문, 대상과 기간, 가장 중요한 수치와 불확실성, 정책적으로 말할 수 있는 범위, 추가로 필요한 정보. 합성자료 실습임을 첫 부분에 표시한다.
2. **전문가용 부록.** 비교대안과 선택 이유, 최종 분석계획, 사용 변수와 단위, 표본 구성, 핵심 표·그림, 해석에 필요한 조건과 검토 결과.
3. **자료 처리 기록.** 입력 사례·변형·파일, 결합키와 관계, 처리 전후 행수, 결측·제외 규칙, 파생변수 정의와 확인 결과.
4. **재현 묶음.** 실제 실행에 사용한 코드 또는 실행계획, 도구가 제공하는 버전·시드·실행 식별정보, 결과 표 파일, 보고서와 그림. 내려받은 파일이 열리는지 확인한다.
5. **대화 검토 메모.** AI에게 물은 중요한 질문 두세 가지와 그 답이 계획 또는 해석에 미친 영향. 결과를 그대로 복사하는 대신 자신이 이해한 내용을 적는다.

모든 그림에는 제목, 축의 뜻과 단위, 대상과 기간을 붙인다. 표에는 표본수, 비교 방향, 추정치의 단위와 구간의 의미를 표시한다. 쉬운 설명과 전문가용 부록은 같은 결과를 표현해야 한다.

## 6. 두 변형으로 확장하는 과제

한 변형을 마친 뒤 다른 변형을 **새 작업**으로 분석한다. 시작할 때 이전 변형의 분석 결과를 복사하지 말고 새 파일의 설명과 관측자료부터 확인한다. 이후 두 작업의 질문, 표본, 계획, 자료 처리, 결과, 해석 범위를 비교한다. 숫자가 달라졌다는 관찰에 그치지 않고 무엇을 비교했는지 설명한다.

같은 사례의 `v01`과 `v02`를 추가 조사시점이나 추가 표본처럼 이어 붙이지 않는다. 여러 파일을 합치는 과제는 각 변형 폴더 안에서 파일의 관측 단위와 키를 근거로 진행한다.

## 7. 인용과 공유

표기 예: cnucho, *Research App Examples: Synthetic Policy Benchmarks*, `policy-benchmark-v1`, `c02_youth_transport/v01`, 합성자료 실습. 사용한 사례와 변형을 실제 작업에 맞게 바꾼다.

합성자료와 새 문항·설명은 [CC BY 4.0](https://github.com/cnucho/research-app-examples/blob/main/mcp-special-analysis-tools/policy-benchmark-v1/LICENSE-DATA.md)에 따라 이용할 수 있다. 오프라인에서는 데이터 ZIP의 `user/LICENSE-DATA.md`에서 상세 조건을 확인한다. 수정본을 공유할 때는 원래 출처와 변경 사실을 적는다. 원자료의 ID와 설명서를 보존한 원본을 별도로 두고 작업한다.

## 부록. 관측자료 38쌍의 정확한 경로

아래 경로는 학생용 데이터 ZIP 내부 기준이다. 같은 행의 CSV와 SAV는 같은 표의 대체 형식이다. 각 행수는 **해당 파일의 행수**이며 결합 후 표본수를 뜻하지 않는다.

| CSV 경로 | SAV 경로 | 행수 |
| --- | --- | ---: |
| `user/c01_heat_shelters/v01/data/annual_outcomes.csv` | `user/c01_heat_shelters/v01/data/annual_outcomes.sav` | 384 |
| `user/c01_heat_shelters/v01/data/facility_inventory.csv` | `user/c01_heat_shelters/v01/data/facility_inventory.sav` | 213 |
| `user/c01_heat_shelters/v01/data/policy_schedule.csv` | `user/c01_heat_shelters/v01/data/policy_schedule.sav` | 48 |
| `user/c01_heat_shelters/v02/data/annual_outcomes.csv` | `user/c01_heat_shelters/v02/data/annual_outcomes.sav` | 384 |
| `user/c01_heat_shelters/v02/data/facility_inventory.csv` | `user/c01_heat_shelters/v02/data/facility_inventory.sav` | 214 |
| `user/c01_heat_shelters/v02/data/policy_schedule.csv` | `user/c01_heat_shelters/v02/data/policy_schedule.sav` | 48 |
| `user/c02_youth_transport/v01/data/policy_schedule.csv` | `user/c02_youth_transport/v01/data/policy_schedule.sav` | 40 |
| `user/c02_youth_transport/v01/data/survey_rows.csv` | `user/c02_youth_transport/v01/data/survey_rows.sav` | 3,200 |
| `user/c02_youth_transport/v02/data/policy_schedule.csv` | `user/c02_youth_transport/v02/data/policy_schedule.sav` | 40 |
| `user/c02_youth_transport/v02/data/survey_rows.csv` | `user/c02_youth_transport/v02/data/survey_rows.sav` | 3,200 |
| `user/c03_training/v01/data/baseline.csv` | `user/c03_training/v01/data/baseline.sav` | 900 |
| `user/c03_training/v01/data/followup_6m.csv` | `user/c03_training/v01/data/followup_6m.sav` | 900 |
| `user/c03_training/v01/data/program_register.csv` | `user/c03_training/v01/data/program_register.sav` | 900 |
| `user/c03_training/v02/data/baseline.csv` | `user/c03_training/v02/data/baseline.sav` | 900 |
| `user/c03_training/v02/data/followup_6m.csv` | `user/c03_training/v02/data/followup_6m.sav` | 900 |
| `user/c03_training/v02/data/program_register.csv` | `user/c03_training/v02/data/program_register.sav` | 900 |
| `user/c04_home_insulation/v01/data/applications.csv` | `user/c04_home_insulation/v01/data/applications.sav` | 1,200 |
| `user/c04_home_insulation/v01/data/awards.csv` | `user/c04_home_insulation/v01/data/awards.sav` | 1,200 |
| `user/c04_home_insulation/v01/data/bills.csv` | `user/c04_home_insulation/v01/data/bills.sav` | 1,200 |
| `user/c04_home_insulation/v01/data/policy_rules.csv` | `user/c04_home_insulation/v01/data/policy_rules.sav` | 2 |
| `user/c04_home_insulation/v02/data/applications.csv` | `user/c04_home_insulation/v02/data/applications.sav` | 1,200 |
| `user/c04_home_insulation/v02/data/awards.csv` | `user/c04_home_insulation/v02/data/awards.sav` | 1,200 |
| `user/c04_home_insulation/v02/data/bills.csv` | `user/c04_home_insulation/v02/data/bills.sav` | 1,200 |
| `user/c04_home_insulation/v02/data/policy_rules.csv` | `user/c04_home_insulation/v02/data/policy_rules.sav` | 2 |
| `user/c05_digital_service/v01/data/assignments.csv` | `user/c05_digital_service/v01/data/assignments.sav` | 800 |
| `user/c05_digital_service/v01/data/baseline.csv` | `user/c05_digital_service/v01/data/baseline.sav` | 800 |
| `user/c05_digital_service/v01/data/mediator_survey.csv` | `user/c05_digital_service/v01/data/mediator_survey.sav` | 800 |
| `user/c05_digital_service/v01/data/performance.csv` | `user/c05_digital_service/v01/data/performance.sav` | 800 |
| `user/c05_digital_service/v02/data/assignments.csv` | `user/c05_digital_service/v02/data/assignments.sav` | 800 |
| `user/c05_digital_service/v02/data/baseline.csv` | `user/c05_digital_service/v02/data/baseline.sav` | 800 |
| `user/c05_digital_service/v02/data/mediator_survey.csv` | `user/c05_digital_service/v02/data/mediator_survey.sav` | 800 |
| `user/c05_digital_service/v02/data/performance.csv` | `user/c05_digital_service/v02/data/performance.sav` | 800 |
| `user/c06_heat_safety/v01/data/baseline.csv` | `user/c06_heat_safety/v01/data/baseline.sav` | 900 |
| `user/c06_heat_safety/v01/data/followup.csv` | `user/c06_heat_safety/v01/data/followup.sav` | 900 |
| `user/c06_heat_safety/v01/data/training.csv` | `user/c06_heat_safety/v01/data/training.sav` | 900 |
| `user/c06_heat_safety/v02/data/baseline.csv` | `user/c06_heat_safety/v02/data/baseline.sav` | 900 |
| `user/c06_heat_safety/v02/data/followup.csv` | `user/c06_heat_safety/v02/data/followup.sav` | 900 |
| `user/c06_heat_safety/v02/data/training.csv` | `user/c06_heat_safety/v02/data/training.sav` | 900 |
