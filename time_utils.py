# 교안: Python 기초 6장 1강 3.2절 / 9장 2강 2.1절의 datetime.now()와 문자열 변환.
# 실행 조건: 운영체제의 시간대를 한국 표준시(KST, UTC+09:00)로 설정합니다.
# 다른 시간대의 실행 환경은 이 구현에서 지원하지 않습니다.
import datetime


def current_modified_at():
    return str(datetime.datetime.now()) + "+09:00"
