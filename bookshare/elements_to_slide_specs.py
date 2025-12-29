import json
import sys
from pathlib import Path
from statistics import median

# ----------------------------
# Heuristics helpers
# ----------------------------

def is_probably_logo_or_footer(el, slide_w, slide_h):
    """Heuristic: small element near bottom or tiny at corners -> likely footer/logo."""
    b = el.get("bbox_cm")
    if not b:
        return False
    # Very small
    if b["w"] <= 2.0 and b["h"] <= 2.0:
        # near corners or bottom band
        if b["y"] >= slide_h - 2.0:
            return True
        if b["x"] <= 1.0 or b["x"] >= slide_w - 3.0:
            return True
    # Footer band: y very low and height small
    if b["y"] >= slide_h - 1.5 and b["h"] <= 1.2:
        return True
    return False

def normalize_text_lines(el):
    lines = el.get("text_lines") or []
    # drop empty and normalize whitespace
    out = []
    for ln in lines:
        ln = " ".join(ln.split())
        if ln:
            out.append(ln)
    return out

def bullet_score(lines):
    """How bullet-ish is this text block."""
    if not lines:
        return 0.0
    bullet_prefixes = ("・", "-", "–", "—", "•", "▶", "→", "✓", "＊", "*", "①", "②", "③", "1.", "2.", "3.")
    hits = 0
    for ln in lines:
        s = ln.strip()
        if s.startswith(bullet_prefixes):
            hits += 1
    return hits / max(1, len(lines))

def text_char_count(lines):
    return sum(len(ln) for ln in (lines or []))

def classify_layout_pattern(text_blocks, slide_w):
    """
    Very rough:
    - if text blocks cluster into two x bands -> two_column
    - else -> single_column
    """
    xs = []
    for tb in text_blocks:
        b = tb.get("bbox_cm")
        if not b:
            continue
        xs.append(b["x"] + b["w"]/2)
    if len(xs) < 2:
        return "single_column"

    # split by midline, see if both sides have enough blocks
    mid = slide_w / 2
    left = sum(1 for x in xs if x < mid - 0.5)
    right = sum(1 for x in xs if x > mid + 0.5)
    if left >= 1 and right >= 1:
        return "two_column"
    return "single_column"

def estimate_visual_weight(elements, slide_w):
    """Where visual emphasis tends to be (left/right/center)."""
    visual_centers = []
    for el in elements:
        if el.get("kind") in ("image", "chart", "table"):
            b = el.get("bbox_cm")
            if b:
                visual_centers.append(b["x"] + b["w"]/2)

    if not visual_centers:
        return "text_only"

    m = median(visual_centers)
    if m < slide_w * 0.42:
        return "left_heavy"
    if m > slide_w * 0.58:
        return "right_heavy"
    return "centered"

def estimate_density(total_chars, num_elements, num_text_blocks):
    """
    Simple density tiers.
    Tune thresholds based on your decks.
    """
    score = total_chars + num_elements * 30 + num_text_blocks * 60
    if score < 450:
        return "low"
    if score < 900:
        return "medium"
    return "high"

def choose_headline(text_blocks, slide_w, slide_h):
    """
    Pick headline:
    - Prefer top-most text block with short-ish text
    - If multiple, pick the one closest to top and wide enough
    """
    candidates = []
    for tb in text_blocks:
        b = tb.get("bbox_cm")
        lines = tb.get("lines", [])
        if not b or not lines:
            continue
        txt = " ".join(lines).strip()
        if not txt:
            continue
        # Prefer top area
        top_weight = max(0.0, 1.0 - (b["y"] / max(slide_h, 1e-6)))
        # Prefer not super long
        len_penalty = min(1.0, len(txt) / 120.0)
        # Prefer reasonable width
        width_bonus = min(1.0, b["w"] / max(slide_w, 1e-6))
        score = top_weight * 0.6 + width_bonus * 0.3 - len_penalty * 0.3

        # Extra boost if it's near very top
        if b["y"] <= slide_h * 0.25:
            score += 0.2

        candidates.append((score, txt, b))

    if not candidates:
        return None, None

    candidates.sort(key=lambda x: x[0], reverse=True)
    best = candidates[0]
    return best[1], best[2]

def guess_role(headline, body_lines):
    """
    Optional: rough role guess from keywords.
    You can ignore this and fill role manually later.
    """
    if not headline:
        headline = ""
    text = (headline + " " + " ".join(body_lines)).lower()

    # JP keyword heuristics
    if any(k in text for k in ["課題", "問題", "ペイン", "現状", "ボトルネック"]):
        return "problem"
    if any(k in text for k in ["提案", "解決策", "ソリューション", "打ち手", "施策"]):
        return "proposal"
    if any(k in text for k in ["計画", "プラン", "ロードマップ", "スケジュール", "体制", "進め方"]):
        return "plan"
    if any(k in text for k in ["kpi", "指標", "目標", "効果", "成果"]):
        return "kpi"
    if any(k in text for k in ["まとめ", "結論", "要点", "next", "次のアクション"]):
        return "summary"
    return "unknown"

# ----------------------------
# Main transform
# ----------------------------

def transform(elements_json: dict):
    slide_w = elements_json["slide_size_cm"]["width"]
    slide_h = elements_json["slide_size_cm"]["height"]

    out = {
        "deck_meta": {
            "source": elements_json.get("source"),
            "slide_size_cm": elements_json.get("slide_size_cm"),
            "notes": "Auto-generated slide_specs from PPTX elements. Review 'role' and 'key_message' for best results."
        },
        "slides": []
    }

    for slide in elements_json["slides"]:
        els = slide.get("elements", [])

        # filter obvious noise (logos/footers)
        filtered = []
        for el in els:
            if is_probably_logo_or_footer(el, slide_w, slide_h):
                continue
            filtered.append(el)

        # collect text blocks
        text_blocks = []
        for el in filtered:
            if el.get("kind") != "text":
                continue
            lines = normalize_text_lines(el)
            if not lines:
                continue
            text_blocks.append({
                "bbox_cm": el.get("bbox_cm"),
                "lines": lines,
                "bullet_score": bullet_score(lines),
                "char_count": text_char_count(lines),
            })

        # headline
        headline, headline_bbox = choose_headline(text_blocks, slide_w, slide_h)

        # body blocks = other text blocks excluding headline-like block (by bbox equality)
        body_blocks = []
        for tb in text_blocks:
            if headline_bbox and tb.get("bbox_cm") == headline_bbox:
                continue
            body_blocks.append(tb)

        # build sections (simple)
        sections = []
        if headline:
            sections.append({"type": "title", "text": headline})

        # choose primary body block: highest bullet score, then char count
        primary_body = None
        if body_blocks:
            body_blocks_sorted = sorted(
                body_blocks,
                key=lambda x: (x["bullet_score"], x["char_count"]),
                reverse=True
            )
            primary_body = body_blocks_sorted[0]

        body_lines = primary_body["lines"] if primary_body else []
        if body_lines:
            if primary_body["bullet_score"] >= 0.4:
                sections.append({"type": "bullets", "items": body_lines})
            else:
                sections.append({"type": "text", "text": "\n".join(body_lines)})

        # gather "support" text blocks beyond primary
        support_blocks = []
        for tb in body_blocks:
            if primary_body and tb is primary_body:
                continue
            # treat smaller blocks as evidence/caption candidates
            b = tb.get("bbox_cm") or {}
            if b and b.get("h", 999) <= 3.0 and tb["char_count"] <= 80:
                support_blocks.append(tb)

        if support_blocks:
            # add as captions/evidence (best-effort)
            evidences = []
            for tb in sorted(support_blocks, key=lambda x: (x["char_count"]), reverse=True)[:3]:
                evidences.append({"label": "note", "content": " ".join(tb["lines"])})
            sections.append({"type": "evidence", "items": evidences})

        # visuals
        visuals = []
        img_count = sum(1 for el in filtered if el.get("kind") == "image")
        chart_count = sum(1 for el in filtered if el.get("kind") == "chart")
        table_count = sum(1 for el in filtered if el.get("kind") == "table")
        if img_count:
            visuals.append({"type": "image", "count": img_count})
        if chart_count:
            visuals.append({"type": "chart", "count": chart_count})
        if table_count:
            visuals.append({"type": "table", "count": table_count})

        # density
        total_chars = sum(tb["char_count"] for tb in text_blocks)
        density = estimate_density(
            total_chars=total_chars,
            num_elements=len(filtered),
            num_text_blocks=len(text_blocks)
        )

        # layout pattern
        layout_pattern = classify_layout_pattern(text_blocks, slide_w)
        visual_weight = estimate_visual_weight(filtered, slide_w)

        # key_message (best-effort): headline + first bullet or first line
        key_message = None
        if headline and body_lines:
            key_message = f"{headline} / {body_lines[0]}"
        elif headline:
            key_message = headline
        elif body_lines:
            key_message = body_lines[0]

        role = guess_role(headline, body_lines)

        out["slides"].append({
            "slide_index": slide.get("slide_index"),
            "role": role,  # review later
            "headline": headline,
            "key_message": key_message,
            "structure": {
                "sections": sections
            },
            "layout": {
                "pattern": layout_pattern,     # single_column | two_column
                "density": density,            # low | medium | high
                "visual_weight": visual_weight # left_heavy | right_heavy | centered | text_only
            },
            "visuals": visuals,
            "debug": {
                "total_chars": total_chars,
                "elements_count": len(filtered),
                "text_blocks_count": len(text_blocks),
                "images": img_count,
                "charts": chart_count,
                "tables": table_count,
            }
        })

    return out

def main():
    if len(sys.argv) < 2:
        print("Usage: python elements_to_slide_specs.py path/to/file.elements.json")
        sys.exit(1)

    # ファイルパスにスペースが含まれる場合、複数の引数に分割される可能性があるため結合
    in_path = Path(" ".join(sys.argv[1:]))
    data = json.loads(in_path.read_text(encoding="utf-8"))
    out = transform(data)

    out_path = in_path.with_suffix("").with_suffix(".slide_specs.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
