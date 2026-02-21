import spacy

nlp = spacy.load("en_core_web_sm")

def analyze(text):

    doc = nlp(text)

    sentences = [s.text for s in doc.sents]

    tokens = [t.text for t in doc]

    entities = [(e.text, e.label_) for e in doc.ents]

    return {
        "sentences": sentences,
        "tokens": tokens,
        "entities": entities
    }