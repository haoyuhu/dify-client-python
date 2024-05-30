from typing import Optional, Any, Mapping, Iterator, AsyncIterator, Union, Dict

try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum
try:
    from http import HTTPMethod
except ImportError:
    class HTTPMethod(StrEnum):
        GET = "GET"
        POST = "POST"
        PUT = "PUT"
        DELETE = "DELETE"

import httpx
# noinspection PyProtectedMember
import httpx._types as types
from httpx_sse import connect_sse, ServerSentEvent, aconnect_sse
from pydantic import BaseModel

from dify_client import errors, models

_httpx_client = httpx.Client()
_async_httpx_client = httpx.AsyncClient()

IGNORED_STREAM_EVENTS = (models.StreamEvent.PING.value,)

# feedback
ENDPOINT_FEEDBACKS = "/messages/{message_id}/feedbacks"
# suggest
ENDPOINT_SUGGESTED = "/messages/{message_id}/suggested"
# files upload
ENDPOINT_FILES_UPLOAD = "/files/upload"
# completion
ENDPOINT_COMPLETION_MESSAGES = "/completion-messages"
ENDPOINT_STOP_COMPLETION_MESSAGES = "/completion-messages/{task_id}/stop"
# chat
ENDPOINT_CHAT_MESSAGES = "/chat-messages"
ENDPOINT_STOP_CHAT_MESSAGES = "/chat-messages/{task_id}/stop"
# workflow
ENDPOINT_RUN_WORKFLOWS = "/workflows/run"
ENDPOINT_STOP_WORKFLOWS = "/workflows/{task_id}/stop"
# audio <-> text
ENDPOINT_TEXT_TO_AUDIO = "/text-to-audio"
ENDPOINT_AUDIO_TO_TEXT = "/audio-to-text"


class Client(BaseModel):
    api_key: str
    api_base: Optional[str] = "https://api.dify.ai/v1"

    def request(self, endpoint: str, method: str,
                content: Optional[types.RequestContent] = None,
                data: Optional[types.RequestData] = None,
                files: Optional[types.RequestFiles] = None,
                json: Optional[Any] = None,
                params: Optional[types.QueryParamTypes] = None,
                headers: Optional[Mapping[str, str]] = None,
                **kwargs: object,
                ) -> httpx.Response:
        """
        Sends a synchronous HTTP request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the request to.
            method: The HTTP method to use (e.g., 'GET', 'POST').
            content: Raw content to include in the request body.
            data: Form data to include in the request body.
            files: Files to include in the request body.
            json: JSON data to include in the request body.
            params: Query parameters to include in the request URL.
            headers: Additional headers to include in the request.
            **kwargs: Extra keyword arguments to pass to the request function.

        Returns:
            A `httpx.Response` object containing the HTTP response.

        Raises:
            Various DifyAPIError exceptions if the response contains an error.
        """
        merged_headers = {}
        if headers:
            merged_headers.update(headers)
        self._prepare_auth_headers(merged_headers)

        response = _httpx_client.request(method, endpoint, content=content, data=data, files=files, json=json,
                                         params=params, headers=merged_headers, **kwargs)
        errors.raise_for_status(response)
        return response

    def request_stream(self, endpoint: str, method: str,
                       content: Optional[types.RequestContent] = None,
                       data: Optional[types.RequestData] = None,
                       files: Optional[types.RequestFiles] = None,
                       json: Optional[Any] = None,
                       params: Optional[types.QueryParamTypes] = None,
                       headers: Optional[Mapping[str, str]] = None,
                       **kwargs,
                       ) -> Iterator[ServerSentEvent]:
        """
        Opens a server-sent events (SSE) stream to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the request to.
            method: The HTTP method to use (e.g., 'GET', 'POST').
            content: Raw content to include in the request body.
            data: Form data to include in the request body.
            files: Files to include in the request body.
            json: JSON data to include in the request body.
            params: Query parameters to include in the request URL.
            headers: Additional headers to include in the request.
            **kwargs: Extra keyword arguments to pass to the request function.

        Returns:
            An iterator of `ServerSentEvent` objects representing the stream of events.

        Raises:
            Various DifyAPIError exceptions if an error event is received in the stream.
        """
        merged_headers = {}
        if headers:
            merged_headers.update(headers)
        self._prepare_auth_headers(merged_headers)

        with connect_sse(_httpx_client, method, endpoint, headers=merged_headers,
                         content=content, data=data, files=files, json=json, params=params, **kwargs) as event_source:
            if not _check_stream_content_type(event_source.response):
                event_source.response.read()
                errors.raise_for_status(event_source.response)
            for sse in event_source.iter_sse():
                errors.raise_for_status(sse)
                if sse.event in IGNORED_STREAM_EVENTS or sse.data in IGNORED_STREAM_EVENTS:
                    continue
                yield sse

    def feedback_messages(self, message_id: str, req: models.FeedbackRequest, **kwargs) -> models.FeedbackResponse:
        """
        Submits feedback for a specific message.

        Args:
            message_id: The identifier of the message to submit feedback for.
            req: A `FeedbackRequest` object containing the feedback details, such as the rating.
            **kwargs: Extra keyword arguments to pass to the request function.

        Returns:
            A `FeedbackResponse` object containing the result of the feedback submission.
        """
        response = self.request(
            self._prepare_url(ENDPOINT_FEEDBACKS, message_id=message_id),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.FeedbackResponse(**response.json())

    def suggest_messages(self, message_id: str, req: models.ChatSuggestRequest, **kwargs) -> models.ChatSuggestResponse:
        """
        Retrieves suggested messages based on a specific message.

        Args:
            message_id: The identifier of the message to get suggestions for.
            req: A `ChatSuggestRequest` object containing the request details.
            **kwargs: Extra keyword arguments to pass to the request function.

        Returns:
            A `ChatSuggestResponse` object containing suggested messages.
        """
        response = self.request(
            self._prepare_url(ENDPOINT_SUGGESTED, message_id=message_id),
            HTTPMethod.GET,
            params=req.model_dump(),
            **kwargs,
        )
        return models.ChatSuggestResponse(**response.json())

    def upload_files(self, file: types.FileTypes, req: models.UploadFileRequest,
                     **kwargs) -> models.UploadFileResponse:
        """
        Uploads a file to be used in subsequent requests.

        Args:
            file: The file to upload. This can be a file-like object, or a tuple of
            (`filename`, file-like object, mime_type).
            req: An `UploadFileRequest` object containing the upload details, such as the user who is uploading.
            **kwargs: Extra keyword arguments to pass to the request function.

        Returns:
            An `UploadFileResponse` object containing details about the uploaded file, such as its identifier and URL.
        """
        response = self.request(
            self._prepare_url(ENDPOINT_FILES_UPLOAD),
            HTTPMethod.POST,
            data=req.model_dump(),
            files=[("file", file)],
            **kwargs,
        )
        return models.UploadFileResponse(**response.json())

    def completion_messages(self, req: models.CompletionRequest, **kwargs) \
            -> Union[models.CompletionResponse, Iterator[models.CompletionStreamResponse]]:
        """
        Sends a request to generate a completion or a series of completions based on the provided input.

        Returns:
            If the response mode is blocking, it returns a `CompletionResponse` object containing the generated message.
            If the response mode is streaming, it returns an iterator of `CompletionStreamResponse` objects containing
            the stream of generated events.
        """
        if req.response_mode == models.ResponseMode.BLOCKING:
            return self._completion_messages(req, **kwargs)
        if req.response_mode == models.ResponseMode.STREAMING:
            return self._completion_messages_stream(req, **kwargs)
        raise ValueError(f"Invalid request_mode: {req.response_mode}")

    def _completion_messages(self, req: models.CompletionRequest, **kwargs) -> models.CompletionResponse:
        response = self.request(
            self._prepare_url(ENDPOINT_COMPLETION_MESSAGES),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.CompletionResponse(**response.json())

    def _completion_messages_stream(self, req: models.CompletionRequest, **kwargs) \
            -> Iterator[models.CompletionStreamResponse]:
        event_source = self.request_stream(
            self._prepare_url(ENDPOINT_COMPLETION_MESSAGES),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        for sse in event_source:
            yield models.build_completion_stream_response(sse.json())

    def stop_completion_messages(self, task_id: str, req: models.StopRequest, **kwargs) -> models.StopResponse:
        """
        Sends a request to stop a streaming completion task.

        Returns:
            A `StopResponse` object indicating the success of the operation.
        """
        return self._stop_stream(self._prepare_url(ENDPOINT_STOP_COMPLETION_MESSAGES, task_id=task_id), req, **kwargs)

    def chat_messages(self, req: models.ChatRequest, **kwargs) \
            -> Union[models.ChatResponse, Iterator[models.ChatStreamResponse]]:
        """
        Sends a request to generate a chat message or a series of chat messages based on the provided input.

        Returns:
            If the response mode is blocking, it returns a `ChatResponse` object containing the generated chat message.
            If the response mode is streaming, it returns an iterator of `ChatStreamResponse` objects containing the
            stream of chat events.
        """
        if req.response_mode == models.ResponseMode.BLOCKING:
            return self._chat_messages(req, **kwargs)
        if req.response_mode == models.ResponseMode.STREAMING:
            return self._chat_messages_stream(req, **kwargs)
        raise ValueError(f"Invalid request_mode: {req.response_mode}")

    def _chat_messages(self, req: models.ChatRequest, **kwargs) -> models.ChatResponse:
        response = self.request(
            self._prepare_url(ENDPOINT_CHAT_MESSAGES),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.ChatResponse(**response.json())

    def _chat_messages_stream(self, req: models.ChatRequest, **kwargs) -> Iterator[models.ChatStreamResponse]:
        event_source = self.request_stream(
            self._prepare_url(ENDPOINT_CHAT_MESSAGES),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        for sse in event_source:
            yield models.build_chat_stream_response(sse.json())

    def stop_chat_messages(self, task_id: str, req: models.StopRequest, **kwargs) -> models.StopResponse:
        """
        Sends a request to stop a streaming chat task.

        Returns:
            A `StopResponse` object indicating the success of the operation.
        """
        return self._stop_stream(self._prepare_url(ENDPOINT_STOP_CHAT_MESSAGES, task_id=task_id), req, **kwargs)

    def run_workflows(self, req: models.WorkflowsRunRequest, **kwargs) \
            -> Union[models.WorkflowsRunResponse, Iterator[models.WorkflowsRunStreamResponse]]:
        """
        Initiates the execution of a workflow, which can consist of multiple steps and actions.

        Returns:
            If the response mode is blocking, it returns a `WorkflowsRunResponse` object containing the results of the
            completed workflow.
            If the response mode is streaming, it returns an iterator of `WorkflowsRunStreamResponse` objects
            containing the stream of workflow events.
        """
        if req.response_mode == models.ResponseMode.BLOCKING:
            return self._run_workflows(req, **kwargs)
        if req.response_mode == models.ResponseMode.STREAMING:
            return self._run_workflows_stream(req, **kwargs)
        raise ValueError(f"Invalid request_mode: {req.response_mode}")

    def _run_workflows(self, req: models.WorkflowsRunRequest, **kwargs) -> models.WorkflowsRunResponse:
        response = self.request(
            self._prepare_url(ENDPOINT_RUN_WORKFLOWS),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.WorkflowsRunResponse(**response.json())

    def _run_workflows_stream(self, req: models.WorkflowsRunRequest, **kwargs) \
            -> Iterator[models.WorkflowsRunStreamResponse]:
        event_source = self.request_stream(
            self._prepare_url(ENDPOINT_RUN_WORKFLOWS),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        for sse in event_source:
            yield models.build_workflows_stream_response(sse.json())

    def stop_workflows(self, task_id: str, req: models.StopRequest, **kwargs) -> models.StopResponse:
        """
        Sends a request to stop a streaming workflow task.

        Returns:
            A `StopResponse` object indicating the success of the operation.
        """
        return self._stop_stream(self._prepare_url(ENDPOINT_STOP_WORKFLOWS, task_id=task_id), req, **kwargs)

    def _stop_stream(self, endpoint: str, req: models.StopRequest, **kwargs) -> models.StopResponse:
        response = self.request(
            endpoint,
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.StopResponse(**response.json())

    def _prepare_url(self, endpoint: str, **kwargs) -> str:
        return self.api_base + endpoint.format(**kwargs)

    def _prepare_auth_headers(self, headers: Dict[str, str]):
        if "authorization" not in (key.lower() for key in headers.keys()):
            headers["Authorization"] = f"Bearer {self.api_key}"


class AsyncClient(BaseModel):
    api_key: str
    api_base: Optional[str] = "https://api.dify.ai/v1"

    async def arequest(self, endpoint: str, method: str,
                       content: Optional[types.RequestContent] = None,
                       data: Optional[types.RequestData] = None,
                       files: Optional[types.RequestFiles] = None,
                       json: Optional[Any] = None,
                       params: Optional[types.QueryParamTypes] = None,
                       headers: Optional[Mapping[str, str]] = None,
                       **kwargs,
                       ) -> httpx.Response:
        """
        Asynchronously sends a request to the specified Dify API endpoint.

        Args:
            endpoint: The endpoint URL to which the request is sent.
            method: The HTTP method to be used for the request (e.g., 'GET', 'POST').
            content: Raw content to include in the request body, if any.
            data: Form data to be sent in the request body.
            files: Files to be uploaded with the request.
            json: JSON data to be sent in the request body.
            params: Query parameters to be included in the request URL.
            headers: Additional headers to be sent with the request.
            **kwargs: Extra keyword arguments to be passed to the underlying HTTPX request function.

        Returns:
            A httpx.Response object containing the server's response to the HTTP request.

        Raises:
            Various DifyAPIError exceptions if the response contains an error.
        """
        merged_headers = {}
        if headers:
            merged_headers.update(headers)
        self._prepare_auth_headers(merged_headers)

        response = await _async_httpx_client.request(method, endpoint, content=content, data=data, files=files,
                                                     json=json, params=params, headers=merged_headers, **kwargs)
        errors.raise_for_status(response)
        return response

    async def arequest_stream(self, endpoint: str, method: str,
                              content: Optional[types.RequestContent] = None,
                              data: Optional[types.RequestData] = None,
                              files: Optional[types.RequestFiles] = None,
                              json: Optional[Any] = None,
                              params: Optional[types.QueryParamTypes] = None,
                              headers: Optional[Mapping[str, str]] = None,
                              **kwargs,
                              ) -> AsyncIterator[ServerSentEvent]:
        """
        Asynchronously establishes a streaming connection to the specified Dify API endpoint.

        Args:
            endpoint: The endpoint URL to which the request is sent.
            method: The HTTP method to be used for the request (e.g., 'GET', 'POST').
            content: Raw content to include in the request body, if any.
            data: Form data to be sent in the request body.
            files: Files to be uploaded with the request.
            json: JSON data to be sent in the request body.
            params: Query parameters to be included in the request URL.
            headers: Additional headers to be sent with the request.
            **kwargs: Extra keyword arguments to be passed to the underlying HTTPX request function.

        Yields:
            ServerSentEvent objects representing the events received from the server.

        Raises:
            Various DifyAPIError exceptions if an error event is received in the stream.
        """
        merged_headers = {}
        if headers:
            merged_headers.update(headers)
        self._prepare_auth_headers(merged_headers)

        async with aconnect_sse(_async_httpx_client, method, endpoint, headers=merged_headers,
                                content=content, data=data, files=files, json=json, params=params,
                                **kwargs) as event_source:
            if not _check_stream_content_type(event_source.response):
                await event_source.response.aread()
                errors.raise_for_status(event_source.response)
            async for sse in event_source.aiter_sse():
                errors.raise_for_status(sse)
                if sse.event in IGNORED_STREAM_EVENTS or sse.data in IGNORED_STREAM_EVENTS:
                    continue
                yield sse

    async def afeedback_messages(self, message_id: str, req: models.FeedbackRequest, **kwargs) \
            -> models.FeedbackResponse:
        """
        Submits feedback for a specific message.

        Args:
            message_id: The identifier of the message to submit feedback for.
            req: A `FeedbackRequest` object containing the feedback details, such as the rating.
            **kwargs: Extra keyword arguments to pass to the request function.

        Returns:
            A `FeedbackResponse` object containing the result of the feedback submission.
        """
        response = await self.arequest(
            self._prepare_url(ENDPOINT_FEEDBACKS, message_id=message_id),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.FeedbackResponse(**response.json())

    async def asuggest_messages(self, message_id: str, req: models.ChatSuggestRequest, **kwargs) \
            -> models.ChatSuggestResponse:
        """
        Retrieves suggested messages based on a specific message.

        Args:
            message_id: The identifier of the message to get suggestions for.
            req: A `ChatSuggestRequest` object containing the request details.
            **kwargs: Extra keyword arguments to pass to the request function.

        Returns:
            A `ChatSuggestResponse` object containing suggested messages.
        """
        response = await self.arequest(
            self._prepare_url(ENDPOINT_SUGGESTED, message_id=message_id),
            HTTPMethod.GET,
            params=req.model_dump(),
            **kwargs,
        )
        return models.ChatSuggestResponse(**response.json())

    async def aupload_files(self, file: types.FileTypes, req: models.UploadFileRequest, **kwargs) \
            -> models.UploadFileResponse:
        """
        Uploads a file to be used in subsequent requests.

        Args:
            file: The file to upload. This can be a file-like object, or a tuple of
            (`filename`, file-like object, mime_type).
            req: An `UploadFileRequest` object containing the upload details, such as the user who is uploading.
            **kwargs: Extra keyword arguments to pass to the request function.

        Returns:
            An `UploadFileResponse` object containing details about the uploaded file, such as its identifier and URL.
        """
        response = await self.arequest(
            self._prepare_url(ENDPOINT_FILES_UPLOAD),
            HTTPMethod.POST,
            data=req.model_dump(),
            files=[("file", file)],
            **kwargs,
        )
        return models.UploadFileResponse(**response.json())

    async def acompletion_messages(self, req: models.CompletionRequest, **kwargs) \
            -> Union[models.CompletionResponse, AsyncIterator[models.CompletionStreamResponse]]:
        """
        Sends a request to generate a completion or a series of completions based on the provided input.

        Returns:
            If the response mode is blocking, it returns a `CompletionResponse` object containing the generated message.
            If the response mode is streaming, it returns an iterator of `CompletionStreamResponse` objects containing
            the stream of generated events.
        """
        if req.response_mode == models.ResponseMode.BLOCKING:
            return await self._acompletion_messages(req, **kwargs)
        if req.response_mode == models.ResponseMode.STREAMING:
            return self._acompletion_messages_stream(req, **kwargs)
        raise ValueError(f"Invalid request_mode: {req.response_mode}")

    async def _acompletion_messages(self, req: models.CompletionRequest, **kwargs) -> models.CompletionResponse:
        response = await self.arequest(
            self._prepare_url(ENDPOINT_COMPLETION_MESSAGES),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.CompletionResponse(**response.json())

    async def _acompletion_messages_stream(self, req: models.CompletionRequest, **kwargs) \
            -> AsyncIterator[models.CompletionStreamResponse]:
        async for sse in self.arequest_stream(
                self._prepare_url(ENDPOINT_COMPLETION_MESSAGES),
                HTTPMethod.POST,
                json=req.model_dump(),
                **kwargs):
            yield models.build_completion_stream_response(sse.json())

    async def astop_completion_messages(self, task_id: str, req: models.StopRequest, **kwargs) -> models.StopResponse:
        """
        Sends a request to stop a streaming completion task.

        Returns:
            A `StopResponse` object indicating the success of the operation.
        """
        return await self._astop_stream(
            self._prepare_url(ENDPOINT_STOP_COMPLETION_MESSAGES, task_id=task_id), req, **kwargs)

    async def achat_messages(self, req: models.ChatRequest, **kwargs) \
            -> Union[models.ChatResponse, AsyncIterator[models.ChatStreamResponse]]:
        """
        Sends a request to generate a chat message or a series of chat messages based on the provided input.

        Returns:
            If the response mode is blocking, it returns a `ChatResponse` object containing the generated chat message.
            If the response mode is streaming, it returns an iterator of `ChatStreamResponse` objects containing the
            stream of chat events.
        """
        if req.response_mode == models.ResponseMode.BLOCKING:
            return await self._achat_messages(req, **kwargs)
        if req.response_mode == models.ResponseMode.STREAMING:
            return self._achat_messages_stream(req, **kwargs)
        raise ValueError(f"Invalid request_mode: {req.response_mode}")

    async def _achat_messages(self, req: models.ChatRequest, **kwargs) -> models.ChatResponse:
        response = await self.arequest(
            self._prepare_url(ENDPOINT_CHAT_MESSAGES),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.ChatResponse(**response.json())

    async def _achat_messages_stream(self, req: models.ChatRequest, **kwargs) \
            -> AsyncIterator[models.ChatStreamResponse]:
        async for sse in self.arequest_stream(
                self._prepare_url(ENDPOINT_CHAT_MESSAGES),
                HTTPMethod.POST,
                json=req.model_dump(),
                **kwargs):
            yield models.build_chat_stream_response(sse.json())

    async def astop_chat_messages(self, task_id: str, req: models.StopRequest, **kwargs) -> models.StopResponse:
        """
        Sends a request to stop a streaming chat task.

        Returns:
            A `StopResponse` object indicating the success of the operation.
        """
        return await self._astop_stream(self._prepare_url(ENDPOINT_STOP_CHAT_MESSAGES, task_id=task_id), req, **kwargs)

    async def arun_workflows(self, req: models.WorkflowsRunRequest, **kwargs) \
            -> Union[models.WorkflowsRunResponse, AsyncIterator[models.WorkflowsStreamResponse]]:
        """
        Initiates the execution of a workflow, which can consist of multiple steps and actions.

        Returns:
            If the response mode is blocking, it returns a `WorkflowsRunResponse` object containing the results of the
            completed workflow.
            If the response mode is streaming, it returns an iterator of `WorkflowsRunStreamResponse` objects
            containing the stream of workflow events.
        """
        if req.response_mode == models.ResponseMode.BLOCKING:
            return await self._arun_workflows(req, **kwargs)
        if req.response_mode == models.ResponseMode.STREAMING:
            return self._arun_workflows_stream(req, **kwargs)
        raise ValueError(f"Invalid request_mode: {req.response_mode}")

    async def _arun_workflows(self, req: models.WorkflowsRunRequest, **kwargs) -> models.WorkflowsRunResponse:
        response = await self.arequest(
            self._prepare_url(ENDPOINT_RUN_WORKFLOWS),
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.WorkflowsRunResponse(**response.json())

    async def _arun_workflows_stream(self, req: models.WorkflowsRunRequest, **kwargs) \
            -> AsyncIterator[models.WorkflowsRunStreamResponse]:
        async for sse in self.arequest_stream(
                self._prepare_url(ENDPOINT_RUN_WORKFLOWS),
                HTTPMethod.POST,
                json=req.model_dump(),
                **kwargs):
            yield models.build_workflows_stream_response(sse.json())

    async def astop_workflows(self, task_id: str, req: models.StopRequest, **kwargs) -> models.StopResponse:
        """
        Sends a request to stop a streaming workflow task.

        Returns:
            A `StopResponse` object indicating the success of the operation.
        """
        return await self._astop_stream(self._prepare_url(ENDPOINT_STOP_WORKFLOWS, task_id=task_id), req, **kwargs)

    async def _astop_stream(self, endpoint: str, req: models.StopRequest, **kwargs) -> models.StopResponse:
        response = await self.arequest(
            endpoint,
            HTTPMethod.POST,
            json=req.model_dump(),
            **kwargs,
        )
        return models.StopResponse(**response.json())

    def _prepare_url(self, endpoint: str, **kwargs) -> str:
        return self.api_base + endpoint.format(**kwargs)

    def _prepare_auth_headers(self, headers: Dict[str, str]):
        if "authorization" not in (key.lower() for key in headers.keys()):
            headers["Authorization"] = f"Bearer {self.api_key}"


def _get_content_type(headers: httpx.Headers) -> str:
    return headers.get("content-type", "").partition(";")[0]


def _check_stream_content_type(response: httpx.Response) -> bool:
    content_type = _get_content_type(response.headers)
    return response.is_success and "text/event-stream" in content_type
