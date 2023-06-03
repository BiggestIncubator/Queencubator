import re

# i think only filterer should be different for each bot, the rest should be the same
def filterer(ai_output:str) -> str:
    ai_output = ai_output.lower()
    if 'true' in ai_output and 'false' not in ai_output:
        reply = 'True'
    else:
        reply = 'False'
    return reply


def markdownv2_to_raw(text:str) -> str:
    """
    Removes some MarkdownV2 syntax from the LLM output so we can add our own later.
    """
    
    # Remove escape characters
    text = re.sub(r"\\([*_{}\[\]()#+-`!|>])", r"\1", text)

    # Remove hyperlinks
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)

    # # Remove inline code
    # text = re.sub(r"`(.*?)`", r"\1", text)

    # # Remove bold, italic, underline, and strikethrough formatting
    # text = re.sub(r"[*_~]{1,3}", "", text)

    print(f'after markdownv2_to_raw(): {text}')
    return text


def escape_markdown_v2(text:str) -> str:
    """
    Escapes special characters in a string for use in a Telegram bot message with MarkdownV2 formatting.
    """

    special_chars = ['[', ']', '(', ')', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    escaped_chars = ['\\' + c for c in special_chars]
    for i in range(len(special_chars)):
        text = text.replace(special_chars[i], escaped_chars[i])

    
    print(f'after escape_markdown_v2(): {text}')
    return text


def add_hyperlinks(reply:str, hyperlinks:list) -> str:
    """Add hyperlinks to the text, use MarkdownV2 format: (BigLab)[https://biggestlab.io]"""
    """hyperlinks is a list of dicts, each dict has "keyword" and "url"."""

    for hyperlink in hyperlinks:
        md_link = f'[{hyperlink["keyword"]}]({hyperlink["url"]})'
        reply = reply.replace(hyperlink['keyword'], md_link)

    
    print(f'after add_hyperlinks(): {reply}')
    return reply


def postprocess(reply:str, hyperlinks:list) -> str:
    reply = filterer(reply)
    reply = markdownv2_to_raw(reply)
    reply = escape_markdown_v2(reply)
    reply = add_hyperlinks(reply, hyperlinks)
    return reply