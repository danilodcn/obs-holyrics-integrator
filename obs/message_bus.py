import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from tkinter import messagebox
from typing import Any, Callable

import requests

from obs.integrator_bridge import HolyricsOBSBridge
from obs.integrator_controller import HolyricsOBSController


# Enums
class MessageType(Enum):
    HOST_VERIFY = 'HOST_VERIFY'
    START_SERVER = 'START_SERVER'
    SHOW_MESSAGE = 'SHOW_MESSAGE'


# Message Structure
@dataclass
class Message:
    type: MessageType
    context: dict[str, Any]


class MessageKind(Enum):
    INFO = 'info'
    ERROR = 'error'
    WARNING = 'warning'


# Message Queue
message_bus: queue.Queue[Message] = queue.Queue()

# --- Message Bus Loop --- #
def process_pending_messages() -> None:
    try:
        while True:
            message: Message = message_bus.get_nowait()
            handler = MESSAGE_HANDLERS.get(
                message.type,
                lambda ctx: handle_unknown({'type': message.type}),
            )
            handler(message.context)
    except queue.Empty:
        pass


# --- Message Handlers --- #
def handle_host_verify(context: dict[str, Any]) -> None:
    host = context.get('host')
    if host is None:
        raise ValueError('Host is required')

    # Resolve host
    try:
        requests.get(host, timeout=5)
        message_bus.put(
            Message(
                type=MessageType.SHOW_MESSAGE,
                context={
                    'kind': MessageKind.INFO.value,
                    'title': 'Host OK',
                    'message': f'{host} successfully resolved!',
                },
            )
        )
    except Exception:
        message_bus.put(
            Message(
                type=MessageType.SHOW_MESSAGE,
                context={
                    'kind': MessageKind.ERROR.value,
                    'title': 'Error',
                    'message': f'Could not resolve {host}',
                },
            )
        )


controller: HolyricsOBSController | None = None


def handle_start_server(context: dict[str, Any]) -> None:
    global controller
    obs_host = context.get('obs_host')
    holyrics_host = context.get('holyrics_host')
    principal_scene = context.get('principal_scene', '')
    holyrics_scene = context.get('holyrics_scene', '')

    # validate inputs
    if (
        not obs_host
        or not holyrics_host
        and not principal_scene
        and not holyrics_scene
    ):
        message_bus.put(
            Message(
                type=MessageType.SHOW_MESSAGE,
                context={
                    'kind': MessageKind.ERROR.value,
                    'title': 'Error',
                    'message': 'Invalid input parameters.',
                },
            )
        )
        return

    print(f'Starting with OBS: {obs_host} | Holyrics: {holyrics_host}')

    if controller is not None and controller.is_running():
        controller.stop()
        message_bus.put(
            Message(
                type=MessageType.SHOW_MESSAGE,
                context={
                    'kind': MessageKind.INFO.value,
                    'title': 'Stopping server...',
                    'message': 'The server is stopping.',
                },
            )
        )
        return

    bridge = HolyricsOBSBridge(
        obs_host, holyrics_host, principal_scene, holyrics_scene
    )
    controller = HolyricsOBSController(bridge)
    controller.start()
    message_bus.put(
        Message(
            type=MessageType.SHOW_MESSAGE,
            context={
                'kind': MessageKind.INFO.value,
                'title': 'Started',
                'message': 'Process started is running.',
            },
        )
    )


def handle_show_message(context: dict[str, Any]) -> None:
    kind = context.get('kind')
    title = context.get('title', '')
    message = context.get('message', '')

    if kind == MessageKind.INFO.value:
        messagebox.showinfo(title, message)
    elif kind == MessageKind.ERROR.value:
        messagebox.showerror(title, message)
    elif kind == MessageKind.WARNING.value:
        messagebox.showwarning(title, message)


def handle_unknown(context: dict[str, Any]) -> None:
    message_bus.put(
        Message(
            type=MessageType.SHOW_MESSAGE,
            context={
                'kind': MessageKind.WARNING.value,
                'title': 'Unknown Message',
                'message': f"Unknown message type: {context.get('type')}",
            },
        )
    )


# Message Handlers Registry
MESSAGE_HANDLERS: dict[MessageType, Callable[[dict[str, Any]], None]] = {
    MessageType.HOST_VERIFY: handle_host_verify,
    MessageType.START_SERVER: handle_start_server,
    MessageType.SHOW_MESSAGE: handle_show_message,
}
