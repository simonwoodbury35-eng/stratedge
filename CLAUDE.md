# StratEdge — AI-Powered Marketing Strategist

## Project Overview
A Streamlit app that generates actionable marketing strategies for small business owners using Claude AI with live web search.

## Tech Stack
- Python 3.13
- Streamlit (UI)
- OpenAI API (gpt-4o with web_search_preview)
- SQLite (stratedge.db) for business profiles and strategy history
- python-dotenv for API key management

## Project Structure
- agent.py — Claude API calls and strategy generation logic
- app.py — Streamlit UI
- database.py — SQLite setup and queries
- stratedge.db — SQLite database
- .env — API key (never modify or read this file)

## Key Rules
- Never read or modify the .env file
- Always use the .venv virtual environment
- API key loads from .env via python-dotenv
- Always activate venv before running: source .venv/bin/activate
- Run app with: streamlit run app.py

## Current Phases
- Phase 1  — Database + memory layer
- Phase 2  — Strategy history UI
- Phase 3  — Monthly refresh mode
- Phase 4  — UI glow up