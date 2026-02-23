from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re

model_name = "distilgpt2"

# Load once (IMPORTANT: do not load inside function)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


def generate_story_continuation(context, max_tokens=120):

    prompt = f"""
Continue the following story naturally:

{context}

Next:
"""

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        temperature=0.9,
        top_p=0.95,
        do_sample=True,
        repetition_penalty=1.2
    )

    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    generated = full_text[len(prompt):].strip()

    # Clean ending sentence
    sentences = re.split(r'(?<=[.!?]) +', generated)
    cleaned = " ".join(sentences[:-1]) if len(sentences) > 1 else generated

    return cleaned.strip()