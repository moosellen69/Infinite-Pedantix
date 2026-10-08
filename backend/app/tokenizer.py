import re
from typing import List
import unicodedata
from .models import Token


def normalize_text(text: str) -> str:
    """Normalize text by removing accents and converting to lowercase."""
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')
    return text.lower()


def tokenize(text: str) -> List[str]:
    """Tokenize text into words, removing punctuation and special characters."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Replace punctuation with spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    # Split into words and filter empty strings
    words = text.split()
    return [word.lower() for word in words if word]


def extract_words_from_title(title: str) -> List[str]:
    """Extract and normalize words from an article title."""
    return tokenize(title)


def parse_text_to_tokens(text: str) -> List[Token]:
    """Parse text into tokens (words, punctuation, numbers, spaces)."""
    tokens = []
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Check for numbers
        if char.isdigit():
            start = i
            while i < len(text) and (text[i].isdigit() or text[i] == '.' or text[i] == ','):
                i += 1
            tokens.append(Token(type="number", content=text[start:i]))
            continue
        
        # Check for punctuation
        if char in '.,;:!?()"\'-–—':
            tokens.append(Token(type="punctuation", content=char))
            i += 1
            continue
        
        # Check for spaces/newlines
        if char.isspace():
            if char == '\n':
                tokens.append(Token(type="space", content='\n'))
            else:
                tokens.append(Token(type="space", content=' '))
            i += 1
            continue
        
        # It's a word - include letters and apostrophes for contractions
        start = i
        while i < len(text) and (text[i].isalpha() or text[i] == "'" or text[i] == "’"):
            i += 1
        
        if start < i:
            word = text[start:i]
            tokens.append(Token(type="word", length=len(word), is_revealed=False))
        else:
            # Skip unknown characters
            i += 1
    
    return tokens
