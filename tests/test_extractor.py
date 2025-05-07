from scraper.extractor import (
    extract_subindustries,
    extract_companies_detailed,
    bypass_challenge,
    is_error_500,
    is_access_denied,
    is_connection_lost,
    is_no_companies_message,
)
from types import SimpleNamespace

# Un HTML de ejemplo con dos sub‑industria
HTML_SUB = """
<div class="col-md-6 col-xs-6 data">
  <a href="/business-directory/company-information.foo.en.html">
    Foo Industry
  </a>
</div>
<div class="col-md-6 col-xs-6 data">
  <a href="/business-directory/company-information.bar.en.html">
    Bar Industry
  </a>
</div>
"""

# Un fragmento de HTML de empresas
HTML_COMPS = """
<div class="col-md-12 data">
  <div class="col-md-6">
    <a href="/company-profiles/acme">Acme Corp</a>
  </div>
  <div class="col-md-4">Some City</div>
  <div class="col-md-2 last">$123M</div>
</div>
"""


class DummyDriver:
    def __init__(self, page_source="", elements=None):
        self.page_source = page_source
        self._elements = elements or {}

    def find_element(self, by, val):
        if val in self._elements:
            return SimpleNamespace()
        from selenium.common.exceptions import NoSuchElementException

        raise NoSuchElementException()

    def execute_script(self, *_):
        pass


def test_extract_subindustries_basic():
    items = extract_subindustries(HTML_SUB)
    assert len(items) == 2
    assert items[0][0] == "Foo Industry"
    assert (
        "/business-directory/company-information.foo.en.html"
        in items[0][1]
    )


def test_extract_companies_detailed_basic():
    data = extract_companies_detailed(HTML_COMPS, "foo")
    assert len(data) == 1
    c = data[0]
    assert c["company_name"] == "Acme Corp"
    assert c["company_link"].endswith("/company-profiles/acme")
    assert c["revenue"] == "$123M"
    assert c["sub_industry"] == "foo"


def test_bypass_and_error_detectors():
    # driver con iframe de captcha
    drv = DummyDriver(elements={"sec-cpt-if": True})
    assert bypass_challenge(drv)

    # Simular 500 Error en contenido HTML
    drv2 = DummyDriver(page_source="<h2>500 Error</h2>")
    assert is_error_500(drv2)

    # Simular Access Denied en contenido HTML
    drv3 = DummyDriver(page_source="<h1>Access Denied</h1>")
    assert is_access_denied(drv3)

    # Simular texto de conexión perdida
    drv4 = DummyDriver(page_source="Connection Lost")
    assert is_connection_lost(drv4)

    # Simular ausencia de empresas
    drv5 = DummyDriver(
        elements={"candidatesMatchedQuantityIsNullOrZeroWrapper": True}
    )
    assert is_no_companies_message(drv5)
