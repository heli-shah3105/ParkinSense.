"""
=============================================================================
Dysarthric Lexicon & Language Decoder (Pure Python — Zero C++ Dependency)
=============================================================================
Provides clinical vocabulary-constrained decoding, phonetic error correction,
and language modeling for dysarthric speech recognition.

People with dysarthria frequently exhibit:
  - Incomplete consonant articulation (e.g. "cmpter" -> "computer", "bacspas" -> "backspace")
  - Vowel reduction / centralizations (e.g. "papir" -> "paper")
  - Fricative-to-stop substitutions (e.g. "dat" -> "that", "wit" -> "with")
  - Final consonant deletion (e.g. "escap" -> "escape")

This module uses a clinical lexicon (UASpeech + TORGO) plus high-frequency English
vocabulary to snap distorted CTC acoustic outputs to legitimate words with zero
need for external C++ compilers (like KenLM or pyctcdecode).
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple

from config import UASPEECH_WORDS, MANIFEST_DIR


def damerau_levenshtein(s1: str, s2: str) -> int:
    """Calculate the Damerau-Levenshtein distance between two strings."""
    d = {}
    len1 = len(s1)
    len2 = len(s2)
    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,        # deletion
                d[(i, j - 1)] + 1,        # insertion
                d[(i - 1, j - 1)] + cost  # substitution
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + 1)  # transposition

    return d[(len1 - 1, len2 - 1)]


# Standard high-frequency vocabulary for daily & clinical interaction
CORE_ENGLISH_WORDS = {
    # Pronouns & determiners
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "this", "that", "these", "those",
    "a", "an", "the", "some", "any", "no", "every", "all", "each", "both", "few",
    "many", "much", "more", "most", "other", "another", "such", "what", "which", "who",
    # Verbs (Auxiliary, Modal, Common)
    "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "doing", "done", "go", "goes", "went", "gone", "going",
    "come", "came", "coming", "see", "saw", "seen", "seeing", "say", "said", "saying",
    "get", "got", "getting", "make", "made", "making", "know", "knew", "known", "knowing",
    "think", "thought", "thinking", "take", "took", "taken", "taking", "want", "wanted",
    "wanting", "need", "needed", "needing", "help", "helped", "helping", "feel", "felt",
    "feeling", "hear", "heard", "hearing", "look", "looked", "looking", "stop", "stopped",
    "stopping", "start", "started", "starting", "open", "opened", "opening", "close", "closed",
    "closing", "speak", "spoke", "spoken", "speaking", "talk", "talked", "talking", "call",
    "called", "calling", "eat", "ate", "eaten", "eating", "drink", "drank", "drunk", "drinking",
    "sleep", "slept", "sleeping", "sit", "sat", "sitting", "stand", "stood", "standing",
    "walk", "walked", "walking", "move", "moved", "moving", "turn", "turned", "turning",
    "show", "showed", "showing", "tell", "told", "telling", "ask", "asked", "asking",
    "try", "tried", "trying", "leave", "left", "leaving", "keep", "kept", "keeping",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "test", "testing", "tested", "record", "recording", "recorded", "listen", "listening",
    "check", "checking", "checked", "work", "working", "worked", "translate", "transcribe",
    "transcription", "transcribing", "read", "reading", "write", "writing", "written",
    # Prepositions & conjunctions
    "in", "on", "at", "to", "for", "with", "from", "by", "about", "into", "through",
    "after", "before", "between", "under", "over", "above", "below", "up", "down",
    "out", "off", "of", "and", "but", "or", "so", "if", "because", "as", "than",
    "when", "where", "why", "how", "while", "though", "although", "since", "until",
    # Tech, Speech & Testing Words
    "mic", "microphone", "audio", "sound", "voice", "speech", "text", "words", "sentence",
    "language", "system", "program", "computer", "model", "phone", "device", "screen",
    "volume", "clear", "clearly", "loud", "quiet", "fast", "slow", "speed", "accuracy",
    "real", "time", "life", "delay", "lag", "seconds", "minute", "hour", "project", "demo",
    # Everyday / Clinical / Needs
    "yes", "yeah", "yep", "no", "nope", "nah", "please", "thanks", "thank", "welcome",
    "hello", "hi", "hey", "goodbye", "bye", "okay", "ok", "fine", "good", "great", "well",
    "bad", "water", "food", "medicine", "doctor", "nurse", "hospital", "bed", "chair",
    "pain", "hurts", "cold", "hot", "warm", "tired", "sleepy", "hungry", "thirsty",
    "light", "door", "window", "room", "glasses", "teeth", "head", "hand", "arm", "leg",
    "foot", "feet", "back", "chest", "stomach", "throat", "mouth", "nose", "eye", "eyes",
    "today", "tomorrow", "yesterday", "now", "later", "soon", "morning", "afternoon", "night",
    "evening", "ready", "very", "too", "quite", "really", "almost", "always", "never",
    "sometimes", "often", "here", "there", "everywhere", "somewhere", "anywhere",
    # Numbers
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "first", "second", "third",
    # Grandfather passage
    "grandfather", "old", "nearly", "ninety-three", "years", "yet", "still", "thinks",
    "swiftly", "young", "man", "long", "flowing", "beard", "clings", "chin", "gives",
    "face", "picturesque", "aspect", "speaks", "quivers", "bit", "twice", "day", "plays",
    "violin", "little", "tune", "except", "rare", "occasions", "asks", "coat", "several",
    "tattered", "patches", "frock", "grand", "style",
}

# Known phonological distortions common in dysarthric Parkinsonian speech
DYSARTHRIC_DISTORTIONS = {
    "cmpter": "computer",
    "compter": "computer",
    "cumputer": "computer",
    "bacspas": "backspace",
    "bakspas": "backspace",
    "bakspace": "backspace",
    "escap": "escape",
    "ekap": "escape",
    "capsloc": "caps lock",
    "numloc": "num lock",
    "scroloc": "scroll lock",
    "pagedun": "page down",
    "pagup": "page up",
    "prntscrn": "print screen",
    "dat": "that",
    "dis": "this",
    "dem": "them",
    "der": "there",
    "dey": "they",
    "wit": "with",
    "wif": "with",
    "frockcot": "frock coat",
    "frockoat": "frock coat",
    "granfather": "grandfather",
    "granp": "grandfather",
}

# Multi-word standard computer / assessment phrases
MULTI_WORD_PHRASES = [
    "page up", "page down", "caps lock", "num lock", "scroll lock",
    "print screen", "frock coat", "ninety three", "young man",
    "story starters", "thank you", "good morning", "good night",
    "how are you", "speech to text",
]


class DysarthricLexiconDecoder:
    """
    Intelligent language and lexicon rescorer tailored for dysarthric speech.
    Provides fast phoneme error correction and vocabulary matching without
    mutilating ordinary English conversational words.
    """

    def __init__(self):
        self.vocabulary: Set[str] = set()
        self.word_frequencies: Dict[str, float] = {}
        self.multi_word_phrases: List[str] = MULTI_WORD_PHRASES.copy()

        self._build_lexicon()

    def _build_lexicon(self):
        """Assemble all clinical UASpeech, TORGO, and common English words."""
        # 1. Add all UASpeech words from config
        for word in UASPEECH_WORDS.values():
            w = word.strip().lower()
            if " " in w:
                self.multi_word_phrases.append(w)
                for part in w.split():
                    self._add_word(part, weight=10.0)
            else:
                self._add_word(w, weight=10.0)

        # 2. Add Core English Words
        for w in CORE_ENGLISH_WORDS:
            self._add_word(w, weight=5.0)

        # 3. Harvest from split_manifest.csv if available
        manifest_file = os.path.join(MANIFEST_DIR, "split_manifest.csv")
        if os.path.exists(manifest_file):
            try:
                import pandas as pd
                df = pd.read_csv(manifest_file)
                for transcript in df["transcript"].dropna():
                    clean = re.sub(r"[^a-zA-Z\s']", "", str(transcript).lower()).strip()
                    for tok in clean.split():
                        if len(tok) >= 1:
                            self._add_word(tok, weight=8.0)
            except Exception:
                pass

    def _add_word(self, word: str, weight: float = 1.0):
        w = word.strip().lower()
        if w:
            self.vocabulary.add(w)
            self.word_frequencies[w] = self.word_frequencies.get(w, 0.0) + weight

    def correct_word(self, raw_token: str, confidence: float = 1.0) -> str:
        """
        Intelligently correct a single token:
        1. If already in vocabulary, preserve it.
        2. If a known dysarthric distortion, map it.
        3. If acoustic model confidence >= 0.70, trust the acoustic prediction.
        4. If confidence is low, search for close phonetic match within edit distance.
        """
        token = raw_token.strip().lower()
        if not token:
            return token

        # Exact vocabulary match -> preserve directly
        if token in self.vocabulary:
            return token

        # Known dysarthric phoneme distortion pattern
        if token in DYSARTHRIC_DISTORTIONS:
            return DYSARTHRIC_DISTORTIONS[token]

        # If acoustic model is confident in what it heard, do not override
        if confidence >= 0.70:
            return token

        # Single/two char tokens should not be aggressively rewritten
        if len(token) <= 2:
            return token

        max_dist = 1 if len(token) <= 4 else 2

        best_candidate = token
        best_score = float("inf")

        for candidate in self.vocabulary:
            if abs(len(candidate) - len(token)) > max_dist:
                continue

            first_match = (candidate[0] == token[0])
            dist = damerau_levenshtein(token, candidate)

            if dist <= max_dist:
                freq_weight = 1.0 / (1.0 + 0.1 * self.word_frequencies.get(candidate, 1.0))
                letter_penalty = 0.0 if first_match else 0.5
                vowel_omit_bonus = -0.3 if set(token).issubset(set(candidate)) else 0.0
                score = dist + letter_penalty + vowel_omit_bonus + freq_weight

                if score < best_score:
                    best_score = score
                    best_candidate = candidate

        # Only accept correction if phonetic score is convincingly high
        if best_score <= 1.3:
            return best_candidate

        return token

    def decode_text(self, text: str) -> str:
        """
        Rescore and correct an entire transcription string.
        Resolves multi-word phrases and individual word distortions.
        """
        if not text:
            return ""

        clean_text = text.strip().lower()

        # 1. Multi-word phrase matching
        for phrase in sorted(self.multi_word_phrases, key=len, reverse=True):
            pattern = re.escape(phrase)
            if re.search(r"\b" + pattern + r"\b", clean_text):
                continue

            words_in_phrase = phrase.split()
            tokens = clean_text.split()
            if len(tokens) == len(words_in_phrase):
                dist = sum(damerau_levenshtein(t, w) for t, w in zip(tokens, words_in_phrase))
                if dist <= 2:
                    return phrase

        # 2. Token-by-token correction
        tokens = clean_text.split()
        corrected_tokens = [self.correct_word(tok, confidence=0.6) for tok in tokens]

        # 3. Post-pass for consecutive tokens matching a multi-word phrase
        merged_str = " ".join(corrected_tokens)
        for phrase in self.multi_word_phrases:
            phrase_nospace = phrase.replace(" ", "")
            if merged_str.replace(" ", "") == phrase_nospace:
                return phrase

        return " ".join(corrected_tokens)

    def decode_word_timestamps(self, words: List[Dict]) -> List[Dict]:
        """
        Apply lexicon correction to word timestamp dictionaries.
        Preserves word start_time and end_time while gently correcting distortions.
        """
        if not words:
            return []

        corrected_words = []
        for item in words:
            raw_w = item.get("word", "")
            conf = float(item.get("confidence", 0.5))
            corr_w = self.correct_word(raw_w, confidence=conf)
            boost = 1.05 if corr_w != raw_w else 1.0
            corrected_words.append({
                "word": corr_w,
                "start_time": item.get("start_time", 0.0),
                "end_time": item.get("end_time", 0.0),
                "confidence": min(1.0, round(conf * boost, 3)),
            })
        return corrected_words
