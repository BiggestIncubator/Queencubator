import os
import sys
import json
import time
import openai
import random
from dotenv import load_dotenv
from telegram import Update, constants
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
        print(f'\n({os.getenv("PERSONA")})@{username}({user_id}): {human_input}')

        # load dialogue history, if none, create a blank one
        history_folder = f'memories/dialogues/{os.getenv("PERSONA")}'
        if not os.path.exists(history_folder):
            os.makedirs(history_folder)
        history_file_path = f'{history_folder}/{user_id}.md'
        if not os.path.exists(history_file_path):
            with open(history_file_path, 'w') as file:
                file.write('')
                print(f'({os.getenv("PERSONA")})SYSTEM: No history chat for the user. Creating a blank one...')
        chat_history = open(history_file_path, 'r').read()

        # load user profile, if none, create a blank one
        profile_folder = f'memories/profiles/{os.getenv("PERSONA")}'
        if not os.path.exists(profile_folder):
            os.makedirs(profile_folder)
        profile_file_path = f'{profile_folder}/{user_id}.md'
        if not os.path.exists(profile_file_path):
            with open(profile_file_path, 'w') as file:
                file.write(f'## Profile of @{username}:\n')
                print(f'({os.getenv("PERSONA")})SYSTEM: No profile for the user. Creating a blank one...')
        profile = open(profile_file_path, 'r').read()

        # load ai dialogue persona
        persona_file_path = f'personae/{os.getenv("PERSONA")}/dialogue.md'
        ai_persona = open(persona_file_path, 'r').read()

        # build the prompt for llm
        prompt = f'{ai_persona}\n'
        prompt += f'\nProfile:\n{profile}\n'
        prompt += f'\nRecent Chat:\n{chat_history}\n'
        prompt += f'Human: {human_input}\n'
        prompt += f'AI:'

        # feed prompt to openai api llm
        openai.api_key = os.getenv('OPENAI_API_KEY')
        # retry multiple times because the API is unstable
        max_retries = 10
        retries = 0
        while retries < max_retries:
            try:
                completion = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo', 
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=1,
                    max_tokens=None,
                    request_timeout=60
                    )
                reply_text = completion['choices'][0]['message']['content']
                break
            except:
                print(f'({os.getenv("PERSONA")})SYSTEM: Failed to call OpenAI API! Retrying in 3 seconds...')
                time.sleep(3)
        if retries == max_retries:
            print(f'({os.getenv("PERSONA")})SYSTEM: Max retries exceeded. Giving up.')
            reply_text = open(f'personae/{os.getenv("PERSONA")}/busy_text.md', 'r').read()

        # print raw output before filtering them
        print(f'({os.getenv("PERSONA")})LLM RAW OUTPUT: {reply_text}')

        # load persona metadata
        metadata = json.loads(open(f'personae/{os.getenv("PERSONA")}/metadata.json', 'r').read())
        
        # filter the reply text so that it complies to our intended reply format
        # (because llm outputs are unreliable)
        sys.path.append(f'personae/{os.getenv("PERSONA")}')
        from postprocess import postprocess # import the filterer.py file from the persona's folder
        hyperlinks = metadata['hyperlinks'] # extract hyperlinks from metadata to feed into postproccess
        reply_text = postprocess(reply_text, hyperlinks)

        ### send reply back to user on telegram ###
        # we're using Markdownv2. some characters must be escaped before we send them!!!
        await update.message.reply_text(
            text=reply_text,
            parse_mode=constants.ParseMode.MARKDOWN_V2, # notice that we're use MarkdownV2
            disable_web_page_preview=True # don't show link previews
            )
        print(f'({os.getenv("PERSONA")})REPLY: {reply_text}')

        # save new chat history
        with open(history_file_path, 'a') as file:
            file.write(f'\nHuman: {human_input}\nAI: {reply_text}')

        # if chat history is too long, use llm to turn it into a summary of the user
        # but keep the latest 16 lines of the chat history
        chat_history = open(history_file_path, 'r').read()
        if len(chat_history) > 4096:
            print(f'({os.getenv("PERSONA")})SYSTEM: Chat history too long ({len(chat_history)} chrs). Summarizing new profile...')
            # load ai summarizer
            summarizer_file_path = f'personae/{os.getenv("PERSONA")}/summarizer.md'
            summarizer = open(summarizer_file_path, 'r').read()

            # build summarizer prompt for llm
            summarizer_prompt = f'{summarizer}\n'
            summarizer_prompt += f'\nPrevious Profile:\n{profile}\n'
            summarizer_prompt += f'\nRecent Chat History:\n{new_chat_history}\n'

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
                print(f'({os.getenv("PERSONA")})SYSTEM: New profile made. Chat history pruned.')
            except:
                print(f'({os.getenv("PERSONA")})SYSTEM: Failed to summarize new profile. Will try next time.')

        
        # save full prompt for referrence. this is more of a dev tool actually
        lastprompt_folder = f'memories/lastprompts/{os.getenv("PERSONA")}'
        if not os.path.exists(lastprompt_folder):
            os.makedirs(lastprompt_folder)
        lastprompt_file_path = f'{lastprompt_folder}/dialogue.md'
        with open(lastprompt_file_path, 'w') as file:
            file.write(prompt)
    
    
    ############### Groupchats ################
    elif update.message.chat.type in ['group', 'supergroup']: # for group chats
        username = update.message.from_user.username
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        thread_id = update.message.message_thread_id # if in group topics
        message_text = update.message.text
        message_text = message_text.replace('\n', '') # remove line breaks
        if len(message_text) > 420: # if message too long, only keep first 420 chrs
            message_text = message_text[:417] + '...'
        print(f'\n({os.getenv("PERSONA")})@{username}({user_id}): {message_text}')

        # load groupchat history, if none, create a blank one
        groupchat_folder = f'memories/groupchats/{os.getenv("PERSONA")}'
        if not os.path.exists(groupchat_folder):
            os.makedirs(groupchat_folder)
        groupchat_file_path = f'{groupchat_folder}/{chat_id}.md'
        if not os.path.exists(groupchat_file_path):
            with open(groupchat_file_path, 'w') as file:
                file.write('')
                print(f'({os.getenv("PERSONA")})SYSTEM: No history chat for the user. Creating a blank one...')
        # write new message into groupchat history
        with open(groupchat_file_path, 'a') as file:
            file.write(f'\n@{username}: {message_text}')
        # prune chat history to the latest 21 messages
        chat_history_lines = open(groupchat_file_path, 'r').read().splitlines()
        if len(chat_history_lines) > 21:
            chat_history_lines = chat_history_lines[-21:]
        chat_history = "\n".join(chat_history_lines)
        # save pruned chat history
        with open(groupchat_file_path, 'w') as file:
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
            print(f'({os.getenv("PERSONA")})SYSTEM: Bot randomly decides to reply to this message...')

        # if user message contains summon spells, reply
        for summon_spell in metadata['summon_spells']:
            if summon_spell in message_text.lower():
                print(f'({os.getenv("PERSONA")})SYSTEM: summon spell detected. Bot replying...')
                is_reply = True
                break
        
        # filter out messages not to reply to
        if is_reply != True:
            return
        
        ######## the actual reply ########

        # load ai groupchat persona
        persona_file_path = f'personae/{os.getenv("PERSONA")}/groupchat.md'
        ai_persona = open(persona_file_path, 'r').read()

        # build prompt for llm
        prompt = f'{ai_persona}\n'
        prompt += f'\nChat:\n{chat_history}\n'
        prompt += f'You:'

        # feed prompt to openai api llm
        openai.api_key = os.getenv("OPENAI_API_KEY")
        # retry multiple times because the API is unstable
        max_retries = 10
        retries = 0
        while retries < max_retries:
            try:
                completion = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo', 
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=1,
                    max_tokens=None,
                    request_timeout=60
                    )
                message_text = completion['choices'][0]['message']['content']
                break
            except:
                print(f'({os.getenv("PERSONA")})SYSTEM: Failed to call OpenAI API! Retrying in 3 seconds...')
                time.sleep(3)
        if retries == max_retries:
            print(f'({os.getenv("PERSONA")})SYSTEM: Max retries exceeded. Giving up.')
            message_text = open(f'personae/{os.getenv("PERSONA")}/busy_text.md', 'r').read()

        # print raw output before filtering them
        print(f'({os.getenv("PERSONA")})LLM RAW OUTPUT: {message_text}')

        # filter the reply text so that it complies to our intended reply format
        # (because llm outputs are unreliable)
        sys.path.append(f'personae/{os.getenv("PERSONA")}')
        from postprocess import postprocess # import the filterer.py file from the persona's folder
        hyperlinks = metadata['hyperlinks'] # extract hyperlinks from metadata to feed into postproccess
        message_text = postprocess(message_text, hyperlinks)

        ### send message to chat room ###
        # we're using Markdownv2. some characters must be escaped before we send them!!!
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=message_text, 
            parse_mode=constants.ParseMode.MARKDOWN_V2, # notice that we're use MarkdownV2
            disable_web_page_preview=True # don't show link previews
            )
        print(f'({os.getenv("PERSONA")})AI MESSAGE: {message_text}')

        # wait a while for other bots to finish updating their folders
        time.sleep(random.randint(6, 10))

        # record the reply of the bot itself in groupchat history
        # append the bot reply to every single groupchat record (because telegram restrictions)
        groupchats_folder = f'memories/groupchats' # the mother folder
        for folder in os.listdir(groupchats_folder):
            if os.path.isdir(f'{groupchats_folder}/{folder}'):
                certain_groupchat_file_path = f'{groupchats_folder}/{folder}/{chat_id}.md'
                with open(certain_groupchat_file_path, 'a') as file:
                    file.write(f'\n@{metadata["telegram_username"]}: {message_text}')


        # save full prompt for referrence. this is more of a dev tool actually
        lastprompt_folder = f'memories/lastprompts/{os.getenv("PERSONA")}'
        if not os.path.exists(lastprompt_folder):
            os.makedirs(lastprompt_folder)
        lastprompt_file_path = f'{lastprompt_folder}/groupchat.md'
        with open(lastprompt_file_path, 'w') as file:
            file.write(prompt)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = open(f'personae/{os.getenv("PERSONA")}/start_text.md', 'r').read()
    await update.message.reply_text(start_text)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = open(f'personae/{os.getenv("PERSONA")}/start_text.md', 'r').read()
    await update.message.reply_text(start_text)


def main():
    load_dotenv()
    print(f'SYSTEM: running {os.getenv("PERSONA")}...')
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help))
    app.add_handler(MessageHandler(filters.TEXT, chat))
    app.run_polling()


if __name__ == '__main__':
    main()