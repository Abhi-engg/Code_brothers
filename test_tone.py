import requests, json

r = requests.post("http://localhost:8000/analyze", json={
    "text": "We must act now! This is critical. Our team needs to come together and support each other. Imagine a world where everyone cooperates. The old weathered door creaked open, revealing a dimly lit corridor.",
    "target_tone": "auto"
})
print("Status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text[:500])
else:
    data = r.json()
    t = data.get("tone_analysis", {})
    print("Dominant tone:", t.get("dominant_tone"))
    print("Tone label:", t.get("tone_label"))
    print("Tone scores:")
    for k, v in t.get("tone_scores", {}).items():
        print(f"  {k}: {v}")
    print("Per-sentence count:", len(t.get("per_sentence", [])))
    print("\nSentiment (expanded):")
    s = data.get("sentiment", {})
    print("  sentiment:", s.get("sentiment"))
    print("  score:", s.get("score"))
    ib = s.get("intensity_breakdown", {})
    print("  intensity:", json.dumps(ib, indent=2) if ib else "N/A")
