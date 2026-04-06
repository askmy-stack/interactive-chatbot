# CLAUDE.md

This file provides guidance for AI assistants working with this codebase.

## Repository Overview

A minimal Python-based conversational chatbot built with Streamlit and LangChain. The app provides a web UI for chatting with an OpenAI-powered assistant configured as a "comedian AI assistant". A Jupyter notebook accompanies the app with exploratory LangChain examples.

## File Structure

```
Interactive-Chatbot/
├── app.py              # Main Streamlit web application (entry point)
├── langchain.ipynb     # Exploratory notebook with LangChain patterns and examples
└── README.md           # Minimal project title only
```

No `requirements.txt`, `.gitignore`, `.env.example`, tests, or CI/CD configuration currently exist.

## Tech Stack

- **Python 3.11**
- **Streamlit** — Web UI framework; handles page layout and session state
- **LangChain** — LLM orchestration (`langchain.chat_models.ChatOpenAI`, `langchain.schema`)
- **OpenAI API** — Backend model (`gpt-3.5-turbo` via `ChatOpenAI`)
- **HuggingFace Hub** — Alternative LLM provider used in the notebook
- **python-dotenv** — Loads `OPENAI_API_KEY` from a `.env` file

## Running the App

```bash
# Install dependencies (no requirements.txt — install manually)
pip install streamlit langchain openai python-dotenv huggingface-hub

# Create .env file with required credentials
echo "OPENAI_API_KEY=your-key-here" > .env
echo "HUGGINGFACEHUB_API_TOKEN=your-token-here" >> .env

# Start the Streamlit dev server
streamlit run app.py
```

The app runs on `http://localhost:8501` by default.

## Key Conventions

- **Language:** Python only; no JavaScript or frontend build tooling
- **Naming:** snake_case for functions and variables (`get_chatmodel_response`, `flowmessages`)
- **Session state key:** `st.session_state['flowmessages']` holds the full message history as a list of LangChain message objects (`SystemMessage`, `HumanMessage`, `AIMessage`)
- **Model config:** `ChatOpenAI(temperature=0.5)` — initialized once at module scope
- **System prompt:** Defined inline as `SystemMessage(content="...")` at session state initialization

## Known Issues and Quirks

- **Logic flaw in app.py:** `get_chatmodel_response(input)` is called unconditionally on every Streamlit rerun (line 34), before the submit button is checked. This means the model is called on every keystroke. The submit button only controls whether the response is displayed, not whether it's generated.
- **Typo in system prompt:** `"Yor are a comedian AI assitant"` — "Yor" and "assitant" are misspelled (app.py:19).
- **Shadows built-in:** The variable `input` on line 33 shadows Python's built-in `input()` function.
- **No `.gitignore`:** The repo has no `.gitignore`. Never commit `.env` files or API keys.
- **No persistent storage:** Conversation history lives only in Streamlit session state and is lost on page refresh.

## LangChain Patterns (from langchain.ipynb)

The notebook demonstrates these LangChain patterns — reference it when extending functionality:

| Pattern | Description |
|---|---|
| `LLM` | Basic completion via `OpenAI(model_name="text-davinci-003")` |
| `ChatOpenAI` | Chat model with message history |
| `PromptTemplate` | Parameterized prompt construction |
| `LLMChain` | Chain a prompt template with an LLM |
| `SimpleSequentialChain` | Chain multiple `LLMChain`s sequentially (single input/output) |
| `SequentialChain` | Multi-input/output sequential chain with named variables |
| LCEL (`\|` operator) | Modern LangChain Expression Language for chain composition |
| `HuggingFaceHub` | Use HuggingFace models (e.g. `google/flan-t5-large`) as LLM backend |

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes (for app.py) | Authenticates requests to OpenAI API |
| `HUGGINGFACEHUB_API_TOKEN` | Yes (for notebook) | Authenticates requests to HuggingFace Hub |

Store these in a `.env` file at the project root. The app loads them via `load_dotenv()`.

## Development Notes

- There are no tests. When adding features, consider adding a `tests/` directory with pytest.
- There is no `requirements.txt`. If adding dependencies, create one: `pip freeze > requirements.txt`.
- The notebook (`langchain.ipynb`) is exploratory and not imported by `app.py`.
- All conversation context is managed through LangChain message objects appended to `st.session_state['flowmessages']`. To change the AI's persona, modify the `SystemMessage` content at session initialization.
