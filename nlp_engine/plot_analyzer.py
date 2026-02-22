import spacy
nlp = spacy.load("en_core_web_sm")

def extract_story_state(text):
    doc = nlp(text)

    characters = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

    return {
        "characters": list(set(characters)),
        "tone": "neutral",
        "conflict": "unknown"
    }
