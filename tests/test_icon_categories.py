"""
Tests to validate that all icons referenced in utils.js icon categories
exist in the MDI (Material Design Icons) font set.

Icons are fetched from the same CDN version used in base.html to ensure
consistency. Results are cached to avoid hitting the CDN on every test run.
"""
import json
import re
import pytest
import urllib.request
from pathlib import Path

MDI_VERSION = "7.4.47"
MDI_CSS_URL = f"https://cdn.jsdelivr.net/npm/@mdi/font@{MDI_VERSION}/css/materialdesignicons.css"
CACHE_FILE = Path(__file__).parent / "__pycache__" / "mdi_icons_cache.json"
UTILS_JS = Path(__file__).parent.parent / "app" / "web" / "static" / "js" / "utils.js"


def get_mdi_icon_set() -> set:
    """Fetch and cache the set of valid MDI icon names for the pinned version."""
    if CACHE_FILE.exists():
        return set(json.loads(CACHE_FILE.read_text()))

    with urllib.request.urlopen(MDI_CSS_URL, timeout=10) as resp:
        css = resp.read().decode("utf-8")

    icons = set(re.findall(r'\.mdi-([a-z][a-z0-9-]*)::before', css))
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(sorted(icons)))
    return icons


def extract_icons_from_utils_js() -> dict:
    """
    Parse utils.js to extract all icon names from iconPickerCategories.
    Returns a dict of {category_path: [icon, ...]} e.g.
    {"personal > Health & Fitness": ["walk", "run", ...], ...}
    """
    content = UTILS_JS.read_text()

    # Find the iconPickerCategories block
    match = re.search(r'window\.iconPickerCategories\s*=\s*\{(.+?)\};\s*\n', content, re.DOTALL)
    assert match, "Could not find iconPickerCategories in utils.js"

    result = {}
    # Find top-level sections (household / personal)
    section_re = re.compile(r"(\w+)\s*:\s*\{([^}]+)\}", re.DOTALL)
    for section_match in section_re.finditer(match.group(1)):
        section_name = section_match.group(1)
        section_body = section_match.group(2)

        # Find each category array within the section
        cat_re = re.compile(r"'([^']+)'\s*:\s*\[([^\]]+)\]", re.DOTALL)
        for cat_match in cat_re.finditer(section_body):
            cat_name = cat_match.group(1)
            icons_str = cat_match.group(2)
            icons = re.findall(r"'([^']+)'", icons_str)
            key = f"{section_name} > {cat_name}"
            result[key] = icons

    return result


@pytest.fixture(scope="module")
def mdi_icons():
    try:
        return get_mdi_icon_set()
    except Exception as e:
        pytest.skip(f"Could not fetch MDI icon set: {e}")


@pytest.fixture(scope="module")
def icon_categories():
    return extract_icons_from_utils_js()


def test_all_icons_exist_in_mdi(mdi_icons, icon_categories):
    """Every icon name in iconPickerCategories must exist in the MDI font."""
    invalid = {}
    for category, icons in icon_categories.items():
        bad = [icon for icon in icons if icon not in mdi_icons]
        if bad:
            invalid[category] = bad

    assert not invalid, (
        "Invalid MDI icon names found in utils.js iconPickerCategories:\n"
        + "\n".join(f"  {cat}: {icons}" for cat, icons in invalid.items())
    )


def test_no_duplicate_icons_within_section(icon_categories):
    """Each section (personal/household) should not have duplicate icon names."""
    from collections import defaultdict

    # Group by section
    sections = defaultdict(list)
    for key, icons in icon_categories.items():
        section = key.split(" > ")[0]
        sections[section].extend(icons)

    for section, all_icons in sections.items():
        seen = set()
        dupes = []
        for icon in all_icons:
            if icon in seen:
                dupes.append(icon)
            seen.add(icon)
        assert not dupes, f"Duplicate icons in '{section}' section: {dupes}"


def test_no_empty_categories(icon_categories):
    """Every category should have at least one icon."""
    empty = [cat for cat, icons in icon_categories.items() if not icons]
    assert not empty, f"Empty icon categories: {empty}"
