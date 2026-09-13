from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, SQLModel, Session, create_engine, select
import os

# Настройка подключения к локальной базе данных SQLite
DATABASE_URL = "sqlite:///database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

class Clip(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str
    category: str
    startSeconds: int
    endSeconds: int

def init_db():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates_dir = "templates"
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

templates = Jinja2Templates(directory=templates_dir)

@app.on_event("startup")
def on_startup():
    init_db()

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    try:
        return templates.TemplateResponse(request, "index.html", {})
    except Exception as e:
        return HTMLResponse(content=f"<h3>Ошибка шаблона:</h3><pre>{str(e)}</pre>", status_code=500)

@app.post("/api/clips")
def save_clip(clip_data: Clip, session: Session = Depends(get_session)):
    session.add(clip_data)
    session.commit()
    session.refresh(clip_data)
    
    statement = select(Clip)
    total_clips = len(session.exec(statement).all())
    
    print(f"Клип сохранен в SQLite! Всего в базе: {total_clips}")
    return {"status": "success", "message": "Клип успешно сохранен в базе данных!", "total": total_clips}

@app.get("/api/clips")
def get_clips(session: Session = Depends(get_session)):
    statement = select(Clip)
    clips = session.exec(statement).all()
    return {"clips": clips}

@app.delete("/api/clips/{clip_id}")
def delete_clip(clip_id: int, session: Session = Depends(get_session)):
    clip = session.get(Clip, clip_id)
    if not clip:
        return {"status": "error", "message": "Клип не найден"}
    
    session.delete(clip)
    session.commit()
    print(f"Клип с ID {clip_id} удален из базы.")
    return {"status": "success", "message": "Клип успешно удален"}