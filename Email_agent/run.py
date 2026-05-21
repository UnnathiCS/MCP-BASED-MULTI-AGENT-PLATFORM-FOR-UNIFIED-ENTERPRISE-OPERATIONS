import uvicorn

if __name__ == "__main__":
    print("http://127.0.0.1:8004/")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8004, reload=True)
