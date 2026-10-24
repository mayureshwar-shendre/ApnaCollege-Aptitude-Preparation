#!/usr/bin/env python3
"""Calculate course progress from Markdown checkboxes and refresh the README dashboard.

A topic is considered complete when all four checklist items in its topic README are checked.
Practice completion is counted from checked boxes in each topic's Easy and Medium practice files.
Mock tests are complete when the "Mock completed" checkbox in their README is checked.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
START = "<!--PROGRESS_START-->"
END = "<!--PROGRESS_END-->"

def checked_count(text: str) -> int:
    return len(re.findall(r"(?m)^\s*-\s*\[[xX]\]\s+", text))

def checkbox_count(text: str) -> int:
    return len(re.findall(r"(?m)^\s*-\s*\[[ xX]\]\s+", text))

def pct(done: int, total: int) -> int:
    return round(100 * done / total) if total else 0

def bar(value: int, width: int = 10) -> str:
    filled = round(value * width / 100)
    return "█" * filled + "░" * (width - filled)

def topic_readmes():
    for section in sorted(ROOT.glob("[0-9][0-9]-*")):
        if section.is_dir() and (section / "topics").exists():
            for topic in sorted((section / "topics").iterdir()):
                if topic.is_dir() and (topic / "README.md").exists():
                    yield section, topic

def main():
    rows = []
    topics_done = topics_total = 0
    practice_done = practice_total = 0
    sections = []
    for section in sorted(ROOT.glob("[0-9][0-9]-*")):
        if not section.is_dir() or not (section / "topics").exists():
            continue
        section_topics = []
        for topic in sorted((section / "topics").iterdir()):
            readme = topic / "README.md"
            if not topic.is_dir() or not readme.exists():
                continue
            text = readme.read_text(encoding="utf-8")
            total_checks = checkbox_count(text)
            done_checks = checked_count(text)
            # Four top-level checklist items are the required completion gates.
            required = [
                "- [ ] Review the lecture / lesson material.",
                "- [ ] Complete [lecture notes](./notes/lecture-notes.md).",
                "- [ ] Attempt [Easy practice](./practice/easy.md).",
                "- [ ] Attempt [Medium practice](./practice/medium.md).",
                "- [ ] Update [mistakes log](./review/mistakes-log.md).",
            ]
            complete = all(re.search(r"(?m)^\s*-\s*\[x\]\s+" + re.escape(item[6:]), text, re.I) for item in required)
            topics_total += 1
            topics_done += int(complete)
            section_topics.append((topic.name, complete))
            for level in ("easy", "medium"):
                paper = topic / "practice" / f"{level}.md"
                if paper.exists():
                    ptext = paper.read_text(encoding="utf-8")
                    # One paper is complete only when its explicit completion checkbox is checked.
                    marker = re.search(r"(?m)^\s*-\s*\[[ xX]\]\s*Paper completed\s*$", ptext)
                    practice_total += 1
                    practice_done += int(bool(marker and marker.group(0).lower().replace("[x]", "[x]") and re.search(r"\[[xX]\]", marker.group(0))))
        sections.append((section, section_topics))

    mock_total = mock_done = 0
    mock_rows = []
    for folder_name, label in [
        ("05-tcs-ninja-mock-tests", "TCS Ninja"),
        ("06-tcs-digital-mock-tests", "TCS Digital"),
    ]:
        folder = ROOT / folder_name
        for test in sorted(folder.glob("test-*")) if folder.exists() else []:
            readme = test / "README.md"
            if not readme.exists():
                continue
            text = readme.read_text(encoding="utf-8")
            complete = bool(re.search(r"(?m)^\s*-\s*\[[xX]\]\s*Mock completed\s*$", text))
            mock_total += 1
            mock_done += int(complete)
            mock_rows.append((label, test.name, complete))

    # Weighted overall completion is based on countable deliverables:
    # topic completion + Easy/Medium papers + mock tests.
    overall_total = topics_total + practice_total + mock_total
    overall_done = topics_done + practice_done + mock_done
    overall_pct = pct(overall_done, overall_total)

    lines = [
        "| Learning metric | Completed / Total | Progress |",
        "|---|---:|---|",
        f"| Topics | {topics_done}/{topics_total} | `{bar(pct(topics_done, topics_total))}` {pct(topics_done, topics_total)}% |",
        f"| Easy / Medium practice papers | {practice_done}/{practice_total} | `{bar(pct(practice_done, practice_total))}` {pct(practice_done, practice_total)}% |",
        f"| TCS Ninja + Digital mock tests | {mock_done}/{mock_total} | `{bar(pct(mock_done, mock_total))}` {pct(mock_done, mock_total)}% |",
        f"| **Overall deliverables** | **{overall_done}/{overall_total}** | **`{bar(overall_pct)}` {overall_pct}%** |",
        "",
        "> Progress is calculated from checked Markdown boxes. Topic completion requires all five topic checklist items to be checked. Practice papers and mock tests require their explicit completion checkbox.",
        "",
        "### Section progress",
        "",
        "| Section | Completed topics | Progress |",
        "|---|---:|---|",
    ]
    for section, topics in sections:
        done = sum(1 for _, complete in topics if complete)
        total = len(topics)
        name = section.name
        lines.append(f"| [{name}](./{name}/README.md) | {done}/{total} | `{bar(pct(done,total))}` {pct(done,total)}% |")
    dashboard = "\n".join(lines)
    if not README.exists():
        print("README.md not found", file=sys.stderr)
        return 1
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("README progress markers are missing", file=sys.stderr)
        return 1
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    README.write_text(before + START + "\n" + dashboard + "\n" + END + after, encoding="utf-8")
    print(f"Updated progress: {overall_done}/{overall_total} deliverables ({overall_pct}%).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
