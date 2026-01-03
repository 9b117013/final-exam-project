import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

app = FastAPI(
    title="名言佳句管理 API",
    description="提供名言佳句的 CRUD 操作",
    version="1.0.0"
)


class PostCreate(BaseModel):
    """新增/更新名言時的資料模型"""
    text: str
    author: str
    tags: str


class PostResponse(PostCreate):
    """回傳名言時的資料模型"""
    id: int
    model_config = ConfigDict(from_attributes=True)


def get_db_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect('quotes.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/quotes", response_model=list[PostResponse])
def get_all_quotes():
    """取得所有名言"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, text, author, tags FROM quotes")
        rows = cursor.fetchall()
        quotes = [dict(row) for row in rows]
        return quotes
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"資料庫錯誤: {e}")
    finally:
        conn.close()


@app.post("/quotes", response_model=PostResponse, status_code=201)
def create_quote(quote: PostCreate):
    """新增一則名言"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO quotes (text, author, tags) VALUES (?, ?, ?)",
            (quote.text, quote.author, quote.tags)
        )
        conn.commit()
        new_id = cursor.lastrowid
        
        return {
            "id": new_id,
            "text": quote.text,
            "author": quote.author,
            "tags": quote.tags
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"資料庫錯誤: {e}")
    finally:
        conn.close()


@app.put("/quotes/{quote_id}", response_model=PostResponse)
def update_quote(quote_id: int, quote: PostCreate):
    """更新指定的名言"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM quotes WHERE id = ?", (quote_id,))
        existing = cursor.fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        cursor.execute(
            "UPDATE quotes SET text = ?, author = ?, tags = ? WHERE id = ?",
            (quote.text, quote.author, quote.tags, quote_id)
        )
        conn.commit()
        
        return {
            "id": quote_id,
            "text": quote.text,
            "author": quote.author,
            "tags": quote.tags
        }
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"資料庫錯誤: {e}")
    finally:
        conn.close()


@app.delete("/quotes/{quote_id}")
def delete_quote(quote_id: int):
    """刪除指定的名言"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM quotes WHERE id = ?", (quote_id,))
        existing = cursor.fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        cursor.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
        conn.commit()
        
        return {"message": "Quote deleted successfully"}
    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"資料庫錯誤: {e}")
    finally:
        conn.close()