#!/bin/bash

echo "============================================================"
echo "Fetching Metrics from FastAPI"
echo "============================================================"
echo ""

curl -X GET "http://localhost:8000/metrics" -s | python3 -m json.tool

echo ""
echo "============================================================"
