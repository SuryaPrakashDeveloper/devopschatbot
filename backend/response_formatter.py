"""
Response Formatter — DevOps Chatbot
=====================================
Post-processes LLM output to enforce structure, strip filler, and clean formatting.
Also includes query intent classifier for dynamic format template selection.

Pipeline: LLM Output → format_response() → Clean Response to User
"""

import re

# ─── QUERY INTENT CLASSIFIER ────────────────────────────────────────────────

INTENT_KEYWORDS = {
    "debugging": [
        "debug", "error", "fail", "crash", "not working", "issue", "problem",
        "broken", "stuck", "timeout", "refused", "restart", "backoff",
        "crashloopbackoff", "imagepullbackoff", "oomkilled", "pending",
        "evicted", "terminated", "killed", "unhealthy", "notready",
    ],
    "explanation": [
        "what is", "what are", "explain", "define", "difference between",
        "meaning of", "concept", "overview", "introduction", "basics",
        "tell me about", "describe",
    ],
    "howto": [
        "how to", "how do i", "setup", "configure", "install", "create",
        "deploy", "build", "run", "start", "stop", "scale", "update",
        "upgrade", "migrate", "connect", "expose", "mount",
    ],
    "log_analysis": [
        "log", "logs", "check log", "pod log", "container log",
        "show log", "view log", "analyze log", "error log",
        "application log", "service log",
    ],
    "command": [
        "command", "commands", "kubectl", "docker", "helm", "show me",
        "list", "get pods", "get nodes", "get services",
    ],
}

# Casual/conversational patterns — checked FIRST before keyword scoring
CASUAL_PATTERNS = {
    "greeting": [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
        "howdy", "sup", "what's up", "yo", "greetings",
    ],
    "appreciation": [
        "thanks", "thank you", "love you", "i love you", "appreciate",
        "awesome", "great", "cool", "nice", "good job", "well done",
        "perfect", "amazing", "brilliant", "fantastic",
    ],
    "farewell": [
        "bye", "goodbye", "see you", "later", "take care", "good night",
        "gotta go", "cya",
    ],
    "random": [
        "ok", "okay", "hmm", "lol", "haha", "hehe", "yes", "no", "sure",
        "right", "yep", "nope", "alright",
    ],
}


def classify_query(query: str) -> str:
    """
    Classify user query into intent type.
    Returns: 'casual', 'debugging', 'explanation', 'howto', 'log_analysis', 'command', or 'general'
    
    IMPORTANT: Technical keywords are ALWAYS checked first.
    Casual is only returned if there are ZERO technical keyword matches.
    This prevents "no pods running" from being classified as casual.
    """
    query_lower = query.lower().strip()
    word_count = len(query_lower.split())

    # --- STEP 1: Score technical intents FIRST (always) ---
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[intent] = score

    # If ANY technical keyword matched → return the top technical intent
    if scores:
        return max(scores, key=scores.get)

    # --- STEP 2: No technical keywords found → check casual ---
    if word_count <= 5:
        for casual_type, phrases in CASUAL_PATTERNS.items():
            for phrase in phrases:
                # Single-word casual phrases: EXACT match only (not startswith)
                if ' ' not in phrase:
                    if query_lower == phrase or query_lower == phrase + "!" or query_lower == phrase + "?":
                        return "casual"
                else:
                    # Multi-word phrases (e.g. "good morning"): exact match or starts with
                    if query_lower == phrase or query_lower.startswith(phrase + " ") or query_lower.startswith(phrase + "!"):
                        return "casual"

    # --- STEP 3: No technical, no casual → general or casual for very short ---
    if word_count <= 2:
        return "casual"  # 1-2 random words with no keyword match
    return "general"


# ─── RESPONSE FORMAT TEMPLATES (injected into prompt) ────────────────────────

FORMAT_TEMPLATES = {
    "debugging": """RESPONSE FORMAT (follow this structure exactly):

🔴 Common Issues (list most frequent first, with one-line cause):
- [IssueA] → [one-line cause]
- [IssueB] → [one-line cause]
- [IssueC] → [one-line cause]

⚡ Debug Steps (numbered, in order of execution):
1. `[command]`
2. `[command]` → [what to look for]
3. `[command]`

🧠 Quick Hints (map error messages to root causes):
- "[error message text]" → [what it means]
- "[error message text]" → [what it means]

👉 Start with: [the #1 most important first step]""",

    "explanation": """RESPONSE FORMAT (follow exactly):
[concept] — [one-line definition]

Key Points:
- [point 1]
- [point 2]
- [point 3]

Quick Example:
```[language]
[short example]
```""",

    "howto": """RESPONSE FORMAT (follow exactly):
⚡ [task name]

Steps:
1. [step with command]
2. [step with command]
3. [step with command]

Example:
```[language]
[working example]
```

🧠 Note: [one important note]""",

    "log_analysis": """RESPONSE FORMAT (follow exactly):
📋 Log Analysis: [service name]

🔴 Issues Found:
- [issue 1] ([count] occurrences)
- [issue 2] ([count] occurrences)

⚡ Debug Commands:
```bash
[relevant kubectl/docker log commands]
```

🧠 Root Cause: [brief analysis]""",

    "command": """RESPONSE FORMAT (follow exactly):
⚡ [topic] Commands:

```bash
[command 1]    # [what it does]
[command 2]    # [what it does]
[command 3]    # [what it does]
```

🧠 Most Used: [highlight the most common one]""",

    "casual": """RESPONSE FORMAT:
Respond in a friendly, warm, human-like way in 1-2 short sentences.
Then gently redirect to DevOps topics.
NEVER say 'Error' or 'Irrelevant'. Be natural and welcoming.""",

    "general": """RESPONSE FORMAT:
Answer concisely with bullet points. Include commands in code blocks if relevant.""",
}


def get_format_template(intent: str) -> str:
    """Get the response format template for the given intent."""
    return FORMAT_TEMPLATES.get(intent, FORMAT_TEMPLATES["general"])


# ─── FILLER PHRASES TO REMOVE ───────────────────────────────────────────────

FILLER_PHRASES = [
    # Opening fillers
    r"^(?:Great|Excellent|Good|Awesome|Wonderful|Fantastic) question[.!]*\s*",
    r"^Sure[,!]?\s*(?:I'd be happy to|I can|let me|I'll)\s*(?:help|explain|assist|answer)[^.]*[.!]?\s*",
    r"^(?:Of course|Absolutely|Certainly|Definitely)[,!]?\s*(?:I'd be happy to|I can|let me)?[^.]*[.!]?\s*",
    r"^(?:Let me|Allow me to)\s*(?:explain|help|assist|break\s+(?:this|that|it)\s+down)[^.]*[.!]?\s*",
    r"^(?:That's a great|That's an excellent|That's a good|What a great)\s+question[.!]*\s*",
    r"^(?:I'd be happy to|I'm glad you asked|Thanks for asking)[^.]*[.!]?\s*",
    r"^(?:Here'?s?|Here is|Here are)\s+(?:what you need to know|the (?:answer|explanation|breakdown))[^:]*:?\s*",
    # Closing fillers
    r"\n*(?:I hope this helps|Hope this helps|Hope that helps|Let me know if)[^.]*[.!]*\s*$",
    r"\n*(?:Feel free to|Don't hesitate to)\s+(?:ask|reach out|let me know)[^.]*[.!]*\s*$",
    r"\n*(?:Is there anything else|Would you like (?:me to|to know)|Do you (?:have any|need)|If you have (?:any|more))[^.]*[.!?]*\s*$",
]

# Follow-up topic patterns to remove
FOLLOWUP_PATTERNS = [
    r"\n+(?:---+\s*\n)?(?:#{1,3}\s*)?(?:Related|Follow[- ]?up|Next Steps|Further Reading|Additional|Want to (?:learn|know)|You (?:might|may) also)[^\n]*(?:\n(?:[-•*]\s*[^\n]+))*",
    r"\n+(?:📚|🔗|👉|💡)\s*(?:Related|Follow[- ]?up|Next|Further|Additional|Want to|You might)[^\n]*(?:\n(?:[-•*]\s*[^\n]+))*",
]


# ─── MAIN FORMATTER ─────────────────────────────────────────────────────────

def format_response(text: str, intent: str = "general") -> str:
    """
    Post-process LLM response to enforce quality.
    
    Operations:
    1. Casual length enforcement (if casual intent)
    2. Strip filler phrases (opening + closing)
    3. Remove follow-up topic sections
    4. Fix whitespace (excessive newlines)
    5. Fix unclosed code blocks
    6. Fix numbered list sequence
    """
    if not text or not text.strip():
        return text

    result = text

    # 0. Casual length enforcement — truncate to first sentence
    if intent == "casual":
        result = _truncate_casual(result)
        return result.strip()

    # 1. Strip filler phrases
    for pattern in FILLER_PHRASES:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.MULTILINE)

    # 2. Remove follow-up topic sections
    for pattern in FOLLOWUP_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.DOTALL)

    # 3. Fix excessive whitespace
    result = re.sub(r'\n{4,}', '\n\n\n', result)  # Max 3 newlines
    result = re.sub(r'[ \t]+\n', '\n', result)     # Trailing spaces on lines
    result = result.strip()

    # 4. Fix unclosed code blocks
    code_block_count = result.count('```')
    if code_block_count % 2 != 0:
        result += '\n```'

    # 5. Fix numbered lists (1. 1. 1. → 1. 2. 3.)
    result = _fix_numbered_lists(result)

    return result


def _truncate_casual(text: str) -> str:
    """Truncate casual responses to first 1-2 sentences max."""
    text = text.strip()
    
    # Find the end of the first sentence
    # Look for sentence-ending punctuation followed by space or end
    for i, char in enumerate(text):
        if char in '.!?' and i > 5:  # Min 5 chars to avoid matching abbreviations
            # Check if this is likely end of sentence (not abbreviation like "e.g.")
            remaining = text[i+1:].strip()
            if not remaining:  # End of text
                return text
            # If there's more text after, check if it starts a new sentence
            if remaining and (remaining[0].isupper() or remaining[0] in '😄👋🚀👍👀😅🟢⚡'):
                return text[:i+1].strip()
    
    # If no sentence break found, return as-is (but cap at 100 chars)
    if len(text) > 100:
        # Find last space before 100 chars
        last_space = text[:100].rfind(' ')
        if last_space > 20:
            return text[:last_space].strip()
    
    return text


def _fix_numbered_lists(text: str) -> str:
    """Fix repeated numbered list items (e.g., 1. 1. 1. → 1. 2. 3.)"""
    lines = text.split('\n')
    counter = 0
    in_list = False
    result_lines = []

    for line in lines:
        match = re.match(r'^(\s*)\d+\.\s+(.+)', line)
        if match:
            indent = match.group(1)
            content = match.group(2)
            if not in_list:
                counter = 1
                in_list = True
            else:
                counter += 1
            result_lines.append(f"{indent}{counter}. {content}")
        else:
            if line.strip() == '' and in_list:
                # Empty line might continue the list
                pass
            else:
                in_list = False
                counter = 0
            result_lines.append(line)

    return '\n'.join(result_lines)


def format_stream_response(full_text: str, intent: str = "general") -> str:
    """
    Format a complete streamed response.
    Same as format_response but called after all tokens are collected.
    """
    return format_response(full_text, intent=intent)


# ─── STREAMING-COMPATIBLE FORMATTERS ─────────────────────────────────────────
# These work on partial text for real-time hybrid streaming.

def strip_opening_filler(text: str) -> str:
    """
    Strip opening filler phrases from the first chunk of streamed text.
    Called once on the buffered first ~150 chars before streaming begins.
    """
    result = text
    for pattern in FILLER_PHRASES:
        # Only apply opening patterns (those starting with ^)
        if pattern.startswith(r"^") or pattern.startswith(r"\n*"):
            if pattern.startswith(r"^"):
                result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.MULTILINE)
    return result.lstrip('\n ')


def cleanup_stream_ending(full_text: str) -> tuple[str, str]:
    """
    Clean up the ending of a streamed response after all tokens are collected.
    Checks for:
    1. Trailing filler phrases ("Hope this helps", "Let me know")
    2. Follow-up topic sections
    3. Unclosed code blocks
    
    Returns: (cleaned_full_text, correction_suffix)
    - correction_suffix: empty if no fix needed, or fix tokens to send to frontend
    """
    original = full_text
    result = full_text

    # Strip closing filler phrases
    for pattern in FILLER_PHRASES:
        if "$" in pattern:  # Only closing patterns (ending with $)
            result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.MULTILINE)

    # Remove follow-up topic sections at the end
    for pattern in FOLLOWUP_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.DOTALL)

    result = result.rstrip()

    # Fix unclosed code blocks
    code_block_count = result.count('```')
    if code_block_count % 2 != 0:
        result += '\n```'

    # Calculate what was removed/added
    correction = ""
    if len(result) < len(original):
        # Content was removed from the end — we can't "un-stream" it,
        # but we note it in history. The user saw it briefly, that's OK.
        pass
    elif len(result) > len(original):
        # Content was added (e.g., closing ```) — send as extra token
        correction = result[len(original):]

    return result, correction
