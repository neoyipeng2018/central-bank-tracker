"""Tests for the pluggable classifier backend registry."""

import pytest

from fomc_tracker.stance_classifier import (
    ClassificationResult,
    _CLASSIFIERS,
    classify_snippets,
    classify_text,
    classify_text_with_evidence,
    classifier_backend,
    disable_classifier,
    enable_classifier,
    list_classifiers,
    register_classifier,
)


def _make_result(score: float = 2.0, label: str = "Hawkish") -> ClassificationResult:
    """Helper to create a dummy ClassificationResult."""
    return ClassificationResult(
        score=score,
        label=label,
        confidence=0.9,
        hawkish_matches=["test"],
        dovish_matches=[],
        snippet_count=1,
    )


@pytest.fixture(autouse=True)
def _clean_registry():
    """Clear the classifier registry before and after each test."""
    saved = _CLASSIFIERS.copy()
    _CLASSIFIERS.clear()
    yield
    _CLASSIFIERS.clear()
    _CLASSIFIERS.extend(saved)


class TestRegisterAndList:
    def test_register_and_list(self):
        register_classifier(
            "test_backend",
            lambda text: _make_result(),
            lambda text: (_make_result(), []),
            lambda snippets: _make_result(),
        )
        items = list_classifiers()
        assert len(items) == 1
        assert items[0] == ("test_backend", True)

    def test_register_disabled(self):
        register_classifier(
            "disabled_one",
            lambda text: _make_result(),
            lambda text: (_make_result(), []),
            lambda snippets: _make_result(),
            enabled=False,
        )
        items = list_classifiers()
        assert items[0] == ("disabled_one", False)

    def test_decorator_registers_class(self):
        @classifier_backend("deco_test")
        class MyClassifier:
            @staticmethod
            def classify_text(text):
                return _make_result()

            @staticmethod
            def classify_text_with_evidence(text):
                return _make_result(), []

            @staticmethod
            def classify_snippets(snippets):
                return _make_result()

        items = list_classifiers()
        assert ("deco_test", True) in items


class TestEnableDisable:
    def test_enable_disable(self):
        register_classifier(
            "toggle_me",
            lambda text: _make_result(),
            lambda text: (_make_result(), []),
            lambda snippets: _make_result(),
        )
        assert list_classifiers()[0][1] is True

        disable_classifier("toggle_me")
        assert list_classifiers()[0][1] is False

        enable_classifier("toggle_me")
        assert list_classifiers()[0][1] is True

    def test_enable_unknown_raises(self):
        with pytest.raises(KeyError, match="No classifier named"):
            enable_classifier("nonexistent")

    def test_disable_unknown_raises(self):
        with pytest.raises(KeyError, match="No classifier named"):
            disable_classifier("nonexistent")


class TestPluginPriority:
    """Plugin classifiers should take priority over built-in backends."""

    def test_plugin_takes_priority_classify_text(self, monkeypatch):
        # Clear all LLM env vars to ensure only plugin or keyword would run
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        plugin_result = _make_result(score=3.5, label="Hawkish")
        register_classifier(
            "priority_test",
            lambda text: plugin_result,
            lambda text: (plugin_result, []),
            lambda snippets: plugin_result,
        )

        result = classify_text("some text about rate hike")
        assert result.score == 3.5
        assert result is plugin_result

    def test_plugin_takes_priority_classify_with_evidence(self, monkeypatch):
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        plugin_result = _make_result(score=-2.0, label="Dovish")
        evidence = [{"keyword": "cut rates", "direction": "dovish", "dimension": "policy", "quote": "cut rates"}]
        register_classifier(
            "evidence_test",
            lambda text: plugin_result,
            lambda text: (plugin_result, evidence),
            lambda snippets: plugin_result,
        )

        result, ev = classify_text_with_evidence("cut rates discussion")
        assert result.score == -2.0
        assert ev == evidence

    def test_plugin_takes_priority_classify_snippets(self, monkeypatch):
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        plugin_result = _make_result(score=1.0, label="Neutral")
        register_classifier(
            "snippets_test",
            lambda text: plugin_result,
            lambda text: (plugin_result, []),
            lambda snippets: plugin_result,
        )

        result = classify_snippets(["snippet one", "snippet two"])
        assert result.score == 1.0
        assert result is plugin_result

    def test_disabled_plugin_skipped(self, monkeypatch):
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        plugin_result = _make_result(score=4.0, label="Hawkish")
        register_classifier(
            "disabled_plugin",
            lambda text: plugin_result,
            lambda text: (plugin_result, []),
            lambda snippets: plugin_result,
            enabled=False,
        )

        # Should fall through to keyword, not use the disabled plugin
        result = classify_text("rate hike tighten")
        assert result is not plugin_result


class TestFallbackOnPluginFailure:
    """When a plugin raises, the router should fall through to the next option."""

    def test_fallback_to_keyword_on_plugin_error(self, monkeypatch):
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        def broken_classify(text):
            raise RuntimeError("LLM is down")

        register_classifier(
            "broken_plugin",
            broken_classify,
            lambda text: (_ for _ in ()).throw(RuntimeError("LLM is down")),
            lambda snippets: (_ for _ in ()).throw(RuntimeError("LLM is down")),
        )

        # Should fall through to keyword fallback (not raise)
        result = classify_text("raise rates tighten higher for longer")
        assert result.label == "Hawkish"
        assert result.score > 0

    def test_first_plugin_fails_second_succeeds(self, monkeypatch):
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        good_result = _make_result(score=-3.0, label="Dovish")

        register_classifier(
            "broken_first",
            lambda text: (_ for _ in ()).throw(RuntimeError("fail")),
            lambda text: (_ for _ in ()).throw(RuntimeError("fail")),
            lambda snippets: (_ for _ in ()).throw(RuntimeError("fail")),
        )
        register_classifier(
            "working_second",
            lambda text: good_result,
            lambda text: (good_result, []),
            lambda snippets: good_result,
        )

        result = classify_text("some text")
        assert result is good_result
        assert result.score == -3.0
