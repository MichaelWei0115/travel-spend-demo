"""Visual contract test for chat page button layout."""
from pathlib import Path
from playwright.sync_api import sync_playwright

APP_URL = "http://localhost:8501"
DEBUG_DIR = Path("tests/visual_debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

def get_box(page, selector):
    loc = page.locator(selector)
    assert loc.count() > 0, f"Missing: {selector}"
    box = loc.first.bounding_box()
    assert box is not None, f"No box: {selector}"
    return box

def overlaps(a, b):
    return not (a["x"]+a["width"]<=b["x"] or b["x"]+b["width"]<=a["x"] or a["y"]+a["height"]<=b["y"] or b["y"]+b["height"]<=a["y"])

def assert_between(v, lo, hi, label):
    assert lo <= v <= hi, f"{label}: expected {lo}-{hi}, got {v}"

def assert_same_row(items, tol, label):
    ys = [round(i["y"]) for i in items]
    assert max(ys)-min(ys) <= tol, f"{label} not same row: {ys}"

def assert_no_overlap(items, label):
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            assert not overlaps(items[i], items[j]), f"{label}: {i} overlaps {j}"

def assert_inside(inner, outer, label):
    assert inner["x"] >= outer["x"]-2, f"{label}: left overflow"
    assert inner["x"]+inner["width"] <= outer["x"]+outer["width"]+2, f"{label}: right overflow"

def test_chat_buttons_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width":1440,"height":1000})
        page.goto(APP_URL, wait_until="networkidle")
        page.wait_for_timeout(800)
        page.screenshot(path=str(DEBUG_DIR/"chat_buttons.png"), full_page=True)

        phone = get_box(page, ".st-key-phone_shell")
        assert_between(phone["width"], 382, 398, "phone width")
        assert_between(phone["height"], 855, 879, "phone height")

        detail = get_box(page, ".st-key-btn_ticket_detail button")
        upload = get_box(page, ".st-key-btn_ticket_upload button")
        assert_inside(detail, phone, "detail btn")
        assert_inside(upload, phone, "upload btn")
        assert_same_row([detail, upload], 4, "ticket btns")
        assert_no_overlap([detail, upload], "ticket btns")
        assert_between(detail["width"], 136, 150, "detail w")
        assert_between(upload["width"], 136, 150, "upload w")
        assert_between(detail["height"], 32, 40, "detail h")
        assert_between(upload["height"], 32, 40, "upload h")
        assert upload["width"] < 180, f"upload too wide: {upload['width']}"

        bg = page.locator(".st-key-btn_ticket_upload button").evaluate("el => getComputedStyle(el).backgroundColor")
        assert "255, 0, 0" not in bg, f"upload is red: {bg}"
        assert "255, 59, 48" not in bg, f"upload is red: {bg}"
        assert "255, 77, 79" not in bg, f"upload is red: {bg}"

        quick = [get_box(page, f".st-key-btn_quick_{n} button") for n in ["records","rules","files"]]
        assert_same_row(quick, 4, "quick btns")
        assert_no_overlap(quick, "quick btns")
        for i, b in enumerate(quick):
            assert_inside(b, phone, f"quick {i}")
            assert_between(b["width"], 104, 124, f"quick {i} w")
            assert_between(b["height"], 36, 44, f"quick {i} h")

        plus = get_box(page, ".st-key-btn_chat_plus button")
        msg = get_box(page, ".st-key-input_chat_message input")
        emoji = get_box(page, ".st-key-btn_chat_emoji button")
        voice = get_box(page, ".st-key-btn_chat_voice button")
        input_items = [plus, msg, emoji, voice]
        assert_same_row(input_items, 6, "input toolbar")
        assert_no_overlap(input_items, "input toolbar")
        for i, b in enumerate(input_items):
            assert_inside(b, phone, f"input {i}")
        assert_between(plus["width"], 24, 40, "plus w")
        assert_between(msg["width"], 220, 250, "msg w")
        assert_between(emoji["width"], 24, 40, "emoji w")
        assert_between(voice["width"], 24, 40, "voice w")

        browser.close()
        print("=== VISUAL CONTRACT PASSED ===")

if __name__ == "__main__":
    test_chat_buttons_layout()
