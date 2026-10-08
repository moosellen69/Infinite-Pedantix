from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .game import game_manager
from .models import GuessRequest, GuessResponse, NewGameResponse, GameState

app = FastAPI(title="Endless Pedantix API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/hello")
async def hello():
    return {"message": "Hello from Endless Pedantix backend!"}


@app.post("/api/game/new", response_model=NewGameResponse)
async def new_game():
    """Start a new game round."""
    try:
        game = game_manager.create_game()
        if not game:
            raise HTTPException(status_code=500, detail="Failed to create game")
        
        # Count total words in title
        total_words = sum(1 for token in game.title_tokens if token.type == "word")
        
        return NewGameResponse(
            game_id=game.id,
            tokens=game.tokens,
            title_tokens=game.title_tokens,
            total_words=total_words
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/game/{game_id}/guess", response_model=GuessResponse)
async def make_guess(game_id: str, request: GuessRequest):
    """Submit a word guess."""
    try:
        print(f"API: Received guess '{request.guess}' for game {game_id}")
        response = game_manager.make_guess(game_id, request.guess)
        if not response:
            raise HTTPException(status_code=404, detail="Game not found or already finished")
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/game/{game_id}/giveup", response_model=GameState)
async def give_up(game_id: str):
    """Give up and reveal the article."""
    game = game_manager.give_up(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game


@app.post("/api/game/{game_id}/reveal", response_model=GameState)
async def reveal_all(game_id: str):
    """Reveal all words in the article."""
    game = game_manager.reveal_all(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game


@app.get("/api/game/{game_id}", response_model=GameState)
async def get_game(game_id: str):
    """Get current game state."""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
