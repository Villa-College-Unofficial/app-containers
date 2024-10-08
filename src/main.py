#!/usr/bin/env python3

from modules.app import App
from nicegui import ui
from nicegui.core import app
from modules import auth
from modules.container import Container
from modules.config import current_config, dockerclient as client
from fastapi import WebSocket
from modules.utils import confirm
import time
import requests
import threading

available_apps = current_config.apps()

existing_containers = Container.enumerate()
for container in existing_containers:
    print(f"Adding existing container: '{container.name}'")

def container_toggle(appname:str, email:str):
    def startaction():
        def start_thread(cont, appname, email):
            started = cont.start()
            print(f"Started '{appname}' for '{email}'" if started else f"Failed to started '{appname}' for '{email}'")

        threading.Thread(target=start_thread, args= (cont,appname, email, )).start()
        ui.timer(1, lambda: ui.notify(f"Please wait while we start '{appname}' for you. This may take a while"), once=True)
        # TODO: implement a more graceful solution to refresh app card
        ui.timer(10, lambda: ui.run_javascript("window.location.reload()"), once=True)

    def stopaction():
        contname = cont.name

        def stop_thread(cont, appname, email):
            stopped = cont.destroy()
            print(f"Stopped '{appname}' for '{email}'" if stopped else f"Failed to stop '{appname}' for '{email}'")
                
        threading.Thread(target=stop_thread, args= (cont,appname, email, )).start()
        ui.timer(1, lambda:  ui.notify(f"Please wait while we stop '{appname}' for you. This may take a while"), once=True)
        ui.timer(10, lambda: ui.run_javascript("window.location.reload()"), once=True)

    cont = Container(email, appname)

    if cont is not None and cont.status() == Container.Status.RUNNING:
        confirm(f"Are you sure you want to destroy your {appname} instance?", confirm_action=stopaction)
    else:
        confirm(f"Are you sure you want to start your {appname} instance?", confirm_action=startaction)

@ui.refreshable
def container_card(appname, contname):
    running = False
    
    try:
        cont = client.containers.get(contname)
        ports = cont.attrs['NetworkSettings']['Ports']
        running = cont.status == "running"
    except Exception as e:
        running = False

    if running:
        with ui.button_group():
            for port in ports.keys():
                hostport = ports[port][0]['HostPort']
                is_http = False
                try:
                    requests.head(f"http://localhost:{hostport}", timeout=0.1)
                    is_http = True
                except:
                    pass
                if is_http:
                    ui.button(f"Connect {hostport}", color="green-600", on_click=lambda: ui.run_javascript(f"""
                    window.open(window.location.href.split(':')[0] + "://" + window.location.hostname + ":{hostport}", "_blank");
                    """))
            ui.button("Stop", color="red-600", on_click=lambda:  container_toggle(appname, app.storage.user["username"]))
    else:
        with ui.button_group():
            ui.button("Start", on_click=lambda:  container_toggle(appname, app.storage.user["username"]))

@ui.page("/apps")
def apps_view() -> None:
    ui.page_title(current_config.title())
    if not app.storage.user.get("authenticated"):
        ui.navigate.to("/login")

    with ui.column().classes('absolute-center items-center'):
        ui.label(f'Apps available for {app.storage.user["username"]}!').classes('text-2xl')
        for appname in available_apps.keys():
            
            contname = Container.get_container_name(appname, app.storage.user["username"])
            cont = None
            running = False
            try:
                cont = client.containers.get(contname)
                running = cont.status == "running"
            except:
                running = False

            with ui.card().tight().classes("p-5 rounded hover:cursor-pointer hover:bg-blue-100"):
                ui.label(appname).classes("text-2xl font-bold self-center pb-5 uppercase")
                ui.image(available_apps[appname]['icon']).classes("w-50 h-50 p-2 mb-4")
                ui.chip(text="RUNNING" if running else "STOPPED", color=("green-600" if running else "red-600")).classes("p-2 text-white rounded self-center text-center").props('round')
                
                with ui.card_section():
                    container_card(appname, contname)
                    # print(contname in refresh_statuses)
                    # # refresh every 2 seconds
                    # def refresh():
                    #     if contname in refresh_statuses:
                    #         print("REF 2")
                    #         container_card.refresh(appname, contname)
                    #         refresh_statuses.remove(contname)
                        
                    # ui.timer(2, refresh)
            

ui.run(storage_secret=current_config.secret(), favicon=current_config.favicon())