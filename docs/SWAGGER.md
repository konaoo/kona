# Swagger UI

A static Swagger UI page is included for quick API browsing.

File:
```
docs/swagger-ui.html
```

## How to Use

1. Start the backend
2. Open the file in a browser
3. Swagger will load `docs/openapi.yaml`

If you open from local file system, some browsers may block YAML loading. Use a simple local server:

```
cd docs
python3 -m http.server 8000
```

Then open:
```
http://127.0.0.1:8000/swagger-ui.html
```
