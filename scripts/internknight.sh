#!/bin/bash

export PERSONA=internknight
export OPENAI_API_KEY= $(grep "OPENAI" scripts/secrets/${PERSONA}.env)
export TELEGRAM_BOT_TOKEN= $(grep "TELEGRAM" scripts/secrets/${PERSONA}.env)

python3 main.py
