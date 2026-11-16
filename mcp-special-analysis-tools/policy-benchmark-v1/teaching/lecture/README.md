# 정책 데이터 분석 강의자료 원본

완성된 4쪽 강의자료의 본문·참고문헌·박스플롯과 PDF 생성 코드를 보존한다. 문제 발견, 예측, 원인·효과의 순서로 읽는 자료이며, 별도 실습과제나 특정 앱 없이 사용할 수 있다.

## 파일

| 파일 | 역할 |
| --- | --- |
| [LECTURE_KO.md](LECTURE_KO.md) | 동일 본문과 실제 수록 참고문헌 13개를 읽는 Markdown 원고 |
| [build_lecture.py](build_lecture.py) | 고정된 4쪽 구성, 합성자료 박스플롯, 한국어 글꼴 포함 PDF 생성 |
| [sources.json](sources.json) | 출처 15개의 서지·원문 링크·사용 범위; PDF에서는 `ORDER`의 13개를 사용 |
| [requirements.txt](requirements.txt) | 재생성에 사용한 Python 패키지 버전 |
| [.gitignore](.gitignore) | PDF, 그림, 글꼴 캐시 등 생성물의 Git 제외 규칙 |

PDF 본문은 `build_lecture.py`의 `CONTENT`와 지면 구성에 들어 있다. `LECTURE_KO.md`는 같은 본문을 읽기 쉽게 옮긴 원고다. 내용을 수정할 때에는 두 파일의 문장이 일치하는지 확인한다. 출처의 서지와 링크는 `sources.json`에서 관리한다. 인용 번호를 바꾸는 경우에는 `ORDER`와 본문 번호도 함께 확인한다.

## 저장소 배치

이 디렉터리는 다음 위치에 둔다.

```text
mcp-special-analysis-tools/policy-benchmark-v1/teaching/lecture/
```

한국어 글꼴을 PDF에 포함하는 공통 함수는 상위 디렉터리의 `../build_handbook.py`에서 가져온다. 따라서 저장소의 `teaching/` 구조를 유지한다. 특정 작업 공간이나 사용자 홈 경로를 참조하지 않는다.

## 생성 환경

Python 3.11 이상과 `requirements.txt`의 패키지를 사용한다. 한국어 글꼴은 Noto Sans CJK의 Regular·Bold TTC를 사용하며, 기본 경로는 다음과 같다.

- `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`
- `/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc`

Ubuntu·Debian에서는 `fonts-noto-cjk`가 해당 글꼴을 제공한다. 다른 위치의 글꼴을 사용하는 경우 아래 인자로 지정한다. Poppler의 `pdftoppm`과 `pdfinfo`는 생성 후 화면·페이지를 검토할 때 사용하며, 생성 코드의 필수 의존성은 아니다.

## 실행

저장소 루트에서 실행한다.

```bash
python -m pip install -r mcp-special-analysis-tools/policy-benchmark-v1/teaching/lecture/requirements.txt

python mcp-special-analysis-tools/policy-benchmark-v1/teaching/lecture/build_lecture.py \
  --output /tmp/policy-lecture-output/policy-data-lecture-ko.pdf \
  --tmp /tmp/policy-lecture-build
```

`--output`은 완성 PDF의 경로이고, `--tmp` 또는 `--tmpdir`는 글꼴 캐시·박스플롯·텍스트·배치 기록을 둘 임시 디렉터리다. 인자를 생략하면 이 디렉터리 아래의 `output/pdf/`와 `tmp/pdfs/`를 사용한다. 기존 배포본을 보존하려면 새로운 출력 경로를 지정한다.

기본 위치에 글꼴이 없는 환경에서는 경로를 지정한다.

```bash
python mcp-special-analysis-tools/policy-benchmark-v1/teaching/lecture/build_lecture.py \
  --output /tmp/policy-lecture-output/policy-data-lecture-ko.pdf \
  --tmp /tmp/policy-lecture-build \
  --font-regular /path/to/NotoSansCJK-Regular.ttc \
  --font-bold /path/to/NotoSansCJK-Bold.ttc \
  --font-index 1
```

Noto Sans CJK TTC의 인덱스 1은 한국어 글꼴이다. 다른 글꼴 모음을 지정할 때에는 해당 모음의 인덱스를 확인한다.

## 생성과 검증

생성 코드는 4쪽 여부, 각 페이지의 텍스트, 수록한 원문 링크의 포함 여부를 확인한 뒤 JSON 결과를 출력한다. 임시 디렉터리에는 `extracted.txt`, `layout-record.json`, `synthetic_boxplot.png`, 글꼴 캐시가 생성된다. 링크 주석은 줄바꿈에 따라 같은 URL에 여러 개 생길 수 있으므로, 주석 수와 고유 URL 수를 구분한다. 기준 완성본에는 URI 주석 25개, 고유 원문 URL 13개가 있다.

박스플롯은 코드에 명시한 합성 관측값으로 생성한다. 두 지역의 평균은 11일, 중앙값은 각각 11일과 7일이다. 논문의 실제 관측값이나 분석 결과를 재현한 그림이 아니다. 외부 그림 파일을 내려받을 필요는 없다.

PDF의 생성 시각이나 글꼴 부분집합에 따라 파일 해시는 달라질 수 있다. 재현 여부는 페이지 수, 페이지별 추출 텍스트, 링크 대상과 화면을 함께 비교한다. PDF·그림·글꼴 캐시 등 생성물은 Git에 넣지 않으며, 배포·백업 위치는 상위 자료 배포 기록에서 관리한다.
