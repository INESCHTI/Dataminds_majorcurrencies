# Avec Claude API
echo "FX_LLM_PROVIDER=claude" >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
python agent_macro.py EURUSD

# Avec TokenFactory
echo "FX_LLM_PROVIDER=tokenfactory" >> .env
python agent_macro.py

# Avec Ollama local
echo "FX_LLM_PROVIDER=local" >> .env
python agent_macro.py ALL