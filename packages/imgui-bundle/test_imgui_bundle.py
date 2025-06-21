"""
Test for the Pyodide build of imgui-bundle

Steps:
======
1. Create a <canvas> element in the HTML document.
2. Use the `imgui_bundle` library to create a simple ImGui application that displays
   "Hello, ImGui inside Pyodide!" text.
3. The application runs in a non-blocking manner using `hello_imgui.run()`.
4. The test waits until the ImGui application signals that it is done rendering.
5. Finally, it asserts that the application has completed its execution.

How to run the test:
====================
- Ensure you have Pyodide and the imgui-bundle package installed.
- Run the test using a browser runtime (i.e. not using node):
        pytest pyodide-recipes/packages/imgui-bundle --runtime chrome -rs

Important note: Build configuration for Pyodide
==========================================================
In order to run correctly, the compilation flags of the Pyodide main module
need to be changed (in Makefile.envs):
MAIN_MODULE_LDFLAGS must contain the flag -sMAX_WEBGL_VERSION=2
in the section "export MAIN_MODULE_LDFLAGS=", add a line:
      -sMAX_WEBGL_VERSION=2 \

"""

from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["imgui-bundle"])
def test_imgui_bundle_window(selenium):

    # --- 1. Create / attach a <canvas id="canvas"> -------------------------
    import js
    canvas = js.document.getElementById("canvas")
    if canvas is None:
        canvas = js.document.createElement("canvas")
        canvas.id = "canvas"
        canvas.style.width = "640px"
        canvas.style.height = "480px"
        js.document.body.appendChild(canvas)

    js.pyodide.canvas.setCanvas2D(canvas)
    # opt-in flag required when using SDL2 with Pyodide
    js.pyodide._api._skip_unwind_fatal_error = True

    # --- 2. Minimal ImGui program -----------------------------------------
    from imgui_bundle import imgui, hello_imgui

    done = False

    def gui() -> None:
        nonlocal done
        imgui.text("Hello, ImGui inside Pyodide!")
        # Exit after a few frames were rendered
        if imgui.get_frame_count() > 6:       
            done = True

    # Run the ImGui application 
    # Warning, this is a non-blocking call: it will return immediately (and use requestAnimationFrame)
    hello_imgui.run(gui)

    # ---------- wait until the GUI says it's done ---------------------------
    import time
    deadline = time.time() + 3.0      # 3-second safety net
    while not done and time.time() < deadline:
        time.sleep(0.05)              # yields to JS -> lets requestAnimationFrame run

    # If we reach here the loop opened and closed cleanly
    assert done
