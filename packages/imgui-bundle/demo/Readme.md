This folder contains a demo for Dear ImGui Bundle with Pyodide

### Usage Instructions:

#### Edit demo_imgui_bundle.html and replace the path to pyodide.js with the correct one:

```html
    <script src="dist/pyodide.js"></script>
```

#### Start a local HTTP server in this directory:
```bash
python -m http.server 8000
```

#### Open your browser 

Then navigate to http://localhost:8000/demo_imgui_bundle.html

---

#### Building imgui-bundle for Pyodide

If needed, you may build imgui-bundle package for Pyodide (and its dependencies):
```bash
pyodide build-recipes numpy Pillow typing-extensions pydantic munch future imgui-bundle --recipe-dir pyodide-recipes/packages --install
```
