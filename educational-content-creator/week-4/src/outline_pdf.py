"""course/mini-course-outline.md -> course/mini-course-outline.pdf (A4, brand styling) via Chromium."""
import subprocess, markdown, os
body = markdown.markdown(open("course/mini-course-outline.md").read(), extensions=["tables"])
css = """@page{size:A4;margin:16mm 16mm}body{font:10.5pt/1.5 Inter,sans-serif;color:#14213D}h1{font-size:24pt;margin:0 0 8px;color:#14213D}
h2{font-size:14pt;color:#E8590C;margin:18px 0 4px;page-break-after:avoid}table{border-collapse:collapse;width:100%;margin:10px 0;font-size:9.5pt}
td,th{border:1px solid #eadfcd;padding:5px 7px;text-align:left}th{background:#FFF8EE}code{font-family:'JetBrains Mono',monospace;font-size:9pt;background:#f4efe6;padding:1px 4px;border-radius:3px;font-variant-ligatures:none}
hr{border:0;border-top:2px solid #eadfcd;margin:16px 0}ul{margin:4px 0 8px}a{color:#2F6DB5}"""
open("build/outline.html", "w").write(f"<!doctype html><meta charset=utf-8><style>{css}</style>{body}")
js = "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.goto('file://'+process.argv[1]);await p.pdf({path:process.argv[2],format:'A4',printBackground:true});await b.close()})();"
open("build/pdf.js", "w").write(js)
subprocess.run(["node", "build/pdf.js", os.path.abspath("build/outline.html"), "course/mini-course-outline.pdf"], check=True, env={**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()})
print("pdf ok")
