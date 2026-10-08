import requests
import random
from typing import Optional, List
from .config import settings
from .tokenizer import tokenize

# User-Agent to avoid Wikipedia blocking
HEADERS = {
    'User-Agent': 'EndlessPedantix/1.0 (Educational Game; contact: your-email@example.com)'
}


def fetch_article_content(title: str) -> Optional[str]:
    """Fetch the content of a Wikipedia article by title using MediaWiki API."""
    lang = settings.language
    url = f"https://{lang}.wikipedia.org/w/api.php"
    
    params = {
        'action': 'query',
        'format': 'json',
        'titles': title,
        'prop': 'extracts',
        'explaintext': True,
        'exintro': True
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if page_id != '-1':  # -1 means page not found
                extract = page_data.get('extract', '')
                # Limit to first 400 words
                words = extract.split()
                if len(words) > 400:
                    extract = ' '.join(words[:400])
                return extract
        return None
    except requests.RequestException as e:
        print(f"Error fetching article {title}: {e}")
        return None


def fetch_random_article() -> Optional[tuple[str, str]]:
    """Fetch a random Wikipedia article and return (title, content) using MediaWiki API."""
    lang = settings.language
    url = f"https://{lang}.wikipedia.org/w/api.php"
    
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'random',
        'rnnamespace': 0,  # Main namespace only
        'rnlimit': 1
    }
    
    try:
        # First get a random title
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        random_pages = data.get('query', {}).get('random', [])
        if not random_pages:
            return None
        
        title = random_pages[0].get('title')
        if not title:
            return None
        
        print(f"Fetched random article: {title}")
        
        # Then fetch the content
        content = fetch_article_content(title)
        if content:
            return title, content
        return None
    except requests.RequestException as e:
        print(f"Error fetching random article: {e}")
        return None


def load_article_pool() -> List[str]:
    """Load the article pool from file."""
    lang = settings.language
    filename = f"data/article_pool_{lang}.txt"
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            articles = [line.strip() for line in f if line.strip()]
        return articles
    except FileNotFoundError:
        return []


def get_random_article_from_pool() -> Optional[tuple[str, str]]:
    """Get a random article from the local pool and fetch its content."""
    articles = load_article_pool()
    if not articles:
        return None
    
    title = random.choice(articles)
    content = fetch_article_content(title)
    
    if content:
        return title, content
    return None


def clean_article_content(content: str, max_words: int = None) -> str:
    """Clean article content by extracting text from HTML and limiting word count."""
    # Simple HTML tag removal
    import re
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text).strip()
    
    if max_words:
        words = text.split()
        text = ' '.join(words[:max_words])
    
    return text
