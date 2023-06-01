<<<<<<< HEAD
#!/bin/bash

export PERSONA=startupjesus
export OPENAI_API_KEY= $(grep "OPENAI" scripts/secrets/${PERSONA}.env)
export TELEGRAM_BOT_TOKEN= $(grep "TELEGRAM" scripts/secrets/${PERSONA}.env)

python3 main.py
=======
#!/bin/bash

export OPENAI_API_KEY=
export TELEGRAM_BOT_TOKEN=
export PERSONA=startupjesus

python3 main.py
>>>>>>> origin
