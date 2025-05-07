import json
from scraper.progress import read_progress, save_progress


def test_read_and_save_progress(tmp_path):
    file = tmp_path / "prog.json"
    # al inicio no existe
    comp, block = read_progress(str(file))
    assert comp == set() and block == set()

    # guardar un estado
    save_progress(str(file), {"a", "b"}, {"x"})
    # ahora leer
    c2, b2 = read_progress(str(file))
    assert c2 == {"a", "b"}
    assert b2 == {"x"}

    # contenido en disco
    with open(str(file), "r", encoding="utf-8") as f:
        data = json.load(f)
    assert set(data["completed"]) == {"a", "b"}
    assert set(data["blocked"]) == {"x"}
