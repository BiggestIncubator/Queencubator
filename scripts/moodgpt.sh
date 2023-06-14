#!/bin/bash

export=moodgpt
export OPENAI_API_KEY= $(grep "OPENAI" scripts/secrets/moodgpt.env)
export TELEGRAM_BOT_TOKEN= $(grep "TELEGRAM" scripts/secrets/moodgpt.env)

python3 main.py
