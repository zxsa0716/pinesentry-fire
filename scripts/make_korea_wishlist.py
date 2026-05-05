"""Generate the 30-scene Korean Tanager wishlist GeoJSON for Q7 submission.

Target: 30 scene-equivalent areas spanning Korean forest types most relevant
to the PineSentry-Fire research question. Each polygon is the priority
acquisition footprint (Tanager swath ≈ 18 km × 18 km tile area).

Composition (from competition strategy memo):
  Gwangneung GDK + 동학습림 baseline (8)
  Baekdudaegan pine + oak transect (6)
  East Coast wildfire prone belt (6)
  Pinus densiflora matsutake forest (4)
  DMZ 미접근 forest (3)
  Hallasan + Jeju (3)

Output:
  wishlist/korea_30_scenes.geojson
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path("wishlist/korea_30_scenes.geojson")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Each scene is approximately 0.16 deg × 0.16 deg (≈18 km).
WISHLIST = [
    # Gwangneung GDK + 동학습림 (8)
    ("Gwangneung KoFlux GDK super-site",         127.10, 37.74, 127.20, 37.84, "Gwangneung", "KoFlux primary validation"),
    ("Gwangneung 동학습림 평 yr baseline 봄",       127.05, 37.70, 127.15, 37.80, "Gwangneung", "spring baseline"),
    ("Gwangneung autumn autumn senescence 신호",                127.10, 37.75, 127.20, 37.85, "Gwangneung", "autumn senescence"),
    ("Gwangneung broadleaf forest N face",               127.05, 37.78, 127.15, 37.88, "Gwangneung", "north-face deciduous"),
    ("화천 평 yr 비교",                     127.70, 38.05, 127.80, 38.15, "Hwacheon", "untouched mixed forest"),
    ("춘천 호수~숲 경계",                  127.70, 37.85, 127.80, 37.95, "Chuncheon", "transitional"),
    ("양평 두물머리 활엽수",               127.40, 37.50, 127.50, 37.60, "Yangpyeong", "lowland deciduous"),
    ("가평 Pinus koraiensis림",                     127.50, 37.85, 127.60, 37.95, "Gapyeong", "Pinus koraiensis ref"),
    # Baekdudaegan pine+oak transect (6)
    ("태백산 정상 coniferous forest",               129.00, 37.10, 129.10, 37.20, "Taebaek", "high-elev conifer"),
    ("소백산 능선 broadleaf forest",               128.50, 36.90, 128.60, 37.00, "Sobaek", "ridge mesic"),
    ("월악산 matsutake forest",                     128.20, 36.85, 128.30, 36.95, "Worak", "Pinus densiflora dense"),
    ("속리산 참나무림",                   127.90, 36.55, 128.00, 36.65, "Songnisan", "Quercus mongolica"),
    ("덕유산 mixed forest",                     127.75, 35.85, 127.85, 35.95, "Deogyu", "mixed pine-oak"),
    ("Jirisan Cheonwangbong peak 침엽수",               127.70, 35.30, 127.80, 35.40, "Jirisan", "high pine"),
    # East Coast wildfire prone (6)
    ("강릉 옥계 wildfire prone Pinus densiflora (Korean red pine)",         128.85, 37.65, 128.95, 37.75, "Gangneung", "fire-prone pine belt"),
    ("동해 묵호 matsutake forest",                   129.00, 37.45, 129.10, 37.55, "Donghae", "coastal pine"),
    ("삼척 해안 적송",                     129.10, 37.30, 129.20, 37.40, "Samcheok", "red pine"),
    ("Uljin 금강송림",                     129.30, 36.95, 129.40, 37.05, "Uljin", "Geumgang pine — fire-impacted 2022"),
    ("영덕 해안 침엽수",                   129.30, 36.30, 129.40, 36.40, "Yeongdeok", "coastal Pinus thunbergii"),
    ("포항 호미곶 Pinus thunbergii",                   129.50, 36.05, 129.60, 36.15, "Pohang", "Pinus thunbergii"),
    # matsutake forest Pinus densiflora 특수림 (4)
    ("봉화 Baekdudaegan 송이",                  128.65, 36.95, 128.75, 37.05, "Bonghwa", "songi pine"),
    ("영양 송이특별보호림",                129.05, 36.65, 129.15, 36.75, "Yeongyang", "songi protected"),
    ("청송 주왕산 송이",                   129.15, 36.40, 129.25, 36.50, "Cheongsong", "Juwangsan pine"),
    ("Uiseong 송이주산지 (2025 fire지)",       128.60, 36.40, 128.70, 36.50, "Uiseong", "2025 fire epicenter"),
    # DMZ 미접근 forest (3)
    ("철원 DMZ inland",                   127.20, 38.20, 127.30, 38.30, "Cheorwon", "DMZ pristine"),
    ("양구 DMZ pine",                     127.95, 38.20, 128.05, 38.30, "Yanggu", "DMZ pine"),
    ("고성 DMZ coastal",                  128.45, 38.40, 128.55, 38.50, "Goseong", "DMZ coastal"),
    # Hallasan + Jeju (3)
    ("Hallasan coniferous forest",                    126.55, 33.35, 126.65, 33.45, "Halla", "Abies koreana"),
    ("Halla 동사면 활엽수",                 126.65, 33.35, 126.75, 33.45, "Halla", "east face deciduous"),
    ("Jeju 곶자왈 자생림",                 126.40, 33.30, 126.50, 33.40, "Jeju", "Gotjawal endemic"),
]


def main():
    features = []
    for name, lon0, lat0, lon1, lat1, region, note in WISHLIST:
        features.append({
            "type": "Feature",
            "properties": {
                "name": name,
                "region": region,
                "note": note,
                "priority": "high" if "GDK" in name or "송이" in name or "fire" in name else "medium",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]
                ]],
            },
        })
    fc = {
        "type": "FeatureCollection",
        "name": "PineSentry-Fire 30-scene Korean wishlist",
        "license": "CC-BY-4.0",
        "doi": "(to be assigned upon submission)",
        "features": features,
    }
    OUT.write_text(json.dumps(fc, indent=2, ensure_ascii=False))
    print(f"Saved {len(features)} scenes -> {OUT}")


if __name__ == "__main__":
    main()
