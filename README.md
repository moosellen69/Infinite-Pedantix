# Endless Pedantix

A Wikipedia guessing game inspired by Pedantix, with unlimited rounds. Guess words to reveal a hidden Wikipedia article - find all the words in the article's title to win!

## Features

- **Unlimited rounds**: No daily limit - play as much as you want
- **Semantic hints**: Planned; semantic similarity is not implemented yet
- **Multiple languages**: Supports French (default) and English
- **Responsive design**: Works on desktop and mobile
- **Dark/light themes**: Toggle between themes
- **Session stats**: Track your progress, streaks, and averages

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite, styled with Tailwind CSS
- **Backend**: Python 3.11+ with FastAPI
- **Semantic similarity**: Gensim dependency is present, but embedding-based scoring is not implemented yet
- **Wikipedia content**: Fetched via Wikipedia REST API and MediaWiki Action API
- **Persistence**: SQLite (via SQLModel) for game sessions and stats

## Project Structure

```
/
├── frontend/          # React + TypeScript + Vite app
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py           # FastAPI app and routes
│   │   ├── config.py         # Settings and configuration
│   │   ├── wikipedia.py      # Wikipedia fetching and cleaning
│   │   ├── tokenizer.py      # Tokenization and normalization
│   │   ├── similarity.py     # Embedding model and similarity scoring
│   │   ├── game.py           # Game state logic
│   │   └── models.py         # Database models
│   ├── data/
│   │   ├── article_pool_fr.txt  # French article pool
│   │   └── article_pool_en.txt  # English article pool
│   └── requirements.txt
└── README.md
```

## Setup Instructions

### Requirements

- Python 3.11 or newer
- Node.js 20.19+ or 22.12+ and npm (required by Vite 7)
- Internet access during setup to install packages and during play to fetch Wikipedia articles

### Get the Project

You can either clone the repository with Git or download it from GitHub:

```bash
git clone https://github.com/moosellen69/Infinite-Pedantix.git
cd Infinite-Pedantix
```

To download without Git, open [the GitHub repository](https://github.com/moosellen69/Infinite-Pedantix), select **Code > Download ZIP**, extract the ZIP, and open the extracted project folder in a terminal or VS Code.

### Install Dependencies

Install the backend packages in a virtual environment. From the project root:

```bash
cd backend
python -m venv .venv
```

Activate the environment, then install the pinned Python dependencies:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

```bash
python -m pip install -r requirements.txt
```

Install the frontend packages in a second terminal from the project root:

```bash
cd frontend
npm ci
```

`npm ci` installs the versions recorded in `package-lock.json`. If that lockfile is unavailable in your downloaded copy, use `npm install` instead.

**No embedding model download is needed.** The current semantic-similarity implementation is a placeholder; fastText proximity hints are not active. The app fetches Wikipedia articles online when you start a game.

### Run the App

Keep both services running in separate terminals.

In the first terminal, from the project root:

```bash
cd backend
# Activate the virtual environment if it is not already active:
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
npm run dev
```

This runs the backend's development script from `backend/package.json`. Use `npm start` to run it without auto-reload.

In the second terminal, from the project root:

```bash
cd frontend
npm run dev
```

Open the URL printed by Vite (normally `http://localhost:4173`). The backend API is at `http://localhost:8000`, with interactive documentation at `http://localhost:8000/docs`. Vite proxies the frontend's `/api` requests to the backend.

## Development Steps

1. ✅ **Scaffold both projects** - Complete
2. **Wikipedia fetching and cleaning** - Implement article fetching, cleaning, and tokenizer with unit tests
3. **Game logic with exact matching** - Implement core game mechanics, API endpoints, and in-memory state
4. **Frontend rendering** - Build the hidden article UI, guess submission, word revealing, and victory flow
5. **Semantic similarity** - Add embeddings and proximity hints
6. **Persistence** - Add SQLite database, sessions, stats, and game restoration
7. **Polish** - Add animations, themes, mobile layout, and guess history

## API Endpoints

- `POST /api/game/new` - Start a new game round
- `POST /api/game/{id}/guess` - Submit a word guess
- `POST /api/game/{id}/giveup` - Give up and reveal the article
- `GET /api/game/{id}` - Get current game state (for page reload)
- `GET /api/stats` - Get session statistics

## Configuration

Settings can be configured via environment variables or in `backend/app/config.py`:

- `LANGUAGE`: Game language (`fr` or `en`, default: `fr`)
- `EMBEDDING_MODEL_PATH`: Path to the word embedding model
- `SIMILARITY_THRESHOLD`: Minimum similarity score for proximity hints (default: 0.35)
- `MAX_ARTICLE_WORDS`: Maximum words to include from the article (default: 500)
- `AUTO_REVEAL_COMMON_WORDS`: Auto-reveal common words at start (default: false)
- `USE_LEMMATIZATION`: Enable lemmatization for better matching (default: false)
- `DATABASE_URL`: Database connection string (default: `sqlite:///./game.db`)

## License

MIT
