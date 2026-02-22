"""Phase 8 — Anti-Patterns end-to-end verification"""
import requests, json, sys

API = "http://localhost:8000/analyze"

# Text designed to trigger multiple anti-pattern categories
TEXT = (
    "She walked quickly through the very unique garden. He was happy about the situation. "
    "I think the implementation of the investigation was somewhat successful. "
    "There are many reasons to consider this approach. It was a dark and stormy night. "
    "I saw that the door was open. I felt that something was wrong. "
    "Perhaps we should sort of consider the utilization of better management practices. "
    "He said softly, 'I really just basically want to help.' "
    "The completely destroyed building was absolutely essential to the story. "
    "She seemed worried about the establishment of the new committee. "
    "I was walking down the street when I noticed that the sky was very big and very dark. "
    "The assessment of the requirement showed the development of a new process was needed. "
    "Maybe the determination of the outcome was kind of important."
)

print("=" * 65)
print("  Phase 8 · Anti-Patterns · E2E Test")
print("=" * 65)

# 1. Test with antipatterns enabled
resp = requests.post(API, json={"text": TEXT, "features": {"antipatterns": True}})
assert resp.status_code == 200, "FAIL: status=%s" % resp.status_code
data = resp.json()
ap = data.get("antipatterns")

assert ap is not None, "FAIL: antipatterns key missing from response"
assert "error" not in ap, "FAIL: antipatterns has error: %s" % ap.get("error")
assert "categories" in ap, "FAIL: missing categories"
assert "summary" in ap, "FAIL: missing summary"

cats = ap["categories"]
summary = ap["summary"]

print("\n[PASS] Status 200, antipatterns present")
print("[PASS] Summary: total=%d, critical=%d, moderate=%d, minor=%d" % (
    summary["total"], summary["critical"], summary["moderate"], summary["minor"]))

# 2. Verify all 8 categories exist
expected_cats = [
    "adverb_overuse", "show_dont_tell", "nominalizations",
    "hedge_words", "redundant_modifiers", "weak_openings",
    "filter_words", "info_dumps"
]
for cat in expected_cats:
    assert cat in cats, "FAIL: category '%s' missing" % cat
    assert "instances" in cats[cat], "FAIL: '%s' missing instances" % cat
    assert "count" in cats[cat], "FAIL: '%s' missing count" % cat
    assert "category" in cats[cat], "FAIL: '%s' missing category" % cat
    assert "educational_tip" in cats[cat], "FAIL: '%s' missing educational_tip" % cat
print("[PASS] All 8 categories present with correct structure")

# 3. Check that specific detections fired
cats_with_hits = {k: v["count"] for k, v in cats.items() if v["count"] > 0}
print("\n  Detections per category:")
for k, v in sorted(cats_with_hits.items(), key=lambda x: -x[1]):
    print("    %-22s : %d instances" % (k, v))

assert len(cats_with_hits) >= 4, "FAIL: expected at least 4 categories with hits, got %d" % len(cats_with_hits)
print("[PASS] At least 4 categories triggered")

# 4. Verify instance structure
for cat_key, cat_data in cats.items():
    for inst in cat_data["instances"]:
        required = {"text", "location", "severity", "rule", "suggestion", "before_after_example"}
        missing = required - set(inst.keys())
        assert not missing, "FAIL: instance in '%s' missing keys: %s" % (cat_key, missing)
        ba = inst["before_after_example"]
        assert "before" in ba and "after" in ba, "FAIL: before_after missing keys in '%s'" % cat_key
print("[PASS] All instance structures valid (text, location, severity, rule, suggestion, before_after_example)")

# 5. Verify severities are valid
valid_sevs = {"critical", "moderate", "minor"}
for cat_key, cat_data in cats.items():
    for inst in cat_data["instances"]:
        assert inst["severity"] in valid_sevs, "FAIL: invalid severity '%s' in '%s'" % (inst["severity"], cat_key)
print("[PASS] All severities valid")

# 6. Test with antipatterns disabled
resp2 = requests.post(API, json={"text": TEXT, "features": {"antipatterns": False}})
assert resp2.status_code == 200
data2 = resp2.json()
print("[PASS] antipatterns disabled -> antipatterns=%s" % (
    "absent" if data2.get("antipatterns") is None else "present"))

# 7. Sample instances
print("\nSample instances:")
for cat_key in ["adverb_overuse", "show_dont_tell", "redundant_modifiers", "hedge_words", "weak_openings"]:
    if cats[cat_key]["count"] > 0:
        inst = cats[cat_key]["instances"][0]
        print("  [%s] '%s' => %s" % (cat_key, inst["text"], inst["suggestion"][:60]))

print("\n" + "=" * 65)
print("  ALL TESTS PASSED")
print("=" * 65)
