"""
Plot Generator Module
Generates next plot points based on previous narrative
"""

import random
from typing import Dict, Any

from nlp_engine.plot_analyzer import extract_story_state
from nlp_engine.tension_evaluator import evaluate_tension


def generate_next_plot(previous_plots: str) -> Dict[str, Any]:
    """
    Generate the next plot point based on previous plot points.
    
    Args:
        previous_plots: String containing previous plot points
        
    Returns:
        Dictionary containing generated plot suggestions
    """
    if not previous_plots:
        return {
            "success": False,
            "error": "No previous plots provided"
        }
    
    # Split the previous plots by newlines or periods
    plot_list = [p.strip() for p in previous_plots.replace('\n', '.').split('.') if p.strip()]
    
    # Analyze the last plot point
    last_plot = plot_list[-1] if plot_list else previous_plots
    plot_count = len(plot_list)
    
    # Generate suggestions based on story structure
    suggestions = []
    
    if plot_count == 1:
        # After inciting incident, add complications
        suggestions = [
            f"A mysterious stranger appears, complicating the situation.",
            f"An unexpected obstacle prevents easy resolution.",
            f"A hidden truth is revealed that changes everything."
        ]
    elif plot_count == 2:
        # Rising action
        suggestions = [
            f"The stakes are raised as time runs out.",
            f"An ally becomes an enemy, or vice versa.",
            f"A crucial piece of information is discovered."
        ]
    elif plot_count >= 3:
        # Approaching climax
        suggestions = [
            f"The protagonist must make a difficult choice.",
            f"All story threads begin to converge.",
            f"The ultimate confrontation begins."
        ]
    
    # Add context-aware suggestions
    if "discover" in last_plot.lower():
        suggestions.append("The discovery leads to an unexpected consequence.")
    if "mysterious" in last_plot.lower():
        suggestions.append("The mystery deepens with a new clue.")
    if "artifact" in last_plot.lower() or "object" in last_plot.lower():
        suggestions.append("The artifact reveals its true purpose.")
    
    return {
        "success": True,
        "plot_number": plot_count + 1,
        "previous_plot_summary": last_plot,
        "suggestions": suggestions[:3],  # Return top 3 suggestions
        "narrative_stage": get_narrative_stage(plot_count)
    }


def get_narrative_stage(plot_count: int) -> str:
    """
    Determine the current stage of the narrative.
    
    Args:
        plot_count: Number of plot points so far
        
    Returns:
        String describing the narrative stage
    """
    if plot_count == 1:
        return "Inciting Incident"
    elif plot_count == 2:
        return "Rising Action - Early"
    elif plot_count <= 4:
        return "Rising Action - Middle"
    elif plot_count <= 6:
        return "Rising Action - Late"
    elif plot_count == 7:
        return "Climax Approaching"
    else:
        return "Climax/Resolution"


def generate_next_plot_llm(previous_text):

    story_state = extract_story_state(previous_text)

    # Controlled prompt
    prompt = f"""
    Characters: {story_state['characters']}
    Continue the story maintaining consistency and escalating conflict.
    """

    generated_plot = call_llm(prompt)  # implement separately

    tension_score = evaluate_tension(generated_plot)

    return {
        "generated_plot": generated_plot,
        "tension_score": tension_score
    }
