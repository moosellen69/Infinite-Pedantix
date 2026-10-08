from typing import Optional


def get_similarity(guess: str, target_word: str) -> Optional[float]:
    """Get semantic similarity between guess and target word.
    
    For now, returns None. To implement:
    - Load word embeddings (fastText)
    - Compute cosine similarity between vectors
    - Return similarity score if above threshold
    """
    # TODO: Implement actual similarity scoring with embeddings
    return None
