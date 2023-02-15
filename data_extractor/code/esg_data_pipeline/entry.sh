#!/bin/bash

date_time=$(date +'%d_%h_%Y:%H_%M')
log_file_path="/app/server_logs/extractions_logs_${date_time}.txt"
cd /app/code/esg_data_pipeline/esg_data_pipeline
python3 extraction_server.py
