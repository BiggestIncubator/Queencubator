def prompt_builder(ai_persona:str, human_profile:str, chat_history:str, human_input:str) -> str:
    """Build the final prompt to feed into an LLM"""

    prompt = f'{ai_persona}\n'
    prompt += f'\nProfile:\n{human_profile}\n'
    prompt += f'\nRecent Chat:\n{chat_history}\n'
    prompt += f'Human: {human_input}\n'
    prompt += f'AI:'

    return prompt


def prompt_builder_group_chat(ai_persona:str, chat_history:str) -> str:
    """Build the final prompt to feed into an LLM"""

    prompt = f'{ai_persona}\n'
    prompt += f'\nChat:\n{chat_history}\n'
    prompt += f'You:'

    return prompt


def chat_history_summarizer(summarizer:str, old_summary:str, new_chat_history:str) -> str:
    """Create summary for chat history to save token usage"""

    summary = f'{summarizer}\n'
    summary += f'\nPrevious Profile:\n{old_summary}\n'
    summary += f'\nRecent Chat History:\n{new_chat_history}\n'
    
    return summary