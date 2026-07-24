from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

@app.get('/api/health')
def health_check():
    return {'message': 'HerWellness API is running'}

app.mount('/', StaticFiles(directory='backend/static', html=True), name='static')
