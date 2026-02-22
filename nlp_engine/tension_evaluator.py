def evaluate_tension(text):

    dramatic_words = ["suddenly", "blood", "fear", "fight", "dark"]

    score = 0
    for word in dramatic_words:
        if word in text.lower():
            score += 1

    return score
