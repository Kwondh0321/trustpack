MESSAGES = {
    "ko": {
        "scan_complete": "검사가 완료되었습니다.",
        "report_written": "증거 번들을 저장했습니다: {path}",
        "invalid_root": "검사할 경로가 올바른 디렉터리가 아닙니다: {path}",
        "invalid_config": "설정 파일을 읽을 수 없습니다: {detail}",
        "community_title": "프로젝트 기본 문서",
        "missing_readme": "README 파일이 없습니다.",
        "missing_license": "라이선스 파일이 없습니다.",
        "missing_ci": "CI 워크플로를 찾지 못했습니다.",
        "missing_tests": "테스트 디렉터리나 테스트 파일을 찾지 못했습니다.",
        "missing_contributing": "기여 안내 문서가 없습니다.",
        "missing_security": "보안 제보 정책이 없습니다.",
        "dependencies_title": "의존성 고정 상태",
        "unpinned_dependency": "의존성 버전이 정확히 고정되지 않았습니다: {name} ({value})",
        "provenance_title": "파일 출처 증거",
        "research_title": "연구 재현성",
        "notebook_order": "Notebook 실행 번호가 순서대로 증가하지 않습니다.",
        "absolute_path": "환경에 종속된 절대 경로가 포함되어 있습니다.",
        "missing_seed": "확률적 라이브러리를 사용하지만 명시적인 시드 설정을 찾지 못했습니다.",
        "missing_data_source": "데이터 파일이 있지만 출처 또는 데이터 문서를 찾지 못했습니다.",
        "forms_title": "공공서비스 양식",
        "missing_lang": "HTML 문서에 주 언어가 지정되지 않았습니다.",
        "missing_title": "HTML 문서에 제목이 없습니다.",
        "get_personal_form": "개인정보로 보이는 필드가 GET 방식으로 전송될 수 있습니다.",
        "missing_form_purpose": "필수 개인정보 필드가 있지만 수집 목적 표기가 없습니다.",
        "external_title": "외부 검사기",
        "external_failed": "외부 검사기 실행에 실패했습니다: {detail}",
        "external_invalid": "외부 검사기의 JSON 결과를 해석할 수 없습니다.",
    },
    "en": {
        "scan_complete": "Scan completed.",
        "report_written": "Evidence bundle written to: {path}",
        "invalid_root": "The scan target is not a valid directory: {path}",
        "invalid_config": "Could not read configuration: {detail}",
        "community_title": "Project essentials",
        "missing_readme": "No README file was found.",
        "missing_license": "No license file was found.",
        "missing_ci": "No CI workflow was found.",
        "missing_tests": "No test directory or test file was found.",
        "missing_contributing": "No contribution guide was found.",
        "missing_security": "No security reporting policy was found.",
        "dependencies_title": "Dependency pinning",
        "unpinned_dependency": "Dependency is not exactly pinned: {name} ({value})",
        "provenance_title": "File provenance evidence",
        "research_title": "Research reproducibility",
        "notebook_order": "Notebook execution counts are not monotonically increasing.",
        "absolute_path": "A machine-specific absolute path was found.",
        "missing_seed": "Randomized libraries are used without an explicit seed.",
        "missing_data_source": "Data files exist but no source or data documentation was found.",
        "forms_title": "Public-service forms",
        "missing_lang": "The HTML document does not declare its primary language.",
        "missing_title": "The HTML document has no title.",
        "get_personal_form": "A form may send personal information with GET.",
        "missing_form_purpose": "A required personal field has no collection-purpose annotation.",
        "external_title": "External checker",
        "external_failed": "External checker failed: {detail}",
        "external_invalid": "External checker output was not valid JSON.",
    },
}


def translator(lang: str):
    locale = lang if lang in MESSAGES else "ko"

    def translate(key: str, **values: object) -> str:
        return MESSAGES[locale].get(key, key).format(**values)

    return translate

