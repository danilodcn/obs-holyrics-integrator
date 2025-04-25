import queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

import requests
from ttkthemes import ThemedTk

# Layout constants
PADDING_X: int = 10
PADDING_Y: int = 10
ENTRY_WIDTH: int = 30

# Set up themed window
window = ThemedTk(theme='arc')

# Message types
HOST_VERIFY = 'HOST_VERIFY'
START_SERVER = 'START_SERVER'
SHOW_MESSAGE = 'SHOW_MESSAGE'

# Message queue
message_bus = queue.Queue()
# Function to handle a message based on its type
def handle_message(message):
    msg_type = message.get('type')
    context = message.get('context', {})

    if msg_type == HOST_VERIFY:
        host = context.get('host')
        try:
            response = requests.get(host, timeout=5)
            message_bus.put({
                'type': SHOW_MESSAGE,
                'context': {
                    'kind': 'info',
                    'title': 'Host OK',
                    'message': f'{host} successfully resolved!'
                }
            })
        except Exception:
            message_bus.put({
                'type': SHOW_MESSAGE,
                'context': {
                    'kind': 'error',
                    'title': 'Error',
                    'message': f'Could not resolve {host}'
                }
            })

    elif msg_type == START_SERVER:
        obs = context.get('obs')
        holyrics = context.get('holyrics')
        print(f'Starting with OBS: {obs} | Holyrics: {holyrics}')
        message_bus.put({
            'type': SHOW_MESSAGE,
            'context': {
                'kind': 'info',
                'title': 'Started',
                'message': 'Process started with the provided hosts.'
            }
        })

    elif msg_type == SHOW_MESSAGE:
        kind = context.get('kind')
        title = context.get('title', '')
        message = context.get('message', '')

        if kind == 'info':
            messagebox.showinfo(title, message)
        elif kind == 'error':
            messagebox.showerror(title, message)
        elif kind == 'warning':
            messagebox.showwarning(title, message)

    else:
        message_bus.put({
            'type': SHOW_MESSAGE,
            'context': {
                'kind': 'warning',
                'title': 'Unknown Message',
                'message': f'Unknown message type: {msg_type}'
            }
        })


# Background loop to consume and process messages
def process_message_bus():
    try:
        while True:
            message = message_bus.get_nowait()
            handle_message(message)
    except queue.Empty:
        pass
    root.after(100, process_message_bus)


# Put a HOST_VERIFY message on the bus
def enqueue_host_verification(entry_widget: ttk.Entry):
    host = entry_widget.get().strip()
    if not host:
        return
    message_bus.put({'type': HOST_VERIFY, 'context': {'host': host}})


# Put a START_SERVER message on the bus
def enqueue_start_server():
    obs = obs_host_var.get().strip()
    holyrics = holyrics_host_var.get().strip()
    message_bus.put(
        {'type': START_SERVER, 'context': {'obs': obs, 'holyrics': holyrics}}
    )


# Utility function to create a labeled entry and test button
def create_host_row(
    parent: tk.Tk | ttk.Frame,
    label_text: str,
    row_index: int,
    column_index: int,
    entry_variable: tk.StringVar,
) -> None:
    ttk.Label(parent, text=label_text).grid(
        row=row_index, column=0, sticky='w'
    )
    entry: ttk.Entry = ttk.Entry(
        parent, textvariable=entry_variable, width=ENTRY_WIDTH
    )
    entry.grid(row=row_index, column=column_index)
    ttk.Button(
        parent, text='Test', command=lambda: enqueue_host_verification(entry)
    ).grid(row=row_index, column=2, padx=5)


# UI Setup
root = window
root.title('Hosts Form')
root.geometry('400x250')
root.configure(padx=PADDING_X, pady=PADDING_Y)

# Input variables
obs_host_var: tk.StringVar = tk.StringVar()
holyrics_host_var: tk.StringVar = tk.StringVar()

# Create input rows
create_host_row(root, 'OBS Host:', 0, 1, obs_host_var)
create_host_row(root, 'Holyrics Host:', 1, 1, holyrics_host_var)

ttk.Button(root, text='Save', command=enqueue_start_server).grid(
    row=3, column=1, pady=20
)

# Start the message processing loop
root.after(100, process_message_bus)

root.mainloop()
