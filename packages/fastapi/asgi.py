from asyncio import Event, Future, Queue, create_task, ensure_future, sleep
from contextlib import contextmanager
from inspect import isawaitable

ASGI = {"spec_version": "2.0", "version": "3.0"}


background_tasks = set()


def run_in_background(coro):
    fut = ensure_future(coro)
    background_tasks.add(fut)
    fut.add_done_callback(background_tasks.discard)


@contextmanager
def acquire_js_buffer(pybuffer):
    from pyodide.ffi import create_proxy

    px = create_proxy(pybuffer)
    buf = px.getBuffer()
    px.destroy()
    try:
        yield buf.data
    finally:
        buf.release()


def request_to_scope(req):
    from js import URL

    # @app.get("/example")
    # async def example(request: Request):
    #     request.headers.get("content-type")
    # - this will error if header is not "bytes" as in ASGI spec.
    headers = [(k.lower().encode(), v.encode()) for k, v in req.headers]
    url = URL.new(req.url)
    assert url.protocol[-1] == ":"
    scheme = url.protocol[:-1]
    path = url.pathname
    assert "?".startswith(url.search[0:1])
    query_string = url.search[1:].encode()
    return {
        "asgi": ASGI,
        "headers": headers,
        "http_version": "1.1",
        "method": req.method,
        "scheme": scheme,
        "path": path,
        "query_string": query_string,
        "type": "http",
    }


async def start_application(app):
    shutdown_future = Future()

    async def shutdown():
        shutdown_future.set_result(None)
        await sleep(0)

    it = iter([{"type": "lifespan.startup"}, Future()])

    async def receive():
        res = next(it)
        if isawaitable(res):
            await res
        return res

    ready = Future()

    async def send(got):
        if got["type"] == "lifespan.startup.complete":
            ready.set_result(None)
            return
        if got["type"] == "lifespan.shutdown.complete":
            return
        raise RuntimeError(f"Unexpected lifespan event {got['type']}")

    run_in_background(
        app(
            {
                "asgi": ASGI,
                "state": {},
                "type": "lifespan",
            },
            receive,
            send,
        )
    )
    await ready
    return shutdown


async def process_request(app, req):
    from js import Object, Response

    from pyodide.ffi import create_proxy

    status = None
    headers = None
    result = Future()
    is_sse = False
    finished_response = Event()

    receive_queue = Queue()
    if req.body:
        async for data in req.body:
            await receive_queue.put(
                {
                    "body": data.to_bytes(),
                    "more_body": True,
                    "type": "http.request",
                }
            )
    await receive_queue.put({"body": b"", "more_body": False, "type": "http.request"})

    async def receive():
        message = None
        if not receive_queue.empty():
            message = await receive_queue.get()
        else:
            await finished_response.wait()
            message = {"type": "http.disconnect"}
        return message

    async def send(got):
        nonlocal status
        nonlocal headers

        if got["type"] == "http.response.start":
            status = got["status"]
            # Like above, we need to convert byte-pairs into string explicitly.
            headers = [(k.decode(), v.decode()) for k, v in got["headers"]]

        elif got["type"] == "http.response.body":
            body = got["body"]
            # Convert body to JS buffer
            px = create_proxy(body)
            buf = px.getBuffer()
            px.destroy()

            resp = Response.new(
                buf.data, headers=Object.fromEntries(headers), status=status
            )
            result.set_result(resp)
            finished_response.set()

    async def run_app():
        try:
            await app(request_to_scope(req), receive, send)

            # If we get here and no response has been set yet, the app didn't generate a response
            if not result.done():
                raise RuntimeError("The application did not generate a response")  # noqa: TRY301
        except Exception as e:
            # Handle any errors in the application
            if not result.done():
                result.set_exception(e)
                finished_response.set()

    # Create task to run the application in the background
    app_task = create_task(run_app())

    # Wait for the result (the response)
    response = await result

    await app_task
    return response


async def handle_request(app, req):
    shutdown = await start_application(app)
    result = await process_request(app, req)
    await shutdown()
    return result
