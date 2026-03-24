# Worker Records

A simple Flask app for tracking worker time and pay (VUV).

## Run the app

```bash
cd /Users/ageorge/ConstructionWorkd
source venv/bin/activate
python app.py
```

Then open in your browser: **http://127.0.0.1:5000/**

## If you get "403 Forbidden" or "Access denied"

**Use an external browser.** The 403 usually comes from Cursor’s built-in browser blocking localhost.

1. Start the app with `python app.py` (see above).
2. Open **Chrome**, **Safari**, or **Firefox** (not Cursor’s preview/Simple Browser).
3. Go to: **http://127.0.0.1:5000/**

If it still fails, try **http://localhost:5000/** or disable VPN/proxy and any extensions that block localhost.
# IHS-Payslip
