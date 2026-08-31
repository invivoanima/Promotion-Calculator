from django.db import migrations, models


REGION_CHOICES = [
    ("seoul", "서울특별시"),
    ("busan", "부산광역시"),
    ("daegu", "대구광역시"),
    ("incheon", "인천광역시"),
    ("gwangju", "광주광역시"),
    ("daejeon", "대전광역시"),
    ("ulsan", "울산광역시"),
    ("sejong", "세종특별자치시"),
    ("gyeonggi", "경기도"),
    ("gangwon", "강원특별자치도"),
    ("chungbuk", "충청북도"),
    ("chungnam", "충청남도"),
    ("jeonbuk", "전북특별자치도"),
    ("jeonnam", "전라남도"),
    ("gyeongbuk", "경상북도"),
    ("gyeongnam", "경상남도"),
    ("jeju", "제주특별자치도"),
]


class Migration(migrations.Migration):
    dependencies = [("calc", "0006_profile_created_at_profile_display_name_and_more")]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="primary_region",
            field=models.CharField(
                blank=True,
                choices=REGION_CHOICES,
                default="",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="regionportfolio",
            name="region",
            field=models.CharField(max_length=30, choices=REGION_CHOICES),
        ),
    ]
