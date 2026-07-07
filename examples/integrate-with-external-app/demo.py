"""Minimal external-app integration demo."""

from sdk.python.ask_client import AskClient


def main() -> None:
    ask = AskClient(base_url="http://localhost:8000")
    health = ask.health()
    print(f"A.S.K. status: {health['status']} (provider: {health['provider']})")

    reply = ask.chat("What can you help me with?", session_id="demo")
    print(f"Response: {reply['response']}")

    brief = ask.morning_brief()
    print(f"Morning brief:\n{brief}")


if __name__ == "__main__":
    main()
