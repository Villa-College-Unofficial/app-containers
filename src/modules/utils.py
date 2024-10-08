import shutil
from mount import mount, MountFlag, umount, UmountFlag
from os import path
from nicegui import ui

def overlaymount(destination:str, lowerdirs:list[str], upperdir:str, workdir:str) -> bool:
    if path.ismount(destination):
        return True

    try:
        mount("overlay", destination, "overlay", data=f'lowerdir={":".join(lowerdirs)},upperdir={upperdir},workdir={workdir}')
        return True
    except Exception as e:
        print("\n\n\n")
        print(e)
        print("\n\n\n")
        return False

def unmount(destination:str) -> bool:
    if not path.ismount(destination):
        return True
    
    try:
        umount(destination)
        return True
    except:
        return False

def confirm(title:str = "Are you sure?", confirm_text:str = "YES", reject_text:str = "NO", confirm_action:callable = None, reject_action:callable = None, children_action:callable = None):
    with ui.dialog() as dialog, ui.card():
        def confa():
            dialog.close()
            if confirm_action is not None:
                confirm_action()
                # try:
                # except:
                #     dialog.close()

        def reja():
            dialog.close()
            if reject_action is not None:
                reject_action()
                # try:
                # except:
                #     dialog.close()

        ui.label(title)
        if children_action is not None:
            children_action(ui)

        with ui.row():
            ui.button(confirm_text, on_click=confa)
            ui.button(reject_text, on_click=reja)

        dialog.open()    
    
