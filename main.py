import os
import openai
import prompt_engineering as pe # from prompt_engineering.py
from dotenv import load_dotenv
from collections import deque
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes, 
    filters
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    ############### Direct Messages ################
    if update.message.chat.type == 'private': # 'private' chats are Direct Messages from users
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
    
    
    ############### Group Chats ################
    elif update.message.chat.type in ['group', 'supergroup']: # for group chats
        message_text = update.message.text
        
        # only reply to longer messages because they are likely to be more serious
        # but if it contains 'my queen', still reply to it
        if len(message_text) < 69:
            if message_text[:8].lower() != 'my queen':
                return

        user_name = update.message.from_user.username
        
        chat_id = update.message.chat_id

        # Store messages in a deque with a maximum length of 21
        if 'messages' not in context.chat_data:
            context.chat_data['messages'] = deque(maxlen=21)

        context.chat_data['messages'].append(f'@{user_name}: {message_text}')
        chat_history = '\n'.join(context.chat_data.get('messages', []))


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
        print(f'AI REPLY: {message_text}')


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