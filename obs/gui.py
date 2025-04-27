import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

from profile_manager import get_profile, load_profiles, save_profile
from ttkthemes import ThemedTk

from obs.message_bus import (
    Message,
    MessageKind,
    MessageType,
    process_pending_messages,
)

# Constants
PADDING_X: int = 10
PADDING_Y: int = 10
ENTRY_WIDTH: int = 30


def create_gui(message_bus: queue.Queue) -> tk.Tk:
    # UI Setup
    root = ThemedTk(theme='arc')
    root.title('Holyrics OBS Integrator')
    root.geometry('600x250')
    root.configure(padx=PADDING_X, pady=PADDING_Y)

    # Input variables
    obs_host_var = tk.StringVar()
    holyrics_host_var = tk.StringVar()
    profile_name_var = tk.StringVar()

    principal_scene_name_var = tk.StringVar()
    holyrics_scene_name_var = tk.StringVar()

    profiles_data = load_profiles()
    profile_names = list(profiles_data['profiles'].keys())
    active_profile = profiles_data.get('active_profile', '')
    profile_name_var.set(active_profile)

    def on_profile_change(event=None):
        profile = get_profile(profile_name_var.get())
        obs_host_var.set(profile.get('obs', ''))
        holyrics_host_var.set(profile.get('holyrics', ''))
        principal_scene_name_var.set(profile.get('principal_scene', ''))
        holyrics_scene_name_var.set(profile.get('holyrics_scene', ''))

    def on_save_profile():
        name = profile_name_var.get()

        data = {
            'obs': obs_host_var.get(),
            'holyrics': holyrics_host_var.get(),
            'principal_scene': principal_scene_name_var.get(),
            'holyrics_scene': holyrics_scene_name_var.get(),
        }
        save_profile(name, data)
        if name not in profile_names:
            profile_names.append(name)
            profile_combobox['values'] = profile_names

    ttk.Label(root, text='Profile:').grid(row=0, column=0, sticky='w')
    profile_combobox = ttk.Combobox(
        root, textvariable=profile_name_var, values=profile_names
    )
    profile_combobox.grid(row=0, column=1, columnspan=2, sticky='ew')
    profile_combobox.bind('<<ComboboxSelected>>', on_profile_change)

    ttk.Button(
        root,
        text='Rename',
        command=lambda: profile_name_var.set(profile_name_var.get()),
    ).grid(row=0, column=3, padx=5)

    ttk.Button(root, text='Save Profile', command=on_save_profile).grid(
        row=0, column=4, padx=5
    )

    # UI Elements
    __create_host_row(message_bus, root, 'OBS Host:', 3, 1, obs_host_var)
    __create_host_row(
        message_bus, root, 'Holyrics Host:', 4, 1, holyrics_host_var
    )

    # Cenes names
    ttk.Label(root, text='Principal Scene:').grid(row=5, column=0, sticky='w')
    ttk.Entry(
        root, textvariable=principal_scene_name_var, width=ENTRY_WIDTH
    ).grid(row=5, column=1)

    ttk.Label(root, text='Holyrics Scene:').grid(row=6, column=0, sticky='w')
    ttk.Entry(
        root, textvariable=holyrics_scene_name_var, width=ENTRY_WIDTH
    ).grid(row=6, column=1)

    ttk.Button(
        root,
        text='Start',
        command=lambda: enqueue_start_server(
            message_bus,
            obs_host_var,
            holyrics_host_var,
            principal_scene_name_var,
            holyrics_scene_name_var,
        ),
    ).grid(row=8, column=1, pady=20)

    # Start message loop
    root.after(100, start_worker_thread, message_bus)

    # Load initial active profile
    if active_profile:
        on_profile_change()
    return root


def start_worker_thread(message_bus: queue.Queue) -> None:
    worker_thread = threading.Thread(
        target=process_message_bus,
        args=(message_bus,),
        daemon=True,
    )
    worker_thread.start()


def process_message_bus(message_bus: queue.Queue) -> None:
    while True:
        try:
            process_pending_messages()
            time.sleep(0.1)
        except Exception as e:
            print(f'Error in process_message_bus: {e}')
            message_bus.put(
                Message(
                    type=MessageType.SHOW_MESSAGE,
                    context={
                        'kind': MessageKind.ERROR.value,
                        'title': 'Host OK',
                        'message': f'error: {e}',
                    },
                )
            )
            time.sleep(1)


# Enqueue a host verification message
def enqueue_host_verification(
    message_bus: queue.Queue, entry_widget: ttk.Entry
) -> None:
    host: str = entry_widget.get().strip()
    if not host:
        return
    message_bus.put(
        Message(type=MessageType.HOST_VERIFY, context={'host': host})
    )


# Enqueue a start server message
def enqueue_start_server(
    message_bus: queue.Queue,
    obs_host_var: tk.StringVar,
    holyrics_host_var: tk.StringVar,
    principal_scene_name_var: tk.StringVar,
    holyrics_scene_name_var: tk.StringVar,
) -> None:
    obs_host = obs_host_var.get().strip()
    holyrics_host = holyrics_host_var.get().strip()
    message_bus.put(
        Message(
            type=MessageType.START_SERVER,
            context={
                'obs_host': obs_host,
                'holyrics_host': holyrics_host,
                'principal_scene': principal_scene_name_var.get(),
                'holyrics_scene': holyrics_scene_name_var.get(),
            },
        )
    )


# Utility function to create form inputs
def __create_host_row(
    message_bus: queue.Queue,
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
        parent,
        text='Test',
        command=lambda: enqueue_host_verification(message_bus, entry),
    ).grid(row=row_index, column=2, padx=5)
