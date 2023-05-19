def prompt_builder(ai_persona:str, patient_profile:str, chat_history:str, human_input:str) -> str:
    """Build the final prompt to feed into an LLM"""

    prompt = f'{ai_persona}\n'
    prompt += f'\nPrevious Profile:\n{patient_profile}\n'
    prompt += f'\nRecent Chat History:\n{chat_history}\n'
    prompt += f'Human: {human_input}\n'
    prompt += f'AI:'

    return prompt


def chat_history_summarizer(summarizer:str, old_summary:str, new_chat_history:str) -> str:
    """Create summary for chat history to save token usage"""

    summary = f'{summarizer}\n'
    summary += f'\nPrevious Profile:\n{old_summary}\n'
    summary += f'\nRecent Chat History:\n{new_chat_history}\n'
    
    return summary