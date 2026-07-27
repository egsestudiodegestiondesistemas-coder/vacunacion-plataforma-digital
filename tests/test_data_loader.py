from src.utils.data_loader import load_json

def test_calendar_demo_has_stages():
    data = load_json("src/data/calendar_demo.json")
    assert "stages" in data
    assert len(data["stages"]) >= 1
