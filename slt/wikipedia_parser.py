import json
import bz2
from typing import Any, Dict
import xml.etree.ElementTree as ET


INPUT_PATH = "/home/daniel/data/datasets/wikipedia/jawiki-20181001-corpus.xml.bz2"


TAGS_TO_REMOVE = ["h", "table"]


def extract_content(elem: ET.Element) -> str:
    content = elem.find("content")
    for tag_to_remove in TAGS_TO_REMOVE:
        for elem_to_remove in content.findall(tag_to_remove):
            content.remove(elem_to_remove)
    for paragraph in content.findall("p"):
        for tag_to_remove in TAGS_TO_REMOVE:
            for elem_to_remove in paragraph.findall(tag_to_remove):
                paragraph.remove(elem_to_remove)
        if not paragraph.text:
            content.remove(paragraph)
    return "".join(v.strip() for v in content.itertext())


def parse_element(elem: ET.Element) -> Dict[str, Any]:
    parsed = {
        "title": elem.attrib["name"],
        "categories": [v.attrib["name"] for v in elem.findall("category")],
        "content": extract_content(elem),
    }
    if links_in := elem.find("links_in"):
        parsed["links_in"] = int(links_in.attrib["name"])
    if links_out := elem.find("links_out"):
        parsed["links_out"] = int(links_out.attrib["name"])
    return parsed


parser = ET.XMLPullParser(events=["end"])
with bz2.open(INPUT_PATH, "rb") as f, bz2.open("articles.jsonl.bz2", "wt") as fout:
    for line in f:
        parser.feed(line)
        for event, elem in parser.read_events():
            if elem.tag == "article":
                parsed = parse_element(elem)
                print(json.dumps(parsed, ensure_ascii=False), file=fout)
