# Writing Quality — Plain-Language Testing Guide

This guide is for **non-technical reviewers** who need to check whether a piece of writing sounds human or still reads like AI.

You do **not** need to understand code, APIs, or statistics. Follow the steps below.

---

## What the score means

After you run a check, you get a number from **0 to 100**.

| Score | What it means |
|------:|---------------|
| **80–100** | Sounds very human — natural rhythm and plain wording |
| **60–79** | Mostly fine — may need a light edit in a few spots |
| **40–59** | Mixed — some robotic or template-like patterns remain |
| **0–39** | Likely AI-written or very stiff and formal |

**Higher is better.** The score is a helper, not a final judgment — always read the text yourself too.

---

## How to run a check (easiest method)

1. Open a terminal in the `trueform` folder.
2. Paste this command, replacing the quoted text with your draft:

```bash
trueform score "Paste your paragraph here."
```

3. Read the **Writing Quality Report** that appears.

**From a file instead:**

```bash
trueform score --file my-draft.txt
```

**Save the report to a file:**

```bash
trueform score --file my-draft.txt -o report.txt
```

---

## What the report checks (in plain English)

### 1. Sentence rhythm
Human writing mixes short and long sentences. AI text often makes every sentence about the same length.

**Try this:** Read the text aloud. Does it sound like a person talking, or like a brochure?

### 2. Word variety
Natural writing does not repeat the same words in every sentence.

**Try this:** Skim for repeated filler words (“important,” “powerful,” “crucial”).

### 3. Natural phrasing
AI drafts often use phrases like:
- “Furthermore…”
- “Moreover…”
- “In conclusion…”
- “It is important to note…”
- “In today's fast-paced world…”
- “Leverage” / “utilize” instead of “use”

**Try this:** Highlight any of those phrases and rewrite them in plain language.

### 4. Conversational tone
People often write **don't**, **can't**, **it's** in informal content. Very formal text everywhere can feel machine-made (though formal tone is fine for legal or academic work).

---

## Manual checklist (print or copy)

Use this when reviewing any draft, with or without the tool:

- [ ] **Rhythm** — Read aloud. Does it sound like a real person?
- [ ] **Opener** — No generic “In today's fast-paced world” opening?
- [ ] **Connectors** — “Furthermore / Moreover / In conclusion” removed or rare?
- [ ] **Buzzwords** — “Leverage, utilize, robust, seamless” replaced with plain words?
- [ ] **Meaning** — The message is unchanged after editing?
- [ ] **Your voice** — Would *you* actually write it this way?

---

## Sample test cases

Use these two paragraphs to confirm the tool is working. The **human** sample should score **higher** than the **AI-style** sample.

### AI-style sample (should score low)

> In today's fast-paced world, it is important to note that we utilize technology. Furthermore, it is a powerful tool that can be leveraged. Moreover, it plays a crucial role in society. In conclusion, we must leverage it.

**Expected:** Score around **30–45**. Verdict: “Likely AI-written or very formal.”

### Human-style sample (should score high)

> Tech moves fast. Honestly? Most of it barely matters. But a few tools genuinely changed how I work, and I can't imagine going back now.

**Expected:** Score around **75–90**. Verdict: “Sounds very human.”

---

## Interactive checker (no terminal)

If someone set up the **Writing Quality Checker** canvas in Cursor, open it beside this chat. Paste any text into the box and the scores update instantly with plain-English explanations.

---

## When to humanize vs. only score

| Goal | Command |
|------|---------|
| Just check how human it sounds | `trueform score --file draft.txt` |
| Rewrite it to sound more natural | `trueform humanize --file draft.txt` |

After humanizing, run **score** again on the new version to see if it improved.

---

## Questions?

- The score is based on **patterns**, not magic — a formal legal memo may score lower even when written by a human.
- Always use your judgment. The checklist matters as much as the number.
- If results look wrong, share the text and report with whoever maintains the tool.
