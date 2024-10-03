import yaml
import os
import docker
from os import path

class Config:

    vars: any
    title:  str     = lambda self: self.vars['title']
    docker_prefix:  str     = lambda self: self.vars['docker_prefix']
    base_image:     str     = lambda self: self.vars['base_image']
    upperdir:       str     = lambda self: path.abspath(self.vars['upperdir'])
    workdir:        str     = lambda self: path.abspath(self.vars['workdir'])
    mergeddir:      str     = lambda self: path.abspath(self.vars['mergeddir'])
    ldap_server:    str     = lambda self: self.vars['ldap_server']
    ldap_base:      str     = lambda self: self.vars['ldap_base']
    ldap_filter:    str     = lambda self, email: self.vars['ldap_filter'].replace('{{email}}', email)
    ldap_protocol:  int     = lambda self: self.vars['ldap_protocol']
    ldap_upn:       str     = lambda self: self.vars['ldap_upn']
    secret:         str     = lambda self: self.vars['secret']
    email_suffix:   str     = lambda self: self.vars['email_suffix']
    favicon:        str     = lambda self: self.vars['favicon']
    apps:           dict    = lambda self: self.vars['apps']

    def __init__(self, yaml_path):
        self.yaml_path = yaml_path

        with open(yaml_path, mode="r", encoding="utf8") as stream:
            try:
                self.vars = yaml.safe_load(stream)
                print(self.vars)
            except yaml.YAMLError as err:
                raise err

current_config = Config(os.environ.get('VC_APP_CONTAINERS_CONFIG', 'config.yml'))

dockerclient = docker.from_env()
