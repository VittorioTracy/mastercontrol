#!/bin/bash
# run as mcp user and capture output to a log file 
sudo su mcp -c 'nohup python mcp.py 2>&1 > log/mcp.log &'
