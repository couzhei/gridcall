from fastapi import FastAPI, HTTPException, Request
from cassandra.cluster import Cluster

# from cassandra.query import SimpleStatement
from typing import List
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# import json
import uvicorn
import os
import time


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request details
        body = await request.body()  # Get the raw body of the request
        logger.info(f"Incoming request: {request.method} {request.url}")
        logger.info(f"Headers: {request.headers}")
        logger.info(f"Body: {body.decode('utf-8')}")  # Decode bytes to string

        # Call the next middleware or endpoint
        response = await call_next(request)

        return response


app = FastAPI()

cassandra_host = os.getenv("CASSANDRA_HOST", "localhost")
cassandra_port = int(os.getenv("CASSANDRA_PORT", 9042))

for i in range(3):
    try:
        # Connect to Cassandra
        cluster = Cluster([cassandra_host], port=cassandra_port)
        session = cluster.connect("my_keyspace")
        break
    except:
        time.sleep(10)
        continue


# Prepared statements
insert_stmt = session.prepare("INSERT INTO cells (x, y, json_data) VALUES (?, ?, ?)")
select_all_stmt = session.prepare("SELECT x, y, json_data FROM cells")
select_one_stmt = session.prepare("SELECT json_data FROM cells WHERE x=? AND y=?")
update_stmt = session.prepare("UPDATE cells SET json_data=? WHERE x=? AND y=?")
delete_stmt = session.prepare("DELETE FROM cells WHERE x=? AND y=?")


# Add the logging middleware
app.add_middleware(LogRequestMiddleware)


class CellData(BaseModel):
    x: str
    y: str
    json_data: str


@app.post("/cells/", response_model=CellData)
async def create_cell(cell: CellData):
    session.execute(insert_stmt, (cell.x, cell.y, cell.json_data))
    return cell


@app.get("/cells/", response_model=List[CellData])
async def read_all_cells():
    rows = session.execute(select_all_stmt)
    return [{"x": row.x, "y": row.y, "json_data": row.json_data} for row in rows]


@app.get("/cells/{x}/{y}", response_model=CellData)
async def read_cell(x: str, y: str):
    row = session.execute(select_one_stmt, (x, y)).one()
    if row:
        return {"x": x, "y": y, "json_data": row.json_data}

    raise HTTPException(
        status_code=404,
        detail="Cell not found",
    )


@app.put("/cells/{x}/{y}", response_model=CellData)
async def update_cell(x: str, y: str, cell: CellData):
    session.execute(update_stmt, (cell.json_data, x, y))

    updated_row = session.execute(select_one_stmt, (x, y)).one()
    if updated_row:
        return {"x": x, "y": y, "json_data": cell.json_data}

    raise HTTPException(status_code=404, detail="Cell not found")


@app.delete("/cells/{x}/{y}")
async def delete_cell(x: str, y: str):
    session.execute(delete_stmt, (x, y))

    row = session.execute(select_one_stmt, (x, y)).one()
    if not row:
        return {"message": f"Cell at ({x}, {y}) deleted successfully."}

    raise HTTPException(status_code=404, detail="Cell not found")


# Ensure to close the session on application shutdown
@app.on_event("shutdown")
def shutdown_event():
    session.shutdown()
    cluster.shutdown()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile_password="fuck",
        ssl_certfile="cert.pem",
        ssl_keyfile="key.pem",
        log_level="info",
        # reload=True,
        # debug=True, # not working
    )  # Add SSL parameters here if needed
