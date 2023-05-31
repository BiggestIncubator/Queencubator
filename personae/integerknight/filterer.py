# Filters the output of the LLM to reduce unexpected inappropriate replies

def filterer(ai_output:str) -> str:
    """Returns the first integer (includes negative int) in the string"""
    import re
    match = re.search(r'-?\d+', ai_output)
    if match:
        reply = match.group()
    else:
        reply = '-1' # returns -1 if no answer

    return reply