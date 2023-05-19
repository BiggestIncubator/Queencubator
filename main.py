import os
import openai
import configs as c # from configs.py
import prompt_engineering as pe # from prompt_engineering.py
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes, 
    filters
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    username = str(update.message.from_user.username)
    
    # use telegram user id (long integer) as identifiers for chat history / context
    user_id = update.message.from_user.id

    # take telegram user dm for llm input 
    human_input = update.message.text
    print(f'\n@{username}({user_id}): {human_input}')

    # load chat history, if none, create a blank one
    history_file_path = f'history/{user_id}.md'
    if not os.path.exists(history_file_path):
        with open(history_file_path, 'w') as file:
            file.write('')
            print(f'SYSTEM: No history chat for the user. Creating a blank one...')
    with open(history_file_path, 'r') as file:
        chat_history = file.read()

    # load user profile, if none, create a blank one
    profile_file_path = f'profiles/{user_id}.md'
    if not os.path.exists(profile_file_path):
        with open(profile_file_path, 'w') as file:
            file.write('')
            print(f'SYSTEM: No profile for the user. Creating a blank one...')
    with open(profile_file_path, 'r') as file:
        profile = file.read()

    # load ai persona
    persona_file_path = f'persona_store/persona.md'
    with open(persona_file_path, 'r') as file:
        ai_persona = file.read()

    # build the prompt for llm
    prompt = pe.prompt_builder(
        ai_persona=ai_persona,
        patient_profile=profile,
        chat_history=chat_history,
        human_input=human_input
        )

    # feed prompt to openai api llm
    openai.api_key = os.getenv('OPENAI_API_KEY')
    try:
        completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo', 
            messages=[{'role': 'user', 'content': prompt}],
            temperature=1,
            max_tokens=None,
            request_timeout=60
            )
        reply_text = completion['choices'][0]['message']['content']
    except:
        reply_text = c.BUSY_TEXT
        print('SYSTEM: Failed to call OpenAI API!')

    ### send reply back to user on telegram ###
    await update.message.reply_text(f'{reply_text}')
    print(f'AI REPLY: {reply_text}')

    # save new chat history
    with open(history_file_path, 'a') as file:
        file.write(f'\nHuman: {human_input}\nAI: {reply_text}')

    # if chat history is too long, use llm to turn it into a summary of the user
    # but keep the latest 16 lines of the chat history
    with open(history_file_path, 'r') as file:
        chat_history = file.read()
    if len(chat_history) > 4096:
        print(f'SYSTEM: Chat history too long ({len(chat_history)} chrs). Summarizing new profile...')
        # load ai summarizer
        summarizer_file_path = f'persona_store/summarizer.md'
        with open(summarizer_file_path, 'r') as file:
            summarizer = file.read()
        summarizer_prompt = pe.chat_history_summarizer(
            summarizer=summarizer,
            old_summary=profile,
            new_chat_history=chat_history
            )
        try:
            summarize_completion = openai.ChatCompletion.create(
                model='gpt-3.5-turbo', 
                messages=[{'role': 'user', 'content': summarizer_prompt}],
                temperature=1,
                max_tokens=None,
                request_timeout=60
                )
            new_profile = summarize_completion['choices'][0]['message']['content']
            with open(profile_file_path, 'w') as file:
                file.write(new_profile)
            with open(history_file_path, 'w') as file:
                new_chat_history = chat_history.splitlines()[-16:]
                file.write("\n".join(new_chat_history))
            print(f'SYSTEM: New profile made. Chat history pruned.')
        except:
            print(f'SYSTEM: Failed to summarize new profile. Will try next time.')



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'{c.START_TEXT}')


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'{c.START_TEXT}')


def main():
    load_dotenv()
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(MessageHandler(filters.TEXT, chat))
    app.run_polling()


if __name__ == '__main__':
    main()