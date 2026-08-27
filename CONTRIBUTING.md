# 기여 안내

작고 설명 가능한 규칙 변경을 선호합니다. 새 규칙에는 한국어 메시지, 영어 보조 메시지, 양성·음성 테스트를 함께 추가해 주세요.

```bash
python -m pip install .
python -m unittest discover -s tests -v
```

외부 서비스에 의존하는 검사는 기본 내장 규칙이 아니라 선택적 어댑터로 제안해 주세요.
