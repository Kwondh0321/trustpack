# TrustPack

TrustPack은 저장소의 보안 준비 상태, 의존성 고정, 연구 재현성, 공공서비스 양식, 파일 출처 증거를 **하나의 검토 가능한 증거 번들**로 만드는 한국어 우선 CLI입니다.

여러 검사기의 점수를 단순히 합치는 대신 모든 발견 사항을 공통 JSON 구조로 정리하고, 검사 시점의 파일 SHA-256과 Git 커밋을 함께 기록합니다. 모델이나 API 키 없이 로컬에서 동작합니다.

## 빠른 시작

```bash
python -m pip install .
trustpack scan . --profile full
```

생성 결과:

- `trustpack-evidence/trustpack.json`: 자동화와 장기 보존을 위한 원본 증거
- `trustpack-evidence/report.html`: 사람이 검토하기 쉬운 한국어 보고서

공유 가능한 보고서에는 검사한 컴퓨터의 절대경로를 기록하지 않으며, 기본 결과 디렉터리는 다음 검사에서 자동 제외됩니다. JSON 형식은 [`schema/trustpack.schema.json`](schema/trustpack.schema.json)으로 검증할 수 있습니다.

프로필은 `release`, `research`, `public-service`, `full`을 제공합니다.

```bash
trustpack scan ./research --profile research --fail-on high
trustpack scan ./service --profile public-service --lang en
```

## 현재 내장 검사

- README, 라이선스, CI, 테스트, 기여·보안 문서
- npm 및 Python 의존성의 정확한 버전 고정
- 파일별 크기와 SHA-256, Git HEAD
- Notebook 실행 순서, 절대경로, random seed, 데이터 출처 문서
- HTML 언어·제목, 개인정보 GET 전송, 수집 목적 표기

## 기존 도구 연결

`examples/trustpack.json`처럼 외부 검사기 명령을 등록할 수 있습니다. 명령은 셸을 거치지 않고 인자 배열로 실행되며 JSON의 `findings` 배열을 공통 형식으로 정규화합니다.

```bash
trustpack scan . --config examples/trustpack.json
```

설정 파일은 임의 명령을 실행할 수 있으므로 신뢰하는 저장소의 설정만 사용하세요.

## 언어

CLI와 보고서의 기본 언어는 한국어입니다. 영어 보조 출력은 `--lang en`으로 선택합니다. 영어 소개는 [README.en.md](README.en.md)에 있습니다.

## 한계

TrustPack은 자동 검토의 출발점입니다. 규정 준수, 보안성, 연구 결과의 진실성이나 서비스의 법적 적합성을 보증하지 않습니다. 파일 해시는 검사 당시 바이트의 동일성만 증명합니다.

## 개발

```bash
python -m pip install .
python -m unittest discover -s tests -v
```

Apache-2.0
