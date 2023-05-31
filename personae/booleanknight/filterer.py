# Filters the output of the LLM to reduce unexpected inappropriate replies

def filterer(ai_output:str) -> str:
    ai_output = ai_output.lower()
    if 'true' in ai_output and 'false' not in ai_output:
        reply = 'True'
    else:
        reply = 'False'
    return reply