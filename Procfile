web: streamlit run wisdom/body/app.py --server.port=$PORT --server.address=0.0.0.0
api: uvicorn wisdom.body.api:app --host 0.0.0.0 --port=${API_PORT:-8000}
