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

Run the test using a browser runtime:
=====================================
For example:
    pytest pyodide-recipes/packages/imgui-bundle --runtime chrome -rs

Notes:
======
* This test runs correctly in Chrome.

* This test is expected to fail in Firefox Headless because:
  * Firefox Headless does not support WebGL unless a virtual display is set up.
    This might be solved by adding a step in the GitHub Actions workflow to install xvfb + GL drivers.
  * However, even with a virtual display headless there are remaining issues around requestAnimationFrame
    so the test is still expected to fail.
"""
import pytest
from pytest_pyodide import run_in_pyodide


@pytest.mark.xfail_browsers(firefox="Firefox headless does not support WebGL. Skipping this test", node="Not supported")
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
        if imgui.get_frame_count() > 3:
            done = True

    # Run the ImGui application
    # Warning, this is a non-blocking call: it will return immediately (and use requestAnimationFrame)
    hello_imgui.run(gui)

    # ---------- wait until the GUI says it's done ---------------------------
    import asyncio, time
    deadline = time.time() + 6.0      # 6-second safety net (requestAnimationFrame may run slowly in headless mode)

    async def _wait_until_done():
        while not done and time.time() < deadline:
            await asyncio.sleep(0.05)

    asyncio.run(_wait_until_done())

    # If we reach here, the loop opened and closed cleanly
    assert done
