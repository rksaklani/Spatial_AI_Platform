#!/bin/bash
# Start backend with the Linux venv

cd backend
/tmp/spatial_venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
