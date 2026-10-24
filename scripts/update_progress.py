#!/usr/bin/env python3
"""Calculate course progress from Markdown tables [✔] and refresh the README dashboard."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
START = "<!--PROGRESS_START-->"
END = "<!--PROGRESS_END-->"

def pct(done: int, total: int) -> int:
    return round(100 * done / total) if total else 0

def bar(value: int, width: int = 10) -> str:
    filled = round(value * width / 100)
    return "█" * filled + "░" * (width - filled)

def main():
    topics_total, topics_done = 0, 0
    practice_total, practice_done = 0, 0
    mock_total, mock_done = 0, 0
    sections_data = []

    # 1. Parse Topics and Practice (Folders 01 to 04)
    for i in range(1, 5):
        for section in sorted(ROOT.glob(f"0{i}-*")):
            if not section.is_dir():
                continue
            
            readme = section / "README.md"
            sec_done, sec_total = 0, 0
            
            if readme.exists():
                content = readme.read_text(encoding="utf-8")
                # Count total topics (rows starting with a number)
                sec_total = len(re.findall(r'(?m)^\|\s*\d+\s*\|', content))
                # Count completed topics (rows with [✔])
                sec_done = len(re.findall(r'\|\s*\[✔\]\s*\|', content))
                
                topics_total += sec_total
                topics_done += sec_done
            
            # Count practice papers inside topics directories
            if (section / "topics").exists():
                for level in ["easy", "medium"]:
                    for paper in section.rglob(f"practice/{level}.md"):
                        practice_total += 1
                        ptext = paper.read_text(encoding="utf-8")
                        if re.search(r"(?m)^\s*-\s*\[[xX]\]", ptext) or "[✔]" in ptext:
                            practice_done += 1
            
            sections_data.append((section.name, sec_done, sec_total))

    # 2. Parse Mock Tests (Folders 05 to 06)
    for i in range(5, 7):
        for section in sorted(ROOT.glob(f"0{i}-*")):
            if not section.is_dir():
                continue
                
            readme = section / "README.md"
            if readme.exists():
                content = readme.read_text(encoding="utf-8")
                # Exclude the review rule section, count only rows in the table
                mock_total += len(re.findall(r'(?m)^\|\s*Mock \d+\s*\|', content))
                mock_done += len(re.findall(r'\|\s*\[✔\]\s*\|', content))

    # 3. Calculate Overall Progress
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
        "|---|---:|---|"
    ]

    for name, done, total in sections_data:
        # Fallback to avoid division by zero if total is 0
        section_pct = pct(done, total) if total > 0 else 0
        lines.append(f"| [{name}](./{name}/README.md) | {done}/{total} | `{bar(section_pct)}` {section_pct}% |")

    dashboard = "\n".join(lines)

    if not README.exists():
        print("Main README.md not found", file=sys.stderr)
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