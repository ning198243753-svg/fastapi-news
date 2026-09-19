from fastapi import FastAPI, Path,Query,HTTPException,Depends
from pydantic import BaseModel,Field
from fastapi.responses import HTMLResponse,FileResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession,async_sessionmaker
from sqlalchemy.orm import sessionmaker,DeclarativeBase,mapped_column,Mapped
from sqlalchemy import DateTime, func,String, select
from datetime import datetime
import time


app = FastAPI()

ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/test?charset=utf8mb4"
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True, future=True,pool_size=10, max_overflow=20)
async_session = async_sessionmaker(bind=async_engine, expire_on_commit=False,class_=AsyncSession)

async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception :
            await session.rollback()
            raise 
        finally:
            await session.close()

@app.get("/book/page")
async def get_book_page(session: AsyncSession = Depends(get_session), page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    skip= (page-1) * limit
    result = await session.execute(select(Book).offset(skip).limit(limit))
    books = result.scalars().all()   # 取所有行，返回 list[Book]
    print('books:', books)
    return books

class Bookbase(BaseModel):
    title: str

@app.post("/book/add_book")
async def add_book(book: Bookbase, session: AsyncSession = Depends(get_session)):
    new_book =Book(**book.__dict__)
    session.add(new_book)
    await session.commit()
    return {"message": "Book added successfully", "book": book}

class BookUpdate(BaseModel):
    id: int
    title: str

@app.put("/book/update_book")
async def update_book(book: BookUpdate, session: AsyncSession = Depends(get_session)):
    existing_book = await session.get(Book, book.id)
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    existing_book.title = book.title
    await session.commit()
    return {"message": "Book updated successfully", "book": existing_book}

@app.delete("/book/delete_book/{book_id}")
async def delete_book(book_id: int = Path(..., gt=0), session: AsyncSession = Depends(get_session)):
    existing_book = await session.get(Book, book_id)
    if existing_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    await session.delete(existing_book)
    await session.commit()
    return {"message": "Book deleted successfully"}

@app.get("/book/get_book/{book_id}")
async def get_book_list(session: AsyncSession = Depends(get_session), book_id: int = Path(..., gt=0)):
    # 查一本书，直接用 session.get，并且要 await
    # result = await session.execute(select(Book).where(Book.id == book_id))
    result = await session.execute(select(Book).where((Book.title.like("红%"))))
    book = result.scalars().one_or_none()   # 取一行，返回 Book 或 None
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    print('book:', book)
    return book


@app.get("/book/booklist")
async def get_book_list(session: AsyncSession = Depends(get_session)):
    # 查一本书，直接用 session.get，并且要 await
    book = await session.get(Book, 1)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    print('book:', book)
    return book

@app.get("/book/all")
async def get_all_books(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Book))
    books = result.scalars().all()   # 取所有行，返回 list[Book]
    print('books:', books)
    return books


class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(DateTime,nullable=False, default=func.now,insert_default=func.now(),comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime,nullable=False, default=func.now,insert_default=func.now(), onupdate=func.now(),comment="更新时间")

class Book(Base):
    __tablename__ = "book"
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    title: Mapped[str] = mapped_column(String(200),nullable=False,comment="书名")

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup_event():
    await create_tables()

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Request processing time: {process_time} seconds")
    print(f"Request URL: {request.url}")
    print(f"Request method: {request.method}")
    response.headers["X-Process-Time"] = str(process_time)
    return response


class User(BaseModel):
    username: str = Field(...,description="用户名")
    age: int = Field(...,description="用户年龄",gt=0)

@app.get("/")
async def root():
    return {"message": "Hello, World"}

@app.post("/register")
async def register(user: User):
    return user

@app.get("/book/{id}")
async def get_book(id: int):
    if id <= 0:
        raise HTTPException(status_code=400, detail="Invalid book ID")
    return {
        "book_id": id, "title": f"Book {id}"
        }

async def pages(skip: int = Query(..., ge=0), limit: int = Query(..., ge=0)):
    return {"skip": skip, "limit": limit}   
    


@app.get("/users/userslist")
async def get_users_list(commons=Depends(pages)):
    return commons

@app.get("/news/newslist")
async def get_news_list(commons=Depends(pages)):
    return {
        "news": f"News list with skip {commons['skip']} and limit {commons['limit']}"
    }

@app.get("/html")
async def response_html():
    return FileResponse(path="./1.txt",filename="1.txt",media_type="application/octet-stream")

class News(BaseModel):
    id:int
    title:str
    author:str

@app.get("/NewsModel/{id}",response_model=News)
async def NewsModel(id:int):
    return {
        "id":id,
        "title":"dsasd",
        "author":"djas"
    }

# @app.get("/{name}/{id}")
# async def get_name_id(
#     name: str = Path(..., min_length=2, max_length=100),
#     id: int = Path(..., gt=0, le=100),
# ):
#     return {
#         "name": name, "id": id
#     }

