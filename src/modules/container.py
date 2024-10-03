import docker
from modules.config import current_config, dockerclient as client
from enum import Enum
import tempfile
from os import path, makedirs
import shutil
from nicegui.core import app
from nicegui import ui
from modules.utils import overlaymount, unmount
from fastapi import WebSocket, Request

class Container:
    """
    Represents a Docker container.
    """
    class Status(Enum):
        """
        Enum for container status.
        """
        UNINITIALIZED   = 0
        CREATED         = 1
        RUNNING         = 2
        RESTARTING      = 3
        PAUSED          = 4
        EXITED          = -1
    
        @classmethod
        def from_docker(cls, status: str):
            """
            Convert a Docker status string to a Container.Status enum.
            
            Args:
                status (str): Docker status string
            
            Returns:
                Container.Status: Corresponding enum value
            """
            switch = {
                'restarting': Container.Status.RESTARTING,
                'running': Container.Status.RUNNING,
                'paused': Container.Status.PAUSED,
                'exited': Container.Status.EXITED,
            }

            return switch.get(status, None)

    # Container attributes
    email: str
    safeemail: str
    upperdir: str
    workdir: str
    mergeddir: str
    name: str
    docker_container: docker.models.containers.Container
    docker_network: docker.models.networks.Network
    appname: str

    def __init__(self: 'Container', email: str, app: str):
        """
        Initialize a Container instance.
        
        Args:
            email (str): Email address
            app (str): App name
        """
        self.appname = app
        self.email = email
        self.safeemail = email.replace('@','_').replace('.', '_')
        self.name = Container.get_container_name(app, email)
        self.upperdir = path.join(current_config.upperdir(), self.name)
        self.workdir =  path.join(current_config.workdir(), self.name)
        self.mergeddir = path.join(current_config.mergeddir(), self.name)

        # Create directories if they don't exist
        for p in [self.workdir, self.upperdir, self.mergeddir]:
            if not path.exists(p):
                makedirs(p)
        
        # Get the Docker network
        # TODO: get network name from config
        self.docker_network = client.networks.list(names=["bridge"])[0]

        # Check if container exists and load it
        try:
            self.docker_container = client.containers.get(self.name)

            if self.status() != Container.Status.RUNNING:
                self.start()
        except:
            # TODO: get network name from config
            # Create a new container if it doesn't exist
            self.docker_network = client.networks.list(names=["bridge"])[0]
            self.docker_container = client.containers.run(
                current_config.apps()[app]["container"],
                detach=True,
                auto_remove=True,
                name=self.name,
                volumes=[f"{self.mergeddir}:{current_config.apps()[app]["mergedestination"]}"],
                cap_add=current_config.apps()[app]["caps"],
                devices=current_config.apps()[app]["devices"],
                environment=current_config.apps()[app]["env"],
                network=self.docker_network.name
            )

    def status(self: 'Container') -> 'Container.Status':
        """
        Get the container status.
        
        Returns:
            Container.Status: Current status
        """
        try:
            if self.docker_container is None:
                return Container.Status.UNINITIALIZED

            if not self.docker_container or not path.ismount(self.mergeddir):
                return Container.Status.UNINITIALIZED
            elif not self.docker_container.status and path.ismount(self.mergeddir):
                return Container.Status.CREATED
            else:
                return Container.Status.from_docker(self.docker_container.status)
        except Exception as e:
            return Container.Status.UNINITIALIZED

    def start(self: 'Container') -> bool:
        """
        Start the container.
        
        Returns:
            bool: True if started successfully
        """
        # Create a new mount
        mntsuccess = overlaymount(self.mergeddir, [current_config.apps()[self.appname]["lowerdir"]], upperdir=self.upperdir, workdir=self.workdir)

        if not mntsuccess:
            raise Exception(f"Failed to mount '{self.mergeddir}'. Aborting '{self.name}'!")

        self.docker_container.start()
        return self.docker_container is not None

    def logs(self: 'Container'):
        """
        Get the container logs.
        
        Returns:
            bytes: Container logs
        """
        if not self.docker_container:
            return None
        return self.docker_container.logs(stream=True)

    def stop(self: 'Container') -> bool:
        """
        Stop the container.
        
        Returns:
            bool: True if stopped successfully
        """
        if not self.docker_container:
            return True
        else:
            self.docker_container.stop(timeout=120)
            self.docker_container = None
        if (not path.exists(self.mergeddir)) or (not path.ismount(self.mergeddir)):
            return True
        
        umountsuccess = unmount(self.mergeddir)

        if not umountsuccess:
            raise Exception(f"Failed to unmount '{self.mergeddir}'. Aborting stop '{self.name}'!")
        
        return not path.ismount(self.mergeddir)

    def destroy(self: 'Container') -> bool:
        """
        Destroy the container.
        
        Returns:
            bool: True if destroyed successfully
        """
        if not self.stop():
            return False
        
        try:
            shutil.rmtree(self.mergeddir)
            shutil.rmtree(self.workdir)
            return True
        except:
            print("[ERR] Failed to rm temp paths.")
            return False
    
    @classmethod
    def enumerate(cls):
        """
        Enumerate all containers.
        
        Returns:
            list[Container]: List of containers
        """
        all = list(filter(lambda cont: cont.name.startswith(f"{current_config.docker_prefix()}_"), client.containers.list()))

        def _map(dcont:docker.models.containers.Container):
            email = dcont.name[len(current_config.docker_prefix()):]
            email = email.split("_")[1:][:len(current_config.email_suffix())]
            appname = email[0]
            safesuffix = current_config.email_suffix().replace(".", ".").replace("@", ".")
            email = f"{".".join(email[1:]).replace(safesuffix, current_config.email_suffix())}"

            return Container(email, appname)

        all = list(map(_map, all))
        return all

    @classmethod
    def get_container_name(self, appname:str, email:str):
        safeemail = email.replace('@','_').replace('.', '_')
        return f"{current_config.docker_prefix()}_{appname}_{safeemail}"

    def __str__(self):
     return self.name
