
import uvicorn
from server import app as appServer
from data.config import API_PORT


if __name__ == "__main__":
    uvicorn.run(appServer, host="127.0.0.1", port=API_PORT)
