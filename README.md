# dify-client-python

Welcome to the `dify-client-python` repository! This Python package provides a convenient and powerful interface to
interact with the Dify API, enabling developers to integrate a wide range of features into their applications with ease.

## Main Features

* **Synchronous and Asynchronous Support**: The client offers both synchronous and asynchronous methods, allowing for
  flexible integration into various Python codebases and frameworks.
* **Stream and Non-stream Support**: Seamlessly work with both streaming and non-streaming endpoints of the Dify API for
  real-time and batch processing use cases.
* **Comprehensive Endpoint Coverage**: Support completion, chat, workflows, feedback, file uploads, etc., the client
  covers all available Dify API endpoints.

## Installation

Before using the `dify-client-python` client, you'll need to install it. You can easily install it using `pip`:

```bash
pip install dify-client-python
```

## Quick Start

Here's a quick example of how you can use the Dify Client to send a chat message.

```python
import uuid
from dify_client import Client, models

# Initialize the client with your API key
client = Client(
    api_key="your-api-key",
    api_base="http://localhost/v1",
)
user = str(uuid.uuid4())

# Create a blocking chat request
blocking_chat_req = models.ChatRequest(
    query="Hi, dify-client-python!",
    inputs={"city": "Beijing"},
    user=user,
    response_mode=models.ResponseMode.BLOCKING,
)

# Send the chat message
chat_response = client.chat_messages(blocking_chat_req, timeout=60.)
print(chat_response)

# Create a streaming chat request
streaming_chat_req = models.ChatRequest(
    query="Hi, dify-client-python!",
    inputs={"city": "Beijing"},
    user=user,
    response_mode=models.ResponseMode.STREAMING,
)

# Send the chat message
for chunk in client.chat_messages(streaming_chat_req, timeout=60.):
    print(chunk)
```

For asynchronous operations, use the `AsyncClient` in a similar fashion:

```python
import asyncio
import uuid

from dify_client import AsyncClient, models

# Initialize the async client with your API key
async_client = AsyncClient(
    api_key="your-api-key",
    api_base="http://localhost/v1",
)


# Define an asynchronous function to send a blocking chat message with BLOCKING ResponseMode
async def send_chat_message():
    user = str(uuid.uuid4())
    # Create a blocking chat request
    blocking_chat_req = models.ChatRequest(
        query="Hi, dify-client-python!",
        inputs={"city": "Beijing"},
        user=user,
        response_mode=models.ResponseMode.BLOCKING,
    )
    chat_response = await async_client.achat_messages(blocking_chat_req, timeout=60.)
    print(chat_response)


# Define an asynchronous function to send a chat message with STREAMING ResponseMode
async def send_chat_message_stream():
    user = str(uuid.uuid4())
    # Create a blocking chat request
    streaming_chat_req = models.ChatRequest(
        query="Hi, dify-client-python!",
        inputs={"city": "Beijing"},
        user=user,
        response_mode=models.ResponseMode.STREAMING,
    )
    async for chunk in await async_client.achat_messages(streaming_chat_req, timeout=60.):
        print(chunk)


# Run the asynchronous function
asyncio.gather(send_chat_message(), send_chat_message_stream())
```

## Documentation

For detailed information on all the functionalities and how to use each endpoint, please refer to the official Dify API
documentation. This will provide you with comprehensive guidance on request and response structures, error handling, and
other important details.

## Contributing

Contributions are welcome! If you would like to contribute to the `dify-client-python`, please feel free to make a pull
request or open an issue to discuss potential changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

```text
MIT License

Copyright (c) 2024 haoyuhu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

```

## Support

If you encounter any issues or have questions regarding the usage of this client, please reach out to the Dify Client
support team.

Happy coding! 🚀