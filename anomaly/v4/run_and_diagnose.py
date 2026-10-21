#!/usr/bin/env python3
"""Build V4 while recording a reproducible error for remote review."""
import json,runpy,traceback
from pathlib import Path
from datetime import datetime,timezone
base=Path(__file__).resolve().parent
report={"checked":datetime.now(timezone.utc).isoformat(),"state":"not_run"}
try:
    runpy.run_path(str(base/"generate.py"),run_name="__main__")
    report["state"]="generated"
except BaseException as e:
    report["state"]="failed"
    report["exception"]=type(e).__name__
    report["message"]=str(e)[:1800]
    report["traceback"]=traceback.format_exc()[-3500:]
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
(base/"build-diagnostic.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
