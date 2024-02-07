#!/usr/bin/env python3

from bs4 import BeautifulSoup
from common import get_dirs, get_files, dt_pmc, post_sbom
from dotenv import load_dotenv
import json
import os
from packaging.version import Version
import re
import requests
from urllib import request
from sys import argv

load_dotenv()
dt_api_key = os.getenv('DT_API_KEY')

def project_name(link):
    return link.get('title')[:-1]

def maven_projects(pmc):
    # TODO support deeper hierarchies
    def is_direct(name):
        return name.startswith(f'{pmc}-')
    return list(filter(is_direct, list(map(project_name, get_dirs(f'https://repo1.maven.org/maven2/org/apache/{pmc}/')))))

if len(argv)>1:
    pmc = argv[1]
else:
    pmc = 'commons'

if len(argv)>2:
    projects = [ argv[2] ]
elif pmc == 'camel':
    projects = [
      'camel',
      'kamelets/camel-kamelets-parent',
      'quarkus/camel-quarkus',
      'springboot/spring-boot',
    ]
else:
    projects = maven_projects(pmc)

for project in projects:
    friendly_name = 'Apache ' + project.split('/')[-1].replace('-', ' ').title()
    print(project)
    pmc_uuid = dt_pmc(pmc)['uuid']

    index = get_dirs(f'https://repo1.maven.org/maven2/org/apache/{pmc}/{project}')
    def version_name(link):
        return link.get('title')[:-1]
    def is_version(v):
        # TODO support such versions
        return not 'M' in v and not 'incubating' in v and not 'hadoop' in v and not 'milestone' in v and not 'pre' in v
    versions = list(filter(is_version, list(map(version_name, index))))
    versions.sort(key=Version)
    if versions:
        lastVersion = versions[-1]
        print(lastVersion)
        index = get_files(f'https://repo1.maven.org/maven2/org/apache/{pmc}/{project}/{lastVersion}')
        def file_name(link):
            return link.get('title')
        def is_sbom(name):
            return name.endswith('-cyclonedx.json')
        sboms = list(filter(is_sbom, map(file_name, index)))
        if sboms:
            sbom = sboms[0]
            url = f'https://repo1.maven.org/maven2/org/apache/{pmc}/{project}/{lastVersion}/{sbom}'
            post_sbom(pmc, pmc_uuid, friendly_name, lastVersion, url)
