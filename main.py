import os
import json
import openai
import random
import prompt_builder # from prompt_builder.py
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
        history_file_path = f'memories/dialogues/{user_id}.md'
        if not os.path.exists(history_file_path):
            with open(history_file_path, 'w') as file:
                file.write('')
                print(f'SYSTEM: No history chat for the user. Creating a blank one...')
        chat_history = open(history_file_path, 'r').read()

        # load user profile, if none, create a blank one
        profile_file_path = f'memories/profiles/{user_id}.md'
        if not os.path.exists(profile_file_path):
            with open(profile_file_path, 'w') as file:
                file.write(f'Profile of @{username}: ')
                print(f'SYSTEM: No profile for the user. Creating a blank one...')
        profile = open(profile_file_path, 'r').read()

        # load ai persona
        persona_file_path = f'personae/{os.getenv("PERSONA")}/persona.md'
        ai_persona = open(persona_file_path, 'r').read()

        # build the prompt for llm
        prompt = prompt_builder.dialogue(
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
            reply_text = open(f'personae/{os.getenv("PERSONA")}/busy_text.md', 'r').read()
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
            summarizer_file_path = f'personae/{os.getenv("PERSONA")}/summarizer.md'
            summarizer = open(summarizer_file_path, 'r').read()
            summarizer_prompt = prompt_builder.summary(
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
        message_text = message_text.replace('\n', '') # remove line breaks
        if len(message_text) > 420: # if message too long, only keep first 420 chrs
            message_text = message_text[:417] + '...'
        print(f'\n@{username}({user_id}): {message_text}')

        # load groupchat history, if none, create a blank one
        history_file_path = f'memories/groupchats/{chat_id}.md'
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

        # load persona metadata
        metadata = json.loads(open(f'personae/{os.getenv("PERSONA")}/metadata.json', 'r').read())

        ### Decide whether to reply message ###
        is_reply = False

        # the bot has a certain chance of replying any message
        # reply frequency (integer) is mesured in basis points (0.01%)
        # thus, if reply_frequency is 420, there's a 420 / 10000 = 4.2% chance of it replying
        reply_frequency = int(metadata['reply_frequency'])
        if random.randint(1, 10000) < reply_frequency:
            is_reply = True
            print(f'SYSTEM: Bot randomly decides to reply to this message...')

        # if user message contains summon spells, reply
        for summon_spell in metadata['summon_spells']:
            if summon_spell in message_text.lower():
                print(f'SYSTEM: summon spell detected. Bot replying...')
                is_reply = True
                break
        
        # filter out messages not to reply to
        if is_reply != True:
            return
        
        ######## the actual reply ########

        # load ai persona
        persona_file_path = f'personae/{os.getenv("PERSONA")}/group_chat.md'
        ai_persona = open(persona_file_path, 'r').read()

        # build prompt for llm
        prompt = prompt_builder.groupchat(
            ai_persona=ai_persona,
            ai_id=f'@{os.getenv("TELEGRAM_USERNAME")}',
            chat_history=chat_history
        )
        # feed prompt to openai api llm
        openai.api_key = os.getenv("OPENAI_API_KEY")
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
            message_text = open(f'personae/{os.getenv("PERSONA")}/busy_text.md', 'r').read()
            print('SYSTEM: Failed to call OpenAI API!')

        ### send message to chat room ###
        await context.bot.send_message(chat_id=chat_id, text=message_text)
        print(f'AI MESSAGE: {message_text}')

        # record the reply of the bot itself in groupchat history
        with open(history_file_path, 'a') as file:
            file.write(f'\n@{metadata["telegram_username"]}: {message_text}')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = open(f'personae/{os.getenv("PERSONA")}/start_text.md', 'r').read()
    await update.message.reply_text(start_text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = open(f'personae/{os.getenv("PERSONA")}/start_text.md', 'r').read()
    await update.message.reply_text(start_text)


def main():
    load_dotenv()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(MessageHandler(filters.TEXT, chat))
    app.run_polling()


if __name__ == '__main__':
    main()