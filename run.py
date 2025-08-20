# --- MAIN ---
import uvicorn
from server import app
from bot.config import config

if __name__ == "__main__":
    # Run on custom port
    uvicorn.run(app, host="0.0.0.0", port=config.API_PORT)