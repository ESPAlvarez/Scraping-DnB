from scraper.utils import cargar_proxies, cargar_links, load_json, save_json


def test_cargar_proxies(tmp_path):
    f = tmp_path / "proxies.txt"
    f.write_text("1.2.3.4\n\n5.6.7.8\n")
    lst = cargar_proxies(str(f))
    assert lst == ["1.2.3.4", "5.6.7.8"]


def test_cargar_links(tmp_path, monkeypatch):
    # crea archivo con URLs relativas y absolutas
    f = tmp_path / "links.txt"
    f.write_text("/foo\nhttp://bar\nbaz\n")
    # monkeypatch BASE_URL en utils (si tu módulo lo usa)
    import scraper.utils as u

    monkeypatch.setattr(u, "BASE_URL", "https://site.com")
    links = cargar_links(str(f))
    assert links == [
        "https://site.com/foo",
        "http://bar",
        "https://site.com/baz"
    ]


def test_load_and_save_json(tmp_path):
    data = {"x": 1}
    fp = tmp_path / "d" / "f.json"
    save_json(str(fp), data)
    loaded = load_json(str(fp), {})
    assert loaded == data
    # default when missing
    assert load_json(str(
        tmp_path / "no.json"), {"def": True}) == {"def": True}
