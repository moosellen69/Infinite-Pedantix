import uuid
from typing import Dict, Optional, Tuple, List
from .models import GameState, Token, GuessHistoryItem, GuessResponse
from .wikipedia import get_random_article_from_pool, clean_article_content
from .tokenizer import parse_text_to_tokens, normalize_text
from .config import settings
from difflib import SequenceMatcher


COUNTRY_NAMES = {
    'france', 'allemagne', 'espagne', 'italie', 'portugal', 'belgique', 'pays-bas', 'suisse', 'autriche',
    'suède', 'norvège', 'finlande', 'danemark', 'pologne', 'roumanie', 'hongrie', 'tchéquie', 'slovaquie',
    'grèce', 'turquie', 'islande', 'irlande', 'angleterre', 'royaume-uni', 'états-unis', 'canada', 'mexique',
    'argentine', 'brésil', 'chili', 'perou', 'colombie', 'venezuela', 'japon', 'chine', 'inde', 'inde', 'corée',
    'thailande', 'vietnam', 'indonésie', 'malaisie', 'singapour', 'australie', 'nouvelle-zélande', 'afrique',
    'maroc', 'algérie', 'tunisie', 'egypte', 'algerie', 'tunisie'
}
CATEGORY_HINTS = {
    'pays': {'country', 'nation', 'etat', 'état'},
    'ville': {'ville', 'cité', 'cite', 'capital', 'metropole'},
    'personne': {'personne', 'homme', 'femme', 'roi', 'reine', 'scientifique', 'ecrivain', 'artiste'},
    'animal': {'animal', 'chien', 'chat', 'lion', 'tigre', 'oiseau', 'poisson'},
    'couleur': {'couleur', 'bleu', 'rouge', 'vert', 'jaune', 'noir', 'blanc'},
    'date': {'date', 'annee', 'an', 'année', 'millenaire'},
    'langue': {'langue', 'francais', 'anglais', 'allemand', 'espagnol'}
}

class GameManager:
    def __init__(self):
        self.games: Dict[str, GameState] = {}
    
    def create_game(self) -> Optional[GameState]:
        """Create a new game with a random Wikipedia article."""
        try:
            article_data = get_random_article_from_pool()
            
            if article_data:
                print(f"Got article from pool: {article_data[0]}")
            else:
                print("Article pool empty, trying to fetch random article from Wikipedia")
                from .wikipedia import fetch_random_article
                article_data = fetch_random_article()
                if article_data:
                    print(f"Got article from Wikipedia: {article_data[0]}")
                else:
                    print("Wikipedia fetch returned None")
            
            # Fallback to sample content if Wikipedia fails
            if not article_data:
                print("Failed to get article from Wikipedia, using fallback")
                title = "Paris"
                content = "Paris is the capital and most populous city of France. It is located on the Seine River in northern France. The city is a major global center for art, fashion, gastronomy, and culture."
            else:
                title, content = article_data
            
            game_id = str(uuid.uuid4())
            
            print(f"Creating game {game_id} with title: {title}")
            
            # Parse title and content into tokens with word tracking
            title_tokens, title_words, title_word_token_indices = self._parse_with_words(title)
            content_tokens, content_words, content_word_token_indices = self._parse_with_words(content)
            
            # Build word index for quick lookup
            word_index = self._build_word_index(content_words)
            title_word_index = self._build_word_index(title_words)
            
            # Generate Wikipedia URL
            lang = settings.language
            wikipedia_url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
            
            game = GameState(
                id=game_id,
                tokens=content_tokens,
                title_tokens=title_tokens,
                revealed_words=[],
                guess_history=[],
                is_won=False,
                is_gave_up=False,
                title=None,  # Hidden until win/giveup
                wikipedia_url=None  # Hidden until win/giveup
            )
            
            # Store metadata separately (not sent to frontend)
            self.games[game_id] = {
                'game': game,
                'title': title,
                'wikipedia_url': wikipedia_url,
                'content_words': content_words,
                'title_words': title_words,
                'content_word_token_indices': content_word_token_indices,
                'title_word_token_indices': title_word_token_indices,
                'word_index': word_index,
                'title_word_index': title_word_index
            }
            
            return game
        except Exception as e:
            print(f"Error creating game: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_with_words(self, text: str) -> Tuple[List[Token], List[str], List[int]]:
        """Parse text into tokens and extract actual words with their token indices."""
        tokens = []
        words = []
        word_token_indices = []
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # Check for numbers - treat as hidden words
            if char.isdigit():
                start = i
                while i < len(text) and (text[i].isdigit() or text[i] == '.' or text[i] == ','):
                    i += 1
                number = text[start:i]
                tokens.append(Token(type="word", length=len(number), is_revealed=False))
                words.append(number)
                word_token_indices.append(len(tokens) - 1)
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
            
            # It's a word - include letters and apostrophes
            start = i
            while i < len(text) and (text[i].isalpha() or text[i] == "'" or text[i] == "’"):
                i += 1
            
            if start < i:
                word = text[start:i]
                tokens.append(Token(type="word", length=len(word), is_revealed=False))
                words.append(word)
                word_token_indices.append(len(tokens) - 1)
            else:
                # Skip unknown characters
                i += 1
        
        return tokens, words, word_token_indices
    
    def _build_word_index(self, words: List[str]) -> Dict[str, List[int]]:
        """Build an index mapping normalized words to their occurrence indices."""
        index = {}
        for i, word in enumerate(words):
            normalized = normalize_text(word)
            if normalized not in index:
                index[normalized] = []
            index[normalized].append(i)
        return index

    def _parse_numeric_value(self, value: str) -> Optional[int]:
        """Parse a numeric-like string such as '1840', '1,840', or '1.840' into an integer."""
        if not value:
            return None
        cleaned = value.strip().replace(' ', '').replace(',', '').replace('.', '')
        if cleaned.isdigit():
            return int(cleaned)
        return None

    def _get_hint_color(self, score: float) -> str:
        if score >= 0.8:
            return 'near'
        if score >= 0.55:
            return 'medium'
        return 'far'

    def _word_hint_score(self, guess: str, target: str) -> float:
        guess_norm = normalize_text(guess)
        target_norm = normalize_text(target)

        if not guess_norm or not target_norm:
            return 0.0

        if guess_norm == target_norm:
            return 1.0

        ratio = SequenceMatcher(None, guess_norm, target_norm).ratio()

        shared_prefix = 0.0
        min_len = min(len(guess_norm), len(target_norm))
        for i in range(min_len):
            if guess_norm[i] == target_norm[i]:
                shared_prefix += 1
            else:
                break
        shared_prefix = shared_prefix / max(1, min_len)

        length_factor = 1.0 - abs(len(guess_norm) - len(target_norm)) / max(1, max(len(guess_norm), len(target_norm)))

        guess_tokens = set(guess_norm.replace('-', ' ').split())
        target_tokens = set(target_norm.replace('-', ' ').split())
        token_overlap = len(guess_tokens & target_tokens) / max(1, len(guess_tokens | target_tokens))

        country_bonus = 0.0
        if guess_norm in COUNTRY_NAMES and target_norm in COUNTRY_NAMES:
            country_bonus = 0.5
        elif guess_norm in CATEGORY_HINTS and target_norm in COUNTRY_NAMES:
            if target_norm in CATEGORY_HINTS.get(guess_norm, set()):
                country_bonus = 0.4
        elif guess_norm in {'pays', 'country', 'nation', 'etat', 'état'} and target_norm in COUNTRY_NAMES:
            country_bonus = 0.8

        score = (ratio * 0.55) + (shared_prefix * 0.2) + (length_factor * 0.15) + (token_overlap * 0.1) + country_bonus
        return max(0.0, min(1.0, score))

    def _apply_generic_word_hints(self, game: GameState, game_data: dict, guess: str) -> List[dict]:
        """Add color-coded hints for close word guesses, not only numeric values."""
        hint_updates = []
        guess_norm = normalize_text(guess)
        if not guess_norm:
            return hint_updates

        sections = [
            ('content', game.tokens, game_data['content_words'], game_data['content_word_token_indices']),
            ('title', game.title_tokens, game_data['title_words'], game_data['title_word_token_indices'])
        ]

        for section_name, token_list, words, token_indices in sections:
            for word_idx, actual_word in enumerate(words):
                if word_idx >= len(token_indices):
                    continue
                token_idx = token_indices[word_idx]
                if token_idx >= len(token_list):
                    continue
                target_token = token_list[token_idx]
                if target_token.is_revealed:
                    continue

                if self._parse_numeric_value(actual_word) is not None:
                    continue

                score = self._word_hint_score(guess, actual_word)
                if score < 0.42:
                    continue

                current_hint = target_token.hint or ''
                current_score = self._word_hint_score(current_hint, actual_word) if current_hint else 0.0

                if current_score >= score:
                    continue

                target_token.hint = guess
                target_token.hint_color = self._get_hint_color(score)
                hint_updates.append({
                    'section': section_name,
                    'token_index': token_idx,
                    'hint': guess,
                    'actual_value': actual_word,
                    'score': score,
                    'color': target_token.hint_color
                })

        return hint_updates

    def _apply_numeric_hints(self, game: GameState, game_data: dict, guess: str) -> List[dict]:
        """If the guess is a close numeric candidate, show it as an orange hint on matching hidden numbers."""
        hint_updates = []
        guess_value = self._parse_numeric_value(guess)
        if guess_value is None:
            return hint_updates

        for section_name, token_list, words, token_indices in [
            ('content', game.tokens, game_data['content_words'], game_data['content_word_token_indices']),
            ('title', game.title_tokens, game_data['title_words'], game_data['title_word_token_indices'])
        ]:
            for word_idx, actual_word in enumerate(words):
                if word_idx >= len(token_indices):
                    continue

                token_idx = token_indices[word_idx]
                if token_idx >= len(token_list):
                    continue

                target_token = token_list[token_idx]
                if target_token.is_revealed:
                    continue

                actual_value = self._parse_numeric_value(actual_word)
                if actual_value is None:
                    continue

                distance = abs(guess_value - actual_value)
                threshold = max(10, int(actual_value * 0.08))
                if distance > threshold:
                    continue

                current_hint_value = self._parse_numeric_value(target_token.hint) if target_token.hint else None
                current_distance = abs(actual_value - current_hint_value) if current_hint_value is not None else None

                if current_hint_value is None or current_distance is None or distance < current_distance:
                    target_token.hint = str(guess_value)
                    if distance <= max(5, int(actual_value * 0.02)):
                        target_token.hint_color = 'near'
                    elif distance <= max(15, int(actual_value * 0.05)):
                        target_token.hint_color = 'medium'
                    else:
                        target_token.hint_color = 'far'
                    hint_updates.append({
                        'section': section_name,
                        'token_index': token_idx,
                        'hint': str(guess_value),
                        'actual_value': actual_value,
                        'distance': distance,
                        'color': target_token.hint_color
                    })

        return hint_updates

    def get_game(self, game_id: str) -> Optional[GameState]:
        """Get a game by ID."""
        game_data = self.games.get(game_id)
        if game_data:
            return game_data['game']
        return None
    
    def make_guess(self, game_id: str, guess: str) -> Optional[GuessResponse]:
        """Process a guess and update game state."""
        print(f"Processing guess '{guess}' for game {game_id}")
        print(f"Available games: {list(self.games.keys())}")
        game_data = self.games.get(game_id)
        if not game_data:
            print(f"Game {game_id} not found")
            return None

        game = game_data['game']
        if game.is_won or game.is_gave_up:
            print(f"Game {game_id} already finished")
            return None

        guess_normalized = normalize_text(guess)
        if not guess_normalized:
            print("Empty guess")
            return None

        if guess_normalized in game.revealed_words:
            return GuessResponse(
                found=True,
                occurrences=0,
                hint_updates=[],
                revealed_words=game.revealed_words,
                guess_history=game.guess_history,
                is_won=game.is_won
            )

        existing_guess = next((item for item in game.guess_history if normalize_text(item.word) == guess_normalized), None)
        if existing_guess is not None:
            return GuessResponse(
                found=False,
                occurrences=0,
                hint_updates=[],
                revealed_words=game.revealed_words,
                guess_history=game.guess_history,
                is_won=game.is_won,
                tokens=game.tokens,
                title_tokens=game.title_tokens
            )

        word_index = game_data['word_index']
        word_occurrences = word_index.get(guess_normalized, [])
        occurrences = len(word_occurrences)
        found = occurrences > 0
        hint_updates = []
        guess_color = 'far'

        guess_color = 'near' if found else 'far'

        if found:
            game.revealed_words.append(guess_normalized)

            content_words = game_data['content_words']
            title_words = game_data['title_words']
            content_word_token_indices = game_data['content_word_token_indices']
            title_word_token_indices = game_data['title_word_token_indices']

            for word_idx in word_occurrences:
                if word_idx < len(content_word_token_indices) and word_idx < len(content_words):
                    token_idx = content_word_token_indices[word_idx]
                    if token_idx < len(game.tokens):
                        actual_word = content_words[word_idx]
                        game.tokens[token_idx].is_revealed = True
                        game.tokens[token_idx].revealed_word = actual_word
                        game.tokens[token_idx].hint = None
                        game.tokens[token_idx].hint_color = None
                    
            title_word_index = game_data['title_word_index']
            title_occurrences = title_word_index.get(guess_normalized, [])
            for word_idx in title_occurrences:
                if word_idx < len(title_word_token_indices) and word_idx < len(title_words):
                    token_idx = title_word_token_indices[word_idx]
                    if token_idx < len(game.title_tokens):
                        actual_word = title_words[word_idx]
                        game.title_tokens[token_idx].is_revealed = True
                        game.title_tokens[token_idx].revealed_word = actual_word
                        game.title_tokens[token_idx].hint = None
                        game.title_tokens[token_idx].hint_color = None
        else:
            hint_updates = self._apply_numeric_hints(game, game_data, guess)
            if not hint_updates:
                hint_updates = self._apply_generic_word_hints(game, game_data, guess)
            if hint_updates:
                nearest_hint = min(hint_updates, key=lambda item: item.get('score', 0.0) if 'score' in item else (999 if item.get('distance') is None else item.get('distance', 999)))
                guess_color = nearest_hint.get('color', 'far')

        game.guess_history.append(GuessHistoryItem(word=guess, occurrences=occurrences, color=guess_color))

        title_word_index = game_data['title_word_index']
        title_words_revealed = sum(1 for word in title_word_index.keys() if word in game.revealed_words)
        if title_words_revealed == len(title_word_index):
            game.is_won = True
            game.title = game_data['title']
            game.wikipedia_url = game_data['wikipedia_url']

        return GuessResponse(
            found=found,
            occurrences=occurrences,
            hint_updates=hint_updates,
            revealed_words=game.revealed_words,
            guess_history=game.guess_history,
            is_won=game.is_won,
            tokens=game.tokens,
            title_tokens=game.title_tokens
        )

    def give_up(self, game_id: str) -> Optional[GameState]:
        """Player gives up and reveals the article."""
        game_data = self.games.get(game_id)
        if not game_data:
            return None

        game = game_data['game']
        game.is_gave_up = True
        game.title = game_data['title']
        game.wikipedia_url = game_data['wikipedia_url']

        # Reveal all words
        self._reveal_all_words(game, game_data)

        return game

    def reveal_all(self, game_id: str) -> Optional[GameState]:
        """Reveal all words in the article (after winning)."""
        game_data = self.games.get(game_id)
        if not game_data:
            return None

        game = game_data['game']
        self._reveal_all_words(game, game_data)

        return game

    def _reveal_all_words(self, game: GameState, game_data: dict):
        """Helper method to reveal all words in tokens."""
        content_words = game_data['content_words']
        title_words = game_data['title_words']
        content_word_token_indices = game_data['content_word_token_indices']
        title_word_token_indices = game_data['title_word_token_indices']

        for word_idx, word in enumerate(content_words):
            if word_idx < len(content_word_token_indices):
                token_idx = content_word_token_indices[word_idx]
                if token_idx < len(game.tokens):
                    game.tokens[token_idx].is_revealed = True
                    game.tokens[token_idx].revealed_word = word
                    game.tokens[token_idx].hint = None
                    game.tokens[token_idx].hint_color = None

        for word_idx, word in enumerate(title_words):
            if word_idx < len(title_word_token_indices):
                token_idx = title_word_token_indices[word_idx]
                if token_idx < len(game.title_tokens):
                    game.title_tokens[token_idx].is_revealed = True
                    game.title_tokens[token_idx].revealed_word = word
                    game.title_tokens[token_idx].hint = None
                    game.title_tokens[token_idx].hint_color = None


# Global game manager instance
game_manager = GameManager()
