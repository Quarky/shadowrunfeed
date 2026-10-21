#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parent
URL='https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/feed-v4.xml'
