# 정책효과 분석 연습과제: 학생 안내

이 과제는 **정책 담당자의 질문에 자료를 근거로 답하는 연습**이다. 제시된 정책문제를 읽고, 가상데이터와 설명서를 검토하고, 가능한 비교전략을 선택한 다음, 계산 결과와 한계를 정책 메모로 제출한다.

**이 압축파일만 있으면 과제를 수행할 수 있다.** 특정 앱의 가입·접속·설치나 AI 사용은 과제 요건이 아니다. R, Stata, SPSS, Python 또는 필요한 분석과 재현 기록을 제공할 수 있는 다른 도구를 선택한다. 평가에는 도구 이름보다 질문과 자료의 이해, 비교의 타당성, 계산의 정확성, 설명과 재현 가능성이 반영된다.

자료는 모두 가상이다. 사람·지역·사업·관측값·문항을 새로 만들었으며 실제 응답자나 행정기록을 변형한 자료가 아니다. 실제 공공자료의 파일 구성과 변수 설명 관행을 참고했지만, 여기서 계산한 값을 현실의 정책 성과로 인용해서는 안 된다.

## 1. 바로 시작하기

압축을 풀면 안내문, 문제집, 보고서 틀, 선택 도구 안내, 데이터 폴더가 함께 나온다. 수업에서 사례와 변형을 지정했다면 그 조합을 사용하고, 지정하지 않았다면 여섯 사례 중 하나와 `v01` 또는 `v02` 하나를 선택한다.

1. [정책효과 분석 문제집](PRACTICE_PROBLEMS_KO.md)에서 정책 담당자의 의사결정 상황과 수행할 과제를 읽는다.
2. 선택한 자료 폴더의 `README.md`, `codebook.csv`, `datapackage.json`으로 대상, 관측 단위, 시점, 변수, 파일 간 관계를 확인한다.
3. 결과를 계산하기 전에 정책질문, 비교대상, 분석할 결과변수, 가능한 분석전략과 필요한 가정을 간단히 적는다.
4. `data/`의 CSV 또는 SAV를 읽어 자료를 준비하고, 결합·결측 처리·새 변수 계산의 근거와 확인 결과를 남긴다.
5. 선택한 전략으로 분석하고, 필요한 진단과 민감도 점검을 수행한다. 처음 계획을 바꿨다면 이유를 기록한다.
6. [제출 양식](SUBMISSION_TEMPLATE_KO.md)을 참고해 정책 메모, 상세 부록, 표·그림, 재현자료를 정리한다. 다른 사람이 파일을 열고 계산을 따라갈 수 있는지 확인한다.

PDF 과제집 `policy-effect-exercises-ko.pdf`에도 안내·문제·제출 양식·선택 도구 안내가 들어 있다. 텍스트 문서는 오프라인에서도 읽을 수 있고, 온라인 문서가 바뀌어도 내려받은 ZIP의 문서와 데이터로 같은 과제를 계속할 수 있다. 데이터는 `user/` 아래에 있으며, 압축파일을 통째로 어떤 서비스에 올릴 필요는 없다.

## 2. 학습 목표와 수행 범위

실습을 마치면 다음을 설명할 수 있어야 한다.

- 정책이 누구의 어떤 결과를 어느 기간에 바꾸었는지 질문을 구체화한다.
- 한 행이 무엇을 뜻하는지, 같은 사람이나 지역을 반복해서 관측했는지, 정책 참여나 배정이 어떻게 이루어졌는지 파악한다.
- 단순한 집단 차이와 정책의 영향으로 해석할 수 있는 비교를 구분하고, 분석전략의 가정과 한계를 설명한다.
- 자료 결합과 변수 계산이 분석대상과 결과에 미친 영향을 확인한다.
- 효과의 크기·단위·불확실성을 표와 그림으로 제시하고, 정책 담당자가 이해할 수 있는 말로 답한다.
- 계산을 다시 실행하거나 동일한 옵션으로 재현할 수 있는 기록을 남긴다.

기술통계와 기초적인 회귀 결과를 읽는 수준에서 시작할 수 있다. 세부 분석방법을 아직 배우지 않았다면 먼저 질문·자료 구조·비교 설계안을 작성하고, 수업에서 배운 방법이나 지도받은 대안을 적용한다. 이 과제집은 특정 명령어를 따라 누르는 매뉴얼이나 분석방법의 정답표가 아니다.

기본 과제는 **한 사례·한 변형의 분석**이다. 사례별 필수 작업을 마친 뒤의 다른 변형 재분석, 복수 도구의 결과 대조, 추가 추정전략의 비교는 확장 과제로 수행할 수 있다. 사례 03에 명시된 두 비교전략의 실행은 해당 사례의 필수 작업이다. 확장 과제는 수업에서 지정하지 않는 한 필수 점수 요건이 아니다.

## 3. 여섯 정책 사례와 열두 자료 세트

각 사례에 `v01`, `v02` 두 변형이 있다. 같은 주제와 파일 구조를 공유하면서 관측값이나 정책·표본의 조건이 다를 수 있다. **변형 번호가 난이도 순서나 효과 유무를 뜻하지 않는다.** 변형마다 자료 설명과 관측값을 새로 검토한다.

| 사례 | 정책 담당자의 질문 | 주자료의 관측 단위·규모, 변형당 | 자료 폴더 |
| --- | --- | --- | --- |
| 01 | 무더위쉼터 야간·휴일 운영지원 뒤 온열질환 신고가 달라졌는가? | 동일 48개 지역의 2017~2024년 자료, 지역·연도 384행 | `user/c01_heat_shelters/v01/`, `user/c01_heat_shelters/v02/` |
| 02 | 청년 교통·구직지원이 지역 청년 전체의 월 근로소득을 바꾸었는가? | 40개 지역에서 4개 반기마다 새로 조사한 청년, 3,200행 | `user/c02_youth_transport/v01/`, `user/c02_youth_transport/v02/` |
| 03 | 디지털 재취업교육 참여자의 6개월 뒤 소득은 어떤 비교에서 달라지는가? | 기초조사·사업명부·추적조사의 동일한 성인 900명 | `user/c03_training/v01/`, `user/c03_training/v02/` |
| 04 | 주거환경 개선지원 선정기준 근처에서 전력사용량에 차이가 나타나는가? | 신청가구 1,200가구 및 사업별 공개 규칙 | `user/c04_home_insulation/v01/`, `user/c04_home_insulation/v02/` |
| 05 | 디지털 민원교육의 후속 수행 결과와 자기효능감은 어떻게 연결되는가? | 사전조사부터 후속 평가까지 연결되는 신청자 800명 | `user/c05_digital_service/v01/`, `user/c05_digital_service/v02/` |
| 06 | 폭염 안전교육 시간과 열부담의 관계는 옥외근무 노출에 따라 달라지는가? | 기초조사·교육기록·30일 후속관측의 동일한 작업자 900명 | `user/c06_heat_safety/v01/`, `user/c06_heat_safety/v02/` |

전체는 **12세트, 관측자료 표 38개**다. 각 표에 정본 `.csv`와 대응 `.sav`가 있어 관측자료 CSV 38개, SAV 38개가 제공된다. `codebook.csv`, `questionnaire.csv` 같은 설명용 CSV는 이 수에 포함하지 않는다. 여러 파일에 같은 사람이나 지역이 있으므로 파일별 행수를 합쳐 표본수로 보고하지 않는다.

## 4. 자료와 설명서를 읽는 법

예를 들어 청년 교통·구직지원 첫 번째 변형의 경로는 `user/c02_youth_transport/v01/`이다. 아래 표의 `<사례>`와 `<변형>`을 선택한 폴더명으로 바꿔 읽는다.

| 파일 또는 경로 | 담긴 내용 | 분석 전에 확인할 것 |
| --- | --- | --- |
| `user/<사례>/<변형>/README.md` | 정책질문, 대상, 기간, 파일 관계 | 한 행의 의미와 정책 배정·참여 구조 |
| `user/<사례>/<변형>/data/` | 실제 분석할 CSV와 SAV | 같은 표의 한 형식만 읽기 |
| `codebook.csv`, `codebook.json` | 변수명, 설명, 단위, 측정시점, 결측 정의 | 결과·정책·비교·조정 변수의 의미 |
| `datapackage.json` | 파일명, 열 자료형, 기본키, 파일 간 관계 | 중복키, 결합 방향, 예상 행수 |
| `questionnaire.csv` | 자체 작성 문항과 응답 형식 | 무엇을 어떻게 측정했는지 |
| `value_labels.csv` | 범주형 숫자 코드와 의미 | 범주, 기준집단, 사용자 결측코드 |
| `source_crosswalk.csv`, `sources.json` | 실제 자료에서 구조를 참고한 범위와 출처 | 공식 항목, 개념 차용, 자체 설계의 구분 |

표의 짧은 파일명은 해당 사례·변형 폴더 안에 있다. 설명서가 별도 프로그램 없이도 읽히도록 CSV, JSON, Markdown 형식으로 제공한다.

CSV는 UTF-8 BOM이다. 문자열 ID의 앞자리 0을 보존한다. 같은 표의 CSV와 SAV는 대체 형식이므로 서로 이어 붙이거나 다른 표본처럼 합치지 않는다. SAV의 라벨과 사용자 결측 정의를 읽는 방식은 도구에 따라 다를 수 있으므로 코드북과 대조한다. `0`, `-1` 같은 숫자를 모든 변수에서 일괄 결측 처리하지 않는다.

자료를 결합했다면 키, 일대일·다대일 등 관계, 결합 전후 행수, 중복과 미결합 수를 기록한다. 새 변수를 만들었다면 원변수, 계산식, 단위, 적용 범위, 몇 개 행을 원자료와 대조한 결과를 남긴다. 원본은 보존하고 분석용 자료를 별도로 만든다.

## 5. 분석을 진행하는 공통 원칙

연구질문은 “정책이 효과가 있었는가?”에서 한 걸음 더 구체적이어야 한다. 대상, 결과변수, 비교 방향, 기간을 적고 그 비교가 정책 담당자의 질문 중 어느 부분에 답하는지 설명한다.

분석전략을 선택할 때는 가능한 대안을 적어도 하나 함께 검토한다. 방법 이름을 많이 나열하는 것이 목적은 아니다. 왜 이 자료에서 해당 비교를 했는지, 무엇을 가정했는지, 그 가정의 어느 부분을 관측자료로 점검할 수 있고 어느 부분은 남는지를 설명한다. 자료에 맞지 않는 분석을 억지로 실행할 필요는 없다.

효과 크기와 불확실성을 함께 보고한다. 유의확률만으로 정책의 유용성이나 효과 부재를 확정하지 않는다. 효과가 작거나 불확실하다는 답, 자료만으로 인과효과를 구분하기 어렵다는 답도 근거가 충분하면 적절한 결론이다. 새로운 정보를 얻어 계획을 수정했다면 변경 이유와 결과에 미친 영향을 남긴다.

사업 확대에 대한 의견을 쓸 수 있지만, 이 자료에는 모든 사업비·실행 가능성·대안 사업 정보가 들어 있지 않다. 추정된 효과, 비용 대비 가치, 실제 확대 결정에 필요한 추가 정보를 구분한다. 가상 사례의 수치를 현실 사업에 그대로 적용하지 않는다.

## 6. 공통 제출물

수업에서 별도 형식을 지정하지 않으면 다음 묶음을 제출한다. [제출 양식](SUBMISSION_TEMPLATE_KO.md)은 편집해서 사용하거나 같은 내용을 가진 형식으로 대체할 수 있다.

1. **정책 메모 1~2쪽.** 정책질문, 대상과 기간, 핵심 결과와 불확실성, 정책적으로 말할 수 있는 범위, 추가로 필요한 정보. 합성자료 실습임을 첫 부분에 표시한다.
2. **분석 부록.** 가능한 비교전략과 선택 이유, 사용 변수와 단위, 최종 표본, 계산 방식과 설정, 핵심 표·그림, 필요한 가정·진단·민감도 점검과 남은 한계.
3. **자료 처리 기록.** 사례·변형·파일명, 결합키와 관계, 처리 전후 행수, 중복·미결합·결측·제외, 파생변수 정의와 대조 확인 결과.
4. **재현자료.** 실제 실행한 코드·syntax·노트북 또는 GUI 조작 순서와 모든 중요한 옵션, 실행 결과·로그, 필요한 버전·시드·경로 설정. 계획서만 제출하고 실제 계산 기록을 생략하지 않는다.
5. **분석 선택·수정 기록.** 중요한 선택과 변경, 그 이유, 직접 확인한 사항. AI를 사용했다면 사용 범위, 주요 제안, 채택·수정·기각한 내용과 확인한 근거도 적는다. AI를 사용하지 않았다면 대화 기록은 필요 없다.

표와 그림에는 번호·제목·대상·기간·단위·자료 출처를 표시한다. 표에는 표본수, 비교 방향, 추정치와 구간의 의미를 쓰고, 그림에는 축과 범례를 붙인다. 실제 추정한 범위와 관측한 범위를 드러낸다. 정책 메모와 상세 부록의 수치가 같은 계산 결과와 일치해야 한다.

제출 전에 다른 폴더나 새 작업 세션에서 파일을 열고 재현 절차를 확인한다. 제3자가 가진 것은 내려받은 원자료와 제출물이라고 가정한다. 수행하지 않은 진단이나 계산은 했다고 적지 않는다.

## 7. 평가기준: 기본안 100점

수업 담당자가 사전에 조정할 수 있는 평가안이다. 정답 수치나 특정 효과 방향을 맞히는 점수표가 아니다. 개별 분석방법의 적합성과 해석은 담당자가 근거를 읽고 평가하며, 파일 검사나 계산 대조만으로 대신하지 않는다.

| 평가 항목 | 배점 | 확인할 내용 |
| --- | ---: | --- |
| 정책질문과 분석대상 | 15 | 대상·기간·결과·비교가 명확하고 정책 담당자의 질문과 연결되는가 |
| 자료 이해와 처리 | 20 | 관측 단위·시점·변수·결측·결합을 이해하고 처리 결과를 확인했는가 |
| 비교전략과 가정 | 25 | 대안을 검토하고 선택 이유·필요한 가정·식별 범위를 설명했는가 |
| 계산·불확실성·진단 | 20 | 설정과 수치가 재현되며 자료에 맞는 진단과 민감도 검토를 했는가 |
| 정책적 답변과 전달 | 10 | 효과 크기·단위·불확실성·한계를 정확한 표·그림·문장으로 전달하는가 |
| 재현성과 선택 기록 | 10 | 실제 실행 절차와 변경 기록이 있어 다른 사람이 확인할 수 있는가 |
| **합계** | **100** | **소프트웨어 선택이나 AI 사용 여부에 별도 가산·감점 없음** |

수치가 다르다는 이유만으로 오류라고 단정하지 않는다. 분석 표본, 가중치, 결측 처리, 추정 대상, 모형, 표준오차나 구간 설정이 같았는지 먼저 확인한다. 같은 조건의 계산이 일치하는지와 서로 다른 전략의 결론이 얼마나 민감한지는 구분해 검토한다.

## 8. 확장 과제와 선택 도구 안내

한 변형을 마친 뒤 다른 변형을 새 작업으로 분석하고 질문, 표본, 계획, 결과, 해석 범위를 비교할 수 있다. `v01`과 `v02`를 추가 표본이나 다음 조사차수처럼 이어 붙이지 않는다.

원하면 같은 과제를 다른 도구로 다시 수행할 수 있다. 자료 준비와 오류 확인에 든 작업, 분석 선택을 검토하기 쉬웠는지, 결과와 재현자료를 얻는 과정, 같은 설정에서의 수치 일치를 기록한다. [선택 도구 안내](OPTIONAL_TOOLS_KO.md)에 대화형 분석 도구와 MethodIQ를 활용하는 예를 두었다. 사용 여부와 편리함에 대한 평가는 학생이 실제 수행한 경험을 근거로 적는다.

## 9. 출처·이용허락·자료 개정

인용 예: cnucho, *정책효과 분석 연습과제*, 학생용 `policy-analysis-student-v1` 개정 2, 기반 자료 `policy-benchmark-v1`, `c02_youth_transport/v01`, 합성자료 실습. 사례와 변형은 실제 사용한 것으로 바꾼다.

합성자료와 새 문항·설명은 CC BY 4.0이다. 오프라인에서는 `user/LICENSE-DATA.md`를 읽는다. 온라인 [이용허락](https://github.com/cnucho/research-app-examples/blob/main/mcp-special-analysis-tools/policy-benchmark-v1/LICENSE-DATA.md)과 [구조 참고자료](https://github.com/cnucho/research-app-examples/blob/main/mcp-special-analysis-tools/policy-benchmark-v1/sources.json)도 제공한다. 수정본을 공유할 때 출처와 변경 사실을 적는다.

이 학생용 개정은 분석 데이터·코드북·문항·값 라벨·출처·데이터 descriptor를 원래 배포본에서 그대로 가져오고, 수업용 안내와 과제를 독립적으로 구성했다. 자료 폴더의 README는 도구를 지정하지 않도록 편집했고, 등록부의 해당 README 해시와 `user/manifest.json`을 갱신했다. 개정 경로와 전후 해시는 `student-package.json`에 기록한다. 원래 배포본 manifest와 등록부는 `provenance/original-input-manifest.json`, `provenance/original-input-registry.json`에 보존한다. 파일 정합성 확인은 수치·파일의 일치 점검이며 분석전략이나 인과적 해석의 타당성 판정을 뜻하지 않는다.

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
