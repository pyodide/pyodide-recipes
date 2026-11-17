from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["openai"])
def test_openai(selenium):
    import json

    import httpx2
    from openai import OpenAI

    response = {
        "id": "chatcmpl-8uq5isFy4wOx47MRGZIbz5qa23miM",
        "object": "chat.completion",
        "created": 1708557298,
        "model": "gpt-3.5-turbo-0125",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "In the realm of code, recursion dwells,\nA mystical process, where magic swells.\nIt's a dance of functions calling themselves,\nA looping enchantment where logic delves.\n\nLike a mirror reflecting its image anew,\nRecursion mirrors code, recursive through and through.\nA function, encountering its own essence kind,\nUntil a base case breaks the bind.\n\nWith elegance and power, recursion reigns,\nUnraveling problems, breaking chains.\nIt dives deep into the heart of the task,\nUnraveling complexities, an intricate mask.\n\nSo heed the call of recursion's art,\nA looping symphony, playing its part.\nIn the grand symphony of code's design,\nRecursion weaves a pattern divine.",
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 39, "completion_tokens": 146, "total_tokens": 185},
        "system_fingerprint": "fp_cbdb91ce3f",
    }

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://api.openai.com/v1/chat/completions"
        assert json.loads(request.content)["model"] == "gpt-3.5-turbo"
        return httpx2.Response(201, json=response)

    client = OpenAI(
        api_key="sk-abcdefgh",
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair.",
            },
            {
                "role": "user",
                "content": "Compose a poem that explains the concept of recursion in programming.",
            },
        ],
    )
    lines = completion.choices[0].message.content.splitlines()[0:2]
    assert (
        "\n".join(lines)
        == "In the realm of code, recursion dwells,\nA mystical process, where magic swells."
    )
