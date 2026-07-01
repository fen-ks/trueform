from trueform.pipeline.protect import Protector


def test_code_and_urls_survive_roundtrip():
    text = (
        "Here is code:\n```python\nprint('hi')\n```\n"
        "and inline `x = 1` plus a link https://example.com/page yes."
    )
    p = Protector()
    masked = p.mask(text)

    assert "print('hi')" not in masked
    assert "https://example.com" not in masked
    assert "`x = 1`" not in masked

    # Simulate the model rewriting the prose around the placeholders.
    edited = masked.replace("Here is code", "Check this code")
    restored = p.restore(edited)

    assert "```python\nprint('hi')\n```" in restored
    assert "`x = 1`" in restored
    assert "https://example.com/page" in restored


def test_disabling_protection_leaves_text():
    text = "call `foo()` at https://a.com"
    p = Protector(protect_code=False, protect_urls=False)
    assert p.mask(text) == text
