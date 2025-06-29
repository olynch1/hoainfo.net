from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import threading
import time

# ✅ Load environment variables
load_dotenv()

# 🔐 Local imports
from src.backend.database import otp_store, init_db
from src.backend.routes import auth_routes
from src.backend.routes.auth_routes import router as auth_router
from src.backend.routes.message_routes import router as message_router
from src.backend.routes.complaint_routes import router as complaint_router
from src.backend.routes.notification_routes import router as notification_router
from src.backend.secure_routes import router as secure_router
from src.backend.core_routes import router as core_router
from src.backend.otp_routes import router as otp_router
from src.backend.legal_routes import router as legal_router

# 🌐 Initialize FastAPI app
app = FastAPI()

# 🔁 Enable CORS (open for dev — restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔒 Consider tightening this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧱 Ensure DB tables are created on startup
@app.on_event("startup")
def startup():
    init_db()

# 🧼 Background thread to clean up expired OTPs every 60 seconds
def cleanup_expired_otps():
    while True:
        time.sleep(60)
        now = time.time()
        expired = [email for email, (otp, ts, attempts) in otp_store.items() if now - ts > 300]
        for email in expired:
            del otp_store[email]

threading.Thread(target=cleanup_expired_otps, daemon=True).start()

# 🔗 Include all route modules
app.include_router(auth_router)
app.include_router(secure_router)
app.include_router(core_router)
app.include_router(otp_router)
app.include_router(legal_router, prefix="/api/legal")
app.include_router(message_router)
app.include_router(complaint_router)
app.include_router(notification_router)

# 📁 Mount static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

# 🏠 Serve main login page (force absolute path to avoid bugs)
@app.get("/")
def serve_index():
    path = os.path.abspath("src/frontend/index.html")
    print(f"🔥 Serving index.html from: {path}")
    return FileResponse(path)

# 📬 Serve inbox HTML
@app.get("/inbox")
def serve_inbox():
    return FileResponse(os.path.abspath("src/frontend/inbox.html"))

