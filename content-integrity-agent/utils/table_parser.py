"""Extract structured data from Google Docs table bodies."""
from typing import List, Dict, Optional


def _cell_text(cell_content: list) -> str:
    """Extract plain text from a table cell's content."""
    parts = []
    for elem in cell_content:
        paragraph = elem.get("paragraph")
        if not paragraph:
            continue
        for pe in paragraph.get("elements", []):
            text = pe.get("textRun", {}).get("content", "")
            parts.append(text)
    return "".join(parts).strip()


def _cell_people(cell_content: list) -> List[Dict[str, str]]:
    """Extract person elements from a table cell's content."""
    people = []
    for elem in cell_content:
        paragraph = elem.get("paragraph")
        if not paragraph:
            continue
        for pe in paragraph.get("elements", []):
            person = pe.get("person")
            if person:
                props = person.get("personProperties", {})
                name = props.get("name", "")
                email = props.get("email", "")
                if name and email:
                    people.append({"name": name, "email": email})
    return people


def find_table_in_body(body: dict) -> Optional[dict]:
    """Return the first table from a Google Docs body, or None."""
    for sec in body.get("content", []):
        if "table" in sec:
            return sec["table"]
    return None


def extract_page_owners_from_table(table: dict) -> List[Dict[str, str]]:
    """
    Find the row with a first cell containing 'Page owner' (case-insensitive)
    and extract all person elements from the second cell.
    """
    for row in table.get("tableRows", []):
        cells = row.get("tableCells", [])
        if len(cells) < 2:
            continue
        label = _cell_text(cells[0].get("content", []))
        if "page owner" in label.lower():
            return _cell_people(cells[1].get("content", []))
    return []
