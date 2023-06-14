#!/bin/bash

export=queencubator
export OPENAI_API_KEY= $(grep "OPENAI" scripts/secrets/queencubator.env)
export TELEGRAM_BOT_TOKEN= $(grep "TELEGRAM" scripts/secrets/queencubator.env)

python3 main.py
