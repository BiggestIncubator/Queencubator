import os
import openai
import random
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

    ############### Dialogues ################
    if update.message.chat.type == 'private': # 'private' chats are Direct Messages from users
        username = str(update.message.from_user.username)
        
        # use telegram user id (long integer) as identifiers for chat history / context
        user_id = update.message.from_user.id

        # take telegram user dm for llm input 
        human_input = update.message.text
        print(f'\n@{username}({user_id}): {human_input}')

        # load dialogue history, if none, create a blank one
        history_file_path = f'history/dialogues/{user_id}.md'
        if not os.path.exists(history_file_path):
            with open(history_file_path, 'w') as file:
                file.write('')
                print(f'SYSTEM: No history chat for the user. Creating a blank one...')
        chat_history = open(history_file_path, 'r').read()

        # load user profile, if none, create a blank one
        profile_file_path = f'profiles/{user_id}.md'
        if not os.path.exists(profile_file_path):
            with open(profile_file_path, 'w') as file:
                file.write(f'Profile of @{username}: ')
                print(f'SYSTEM: No profile for the user. Creating a blank one...')
        profile = open(profile_file_path, 'r').read()

        # load ai persona
        persona_file_path = f'prompt_store/personae/{os.getenv("PERSONA")}/persona.md'
        ai_persona = open(persona_file_path, 'r').read()

        # build the prompt for llm
        prompt = pe.prompt_builder(
            ai_persona=ai_persona,
            human_profile=profile,
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
            reply_text = open(f'prompt_store/personae/{os.getenv("PERSONA")}/busy_text.md', 'r').read()
            print('SYSTEM: Failed to call OpenAI API!')

        ### send reply back to user on telegram ###
        await update.message.reply_text(f'{reply_text}')
        print(f'AI REPLY: {reply_text}')

        # save new chat history
        with open(history_file_path, 'a') as file:
            file.write(f'\nHuman: {human_input}\nAI: {reply_text}')

        # if chat history is too long, use llm to turn it into a summary of the user
        # but keep the latest 16 lines of the chat history
        chat_history = open(history_file_path, 'r').read()
        if len(chat_history) > 4096:
            print(f'SYSTEM: Chat history too long ({len(chat_history)} chrs). Summarizing new profile...')
            # load ai summarizer
            summarizer_file_path = f'prompt_store/personae/{os.getenv("PERSONA")}/summarizer.md'
            summarizer = open(summarizer_file_path, 'r').read()
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
                new_profile = f'Profile of @{username}: ' + summarize_completion['choices'][0]['message']['content']
                with open(profile_file_path, 'w') as file:
                    file.write(new_profile)
                with open(history_file_path, 'w') as file:
                    new_chat_history = chat_history.splitlines()[-16:]
                    file.write("\n".join(new_chat_history))
                print(f'SYSTEM: New profile made. Chat history pruned.')
            except:
                print(f'SYSTEM: Failed to summarize new profile. Will try next time.')
    
    
    ############### Groupchats ################
    elif update.message.chat.type in ['group', 'supergroup']: # for group chats

        username = update.message.from_user.username
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        message_text = update.message.text
        print(f'\n@{username}({user_id}): {message_text}')

        # load groupchat history, if none, create a blank one
        history_file_path = f'history/groupchats/{user_id}.md'
        if not os.path.exists(history_file_path):
            with open(history_file_path, 'w') as file:
                file.write('')
                print(f'SYSTEM: No history chat for the user. Creating a blank one...')
        # write new message into groupchat history
        with open(history_file_path, 'a') as file:
            file.write(f'\n@{username}: {message_text}')
        # prune chat history to the latest 21 messages
        chat_history_lines = open(history_file_path, 'r').read().splitlines()
        if len(chat_history_lines) > 21:
            chat_history_lines = chat_history_lines[-21:]
        chat_history = "\n".join(chat_history_lines)
        # save pruned chat history
        with open(history_file_path, 'w') as file:
            file.write(chat_history)

        # the bot has a 1/21 chance of replying
        if random.randint(1, 21) != 1: 
            # but if it contains summon spell, still reply
            if os.getenv("SUMMON_SPELL") not in message_text.lower():
                return # abort mission
        
        ######## the actual reply ########

        # load ai persona
        persona_file_path = f'prompt_store/personae/{os.getenv("PERSONA")}/group_chat.md'
        ai_persona = open(persona_file_path, 'r').read()

        # build prompt for llm
        prompt = pe.prompt_builder_group_chat(
            ai_persona=ai_persona,
            chat_history=chat_history
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
            message_text = completion['choices'][0]['message']['content']
        except:
            message_text = open(f'prompt_store/personae/{os.getenv("PERSONA")}/busy_text.md', 'r').read()
            print('SYSTEM: Failed to call OpenAI API!')

        ### send message to chat room ###
        await context.bot.send_message(chat_id=chat_id, text=message_text)
        print(f'AI MESSAGE: {message_text}')

        # record the reply of the bot itself in groupchat history
        with open(history_file_path, 'a') as file:
            file.write(f'\n@{os.getenv("TELEGRAM_USERNAME")}: {message_text}')


async def start(update: Update):
    start_text = open(f'prompt_store/personae/{os.getenv("PERSONA")}/start_text.md', 'r').read()
    await update.message.reply_text(start_text)


async def help(update: Update):
    start_text = open(f'prompt_store/personae/{os.getenv("PERSONA")}/start_text.md', 'r').read()
    await update.message.reply_text(start_text)


def main():
    load_dotenv()
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(MessageHandler(filters.TEXT, chat))
    app.run_polling()


if __name__ == '__main__':
    main()