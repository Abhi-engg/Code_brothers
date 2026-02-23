"""
Story Generation Module
Uses DistilGPT2 for lightweight text continuation
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Load model once (global)
model_name = "distilgpt2"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)


def generate_story_continuation(text: str, max_length: int = 150) -> str:
    """
    Generate continuation of given story text.
    """

    if not text.strip():
        return ""

    inputs = tokenizer.encode(text, return_tensors="pt")

    outputs = model.generate(
        inputs,
        max_length=len(inputs[0]) + max_length,
        temperature=0.8,
        top_k=50,
        top_p=0.95,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Return only newly generated part
    return generated_text[len(text):].strip()