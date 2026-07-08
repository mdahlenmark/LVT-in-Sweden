from scb_lvt.jsonstat import jsonstat_to_rows


def test_jsonstat_to_rows_flattens_dimensions():
    payload = {
        "id": ["Region", "Tid"],
        "size": [2, 2],
        "dimension": {
            "Region": {"category": {"index": {"0180": 0, "1480": 1}, "label": {"0180": "Stockholm", "1480": "Göteborg"}}},
            "Tid": {"category": {"index": {"2022": 0, "2023": 1}, "label": {"2022": "2022", "2023": "2023"}}},
        },
        "value": [1, 2, 3, 4],
    }

    assert jsonstat_to_rows(payload) == [
        {"value": 1, "Region_code": "0180", "Region_label": "Stockholm", "Tid_code": "2022", "Tid_label": "2022"},
        {"value": 2, "Region_code": "0180", "Region_label": "Stockholm", "Tid_code": "2023", "Tid_label": "2023"},
        {"value": 3, "Region_code": "1480", "Region_label": "Göteborg", "Tid_code": "2022", "Tid_label": "2022"},
        {"value": 4, "Region_code": "1480", "Region_label": "Göteborg", "Tid_code": "2023", "Tid_label": "2023"},
    ]
