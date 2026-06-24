"""Visual assertion test for chat page layout contract."""
from playwright.sync_api import sync_playwright

APP_URL = "http://localhost:8501"

def overlap(a, b):
    return not (a["x"]+a["width"]<=b["x"] or b["x"]+b["width"]<=a["x"] or a["y"]+a["height"]<=b["y"] or b["y"]+b["height"]<=a["y"])

def assert_close(actual, expected, tolerance, label):
    assert abs(actual-expected)<=tolerance, f"{label}: expected {expected}±{tolerance}, got {actual}"

def test_chat_page_layout_contract():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width":1440,"height":1000})
        page.goto(APP_URL, wait_until="networkidle")
        page.screenshot(path="tests/current_chat_page_debug.png", full_page=True)

        phone = page.locator(".st-key-phone_shell").bounding_box()
        assert phone is not None, "Missing phone shell"
        assert_close(phone["width"], 390, 8, "phone width")
        assert_close(phone["height"], 867, 12, "phone height")

        detail = page.locator(".st-key-chat_view_detail button").bounding_box()
        upload = page.locator(".st-key-chat_upload_ticket button").bounding_box()
        assert detail is not None, "Missing detail button"
        assert upload is not None, "Missing upload button"
        assert abs(detail["y"]-upload["y"])<=4, "Card buttons must be same row"
        assert not overlap(detail, upload), "Card buttons must not overlap"
        assert phone["x"]<=detail["x"]<=phone["x"]+phone["width"], "detail outside phone"
        assert phone["x"]<=upload["x"]+upload["width"]<=phone["x"]+phone["width"], "upload outside phone"
        assert 130<=detail["width"]<=150, f"detail width wrong: {detail['width']}"
        assert 130<=upload["width"]<=150, f"upload width wrong: {upload['width']}"

        qsel = [".st-key-quick_records button",".st-key-quick_rules button",".st-key-quick_attachments button"]
        qboxes = [page.locator(s).bounding_box() for s in qsel]
        assert all(b is not None for b in qboxes), "Missing quick buttons"
        qy = [round(b["y"]) for b in qboxes]
        assert max(qy)-min(qy)<=4, f"Quick buttons not same row: {qy}"
        for i in range(2):
            assert not overlap(qboxes[i], qboxes[i+1]), "Quick buttons overlap"
        for b in qboxes:
            assert 104<=b["width"]<=124, f"quick width should be ~114, got {b['width']}"
            assert 36<=b["height"]<=44, f"quick height should be ~40, got {b['height']}"
            assert phone["x"]<=b["x"], "quick starts outside phone"
            assert b["x"]+b["width"]<=phone["x"]+phone["width"], "quick ends outside phone"

        plus = page.locator(".st-key-chat_plus button").bounding_box()
        msg = page.locator(".st-key-chat_message_input input").bounding_box()
        emoji = page.locator(".st-key-chat_emoji button").bounding_box()
        voice = page.locator(".st-key-chat_voice button").bounding_box()
        assert plus and msg and emoji and voice, "Missing input controls"
        iy = [round(b["y"]) for b in [plus,msg,emoji,voice]]
        assert max(iy)-min(iy)<=6, f"Input not same row: {iy}"
        for i,boxes in enumerate([[plus,msg],[msg,emoji],[emoji,voice]]):
            assert not overlap(boxes[0], boxes[1]), f"Input controls {i} overlap"
        assert 24<=plus["width"]<=40, f"plus width: {plus['width']}"
        assert 220<=msg["width"]<=250, f"msg width: {msg['width']}"
        assert 24<=emoji["width"]<=40, f"emoji width: {emoji['width']}"
        assert 24<=voice["width"]<=40, f"voice width: {voice['width']}"

        browser.close()
        print("=== VISUAL ASSERTIONS PASSED ===")

if __name__ == "__main__":
    test_chat_page_layout_contract()
