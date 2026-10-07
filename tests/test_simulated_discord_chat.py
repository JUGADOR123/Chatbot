import random
from pathlib import Path

from chatbot.domain.models import Message
from chatbot.domain.requests import ChatRequest
from chatbot.pipeline import HelpPipeline
from chatbot.providers.base import ProviderResponse
from chatbot.retrieval.index import DocumentIndex, Evidence


class CountingAnswerer:
    name = "test"
    model = "counting"

    def __init__(self) -> None:
        self.calls: list[tuple[tuple[Message, ...], tuple[Evidence, ...]]] = []

    def respond(self, messages, evidence):
        self.calls.append((tuple(messages), tuple(evidence)))
        return ProviderResponse(content="simulated support answer", model=self.model)


NOISE_MESSAGES = [
    "Anyone playing tonight?",
    "I just made coffee.",
    "What is your favorite movie?",
    "The update was wild yesterday.",
    "I will be back in five minutes.",
    "Does anyone know a good recipe for pasta?",
    "That screenshot is hilarious.",
    "hello everyone",
    "I found a cool song.",
    "Can somebody recommend a book?",
    "The weather is strange today.",
    "I forgot my headphones again.",
    "What time are we meeting?",
    "Nice build!",
    "I am watching a documentary.",
    "Did you see the game last night?",
    "pineapple belongs on pizza",
    "I need to finish my homework.",
    "brb",
    "That was a close one.",
    "Anyone want to play something else?",
    "I just joined the voice channel.",
    "What is the capital of France?",
    "lol",
    "My internet is slow today.",
    "Good morning!",
    "I am going shopping later.",
    "Can you send me that photo?",
    "The meeting starts soon.",
    "I like this playlist.",
    "What did everyone eat?",
    "I will test it tomorrow.",
    "That meme is perfect.",
    "Anyone seen my charger?",
    "I am tired.",
    "This conversation is chaotic.",
    "Do you prefer cats or dogs?",
    "I have to go now.",
    "The new keyboard feels great.",
    "See you later.",
    "What should we watch tonight?",
    "I am going to make tea.",
    "That was not what I expected.",
    "Can you remind me tomorrow?",
    "The package finally arrived.",
    "I need a break.",
    "Nice weather for a walk.",
    "I am reading the news.",
    "What is everyone working on?",
    "Thanks for the help earlier.",
]


SUPPORTED_QUESTIONS = [
    "How do I install auto-mcs on Windows?",
    "Downloaded the zip, what do I do next?",
    "Can auto-mcs make a server from a template?",
    "I already have a server folder; how can I import it?",
    "Is importing an mrpack modpack supported?",
    "My plugin made the server crash. What should I check?",
    "My friends cannot join from outside my network, any ideas?",
    "Where do I save a backup before changing mods?",
    "How can I restore an older server backup?",
    "Can backups be automated?",
    "How do I add someone to the whitelist?",
    "What is the easiest way to ban a player?",
    "How can I make a trusted player an operator?",
    "Where can I edit server.properties?",
    "What is the normal way to start my server?",
    "How do I stop the server safely?",
    "Can I change the server distribution later?",
    "How do I pair a remote machine with Telepath?",
    "The server crashed; where should I look first?",
    "Why will my mod not work with this Minecraft version?",
]


def test_simulated_discord_chat_answers_only_supported_questions() -> None:
    assert len(NOISE_MESSAGES) == 50
    assert len(SUPPORTED_QUESTIONS) == 20

    answerer = CountingAnswerer()
    pipeline = HelpPipeline(
        DocumentIndex.from_cache(Path("documentation/guide-cache.json")),
        answerer,
    )
    messages = [(False, message) for message in NOISE_MESSAGES]
    messages.extend((True, message) for message in SUPPORTED_QUESTIONS)
    random.Random(20261006).shuffle(messages)

    outcomes = [pipeline.handle(ChatRequest(text)) for expected, text in messages]
    answered = [outcome for outcome in outcomes if outcome.responded]

    assert len(answered) == 20
    assert len(answerer.calls) == 20
    assert all(outcome.content == "simulated support answer" for outcome in answered)
    assert all(call_evidence for _, call_evidence in answerer.calls)

    for (expected, _), outcome in zip(messages, outcomes):
        assert outcome.responded is expected