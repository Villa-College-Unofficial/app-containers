#!/usr/bin/env python3

from modules.app import App
from nicegui import ui
from nicegui.core import app
from modules import auth
from modules.container import Container
from modules.config import current_config, dockerclient as client
from fastapi import WebSocket
from modules.utils import confirm
from modules.proxy import AppProxy

available_apps = current_config.apps()
proxies = dict()

def add_proxy(cont:Container):
    ip = cont.docker_container.attrs['NetworkSettings']['IPAddress']
    proxy = AppProxy(cont)
    proxy.start()

    proxies[cont.name] = proxy

    return proxy

existing_containers = Container.enumerate()
for container in existing_containers:
    print(f"Adding existing container: '{container.name}'")

    if container.name not in proxies.keys():
        proxy = add_proxy(container)

        print(f"'{container.name}' listening on '{proxy.http_port}'")

def container_toggle(appname:str, email:str):
    def startaction():
        started = cont.start()
        print(f"Started '{appname}' for '{email}'" if started else f"Failed to started '{appname}' for '{email}'")
        add_proxy(cont)
        

    def stopaction():
        contname = cont.name
        stopped = cont.destroy()
        print(f"Stopped '{appname}' for '{email}'" if stopped else f"Failed to stop '{appname}' for '{email}'")
        try:
            proxy = proxies.pop(contname)
            proxy.stop()
        except:
            pass

    cont = Container(email, appname)

    if cont is not None and cont.status() == Container.Status.RUNNING:
        confirm(f"Are you sure you want to destroy your {appname} instance?", confirm_action=stopaction)
    else:
        confirm(f"Are you sure you want to start your {appname} instance?", confirm_action=startaction)

@ui.page("/apps")
def apps_view() -> None:
    ui.page_title(current_config.title())
    if not app.storage.user.get("authenticated"):
        ui.navigate.to("/login")

    with ui.column().classes('absolute-center items-center'):
        ui.label(f'Apps available for {app.storage.user["username"]}!').classes('text-2xl')
        for appname in available_apps.keys():
            
            contname = Container.get_container_name(appname, app.storage.user["username"])
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
                    if running:
                        with ui.button_group():
                            ui.button("Connect", color="green-600", on_click=lambda: ui.run_javascript(f"""
                            window.open(window.location.href.split(':')[0] + "://" + window.location.hostname + ":{proxies[contname].http_port}", "_blank");
                            """))
                            ui.button("Stop", color="red-600", on_click=lambda:  container_toggle(appname, app.storage.user["username"]))
                    else:
                        with ui.button_group():
                            ui.button("Start", on_click=lambda:  container_toggle(appname, app.storage.user["username"]))

ui.run(storage_secret=current_config.secret(), favicon=current_config.favicon())