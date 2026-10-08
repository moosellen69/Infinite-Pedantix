from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Token(BaseModel):
    type: str  # "word", "punctuation", "number", "space"
    content: Optional[str] = None  # Only for punctuation/numbers/space
    length: Optional[int] = None  # Only for words (character count)
    is_revealed: bool = False  # Only for words
    hint: Optional[str] = None  # Semantic hint for words
    hint_color: Optional[str] = None  # "far", "medium", "near" for proximity hints
    revealed_word: Optional[str] = None  # The actual word when revealed


class GuessHistoryItem(BaseModel):
    word: str
    occurrences: int  # Number of times this word appears in article
    color: Optional[str] = None  # far, medium, near


class GameState(BaseModel):
    id: str
    tokens: List[Token]  # Parsed article tokens
    title_tokens: List[Token]  # Parsed title tokens
    revealed_words: List[str]  # Words that have been found
    guess_history: List[GuessHistoryItem]
    is_won: bool
    is_gave_up: bool
    title: Optional[str] = None  # Only revealed on win/giveup
    wikipedia_url: Optional[str] = None  # Only revealed on win/giveup


class GuessRequest(BaseModel):
    guess: str


class GuessResponse(BaseModel):
    found: bool
    occurrences: int  # Number of occurrences found
    hint_updates: List[Dict[str, Any]]  # Token indices with new hints
    revealed_words: List[str]
    guess_history: List[GuessHistoryItem]
    is_won: bool
    tokens: Optional[List[Token]] = None  # Updated tokens
    title_tokens: Optional[List[Token]] = None  # Updated title tokens


class NewGameResponse(BaseModel):
    game_id: str
    tokens: List[Token]
    title_tokens: List[Token]
    total_words: int
