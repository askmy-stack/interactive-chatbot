# External App Integration Example

Minimal demos showing how to connect your app to A.S.K. in sidecar/embedded mode.

## Prerequisites

```bash
# Start the API
uvicorn backend.main:app --port 8000
```

## Python Demo

```bash
python examples/integrate-with-external-app/demo.py
```

## Node.js Demo

```bash
node examples/integrate-with-external-app/demo.js
```

## With API Key

```bash
ASK_API_KEY=my-secret uvicorn backend.main:app --port 8000

# Python
ASK_API_KEY=my-secret python -c "
from sdk.python.ask_client import AskClient
c = AskClient(api_key='my-secret')
print(c.chat('Hello'))
"
```

See `docs/integration-guide.md` for full documentation.
