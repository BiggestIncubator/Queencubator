# Filters the output of the LLM to reduce unexpected inappropriate replies

def filterer(ai_output:str) -> str:

    import re
    reply = re.sub(r'#\w+', '', ai_output).strip() # remove hashtags

    return reply