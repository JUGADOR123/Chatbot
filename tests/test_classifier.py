from chatbot.domain.requests import Audience, Intent, Topic
from chatbot.providers.classifier import RulesClassifier


def test_rules_classifier_labels_end_user_topic() -> None:
    result = RulesClassifier().classify("How do I restore a backup?")

    assert result.intent is Intent.HELP
    assert result.topic is Topic.BACKUPS
    assert result.audience is Audience.END_USER
    assert result.is_help_request is True


def test_rules_classifier_rejects_developer_requests() -> None:
    result = RulesClassifier().classify("How do I use the amscript API?")

    assert result.intent is Intent.OTHER
    assert result.topic is Topic.DEVELOPER
    assert result.audience is Audience.DEVELOPER
    assert result.is_help_request is False


def test_rules_classifier_does_not_match_op_inside_stop() -> None:
    result = RulesClassifier().classify("How do I stop my server?")

    assert result.topic is Topic.SERVER_MANAGEMENT