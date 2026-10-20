"""서울특별시 local policy. Values below are a statutory baseline, NOT verified local limits.

Confirm the education-office manual before changing VERIFICATION_STATUS in __init__.py.
No other region imports this file.
"""
from datetime import date
from decimal import Decimal

ASSESSMENT_DATE = date(2026, 2, 28)
JOB_TRAINING_START = date(2016, 3, 1)
TRAINING_CREDIT_RATE = Decimal("0.02")
TRAINING_CREDIT_ANNUAL_CAP = Decimal("0.12")
TRAINING_CREDIT_TOTAL_CAP = Decimal("1")
RULE_NOTICE = "교육청 원문 대조 전 기본 계산입니다. 연수 학점에는 법령 한도인 학년도별 0.12점·총 1점을 적용합니다. 지역별 상한·인정기간·경과조치는 확인이 필요하며 선택가산점은 총점에서 제외합니다."
SOURCE_LINKS = [{"title": "교육공무원 승진규정 (2026.2.28. 기준 적용 법령)", "url": 'https://law.go.kr/LSW/lsPdfPrint.do?ancYnChk=0&bylChaChk=N&efGubun=Y&efYd=20230613&joAllCheck=Y&joEfOutPutYn=on&lsiSeq=251543&mokChaChk=N'}]
