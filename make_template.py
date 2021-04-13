import requests
from bs4 import BeautifulSoup
import yaml

print("*** Starting LSIO Template Generation ***")

_ignored_apps = []
example_list = []
app_example_list = requests.get("https://fleet.linuxserver.io/api/v1/images")
json_list = app_example_list.json()
for repo in json_list['data']['repositories']:
    if repo == 'lsiobase':
        continue
    print("* Getting Apps from the "+repo+" repo.")

    for _app in json_list['data']['repositories'][repo]:
        print("  - "+_app['name'])
        app_example_details = requests.get("https://fleet.linuxserver.io/image?name=linuxserver/"+_app['name'])
        app_example_content = app_example_details.content.decode("ISO-8859-1")
        app_example_soup = BeautifulSoup(app_example_content, features="html.parser")
        app_example_logo = app_example_soup.find_all('img', alt='Title logo')
        _app_example = app_example_soup.find_all('code', class_='language-yaml')
        if len(_app_example) > 0:
            if app_example_logo:
                app_example = str(_app_example[0].contents[0]).replace('---\n','').replace("\\'", '').replace('\\t', '') + '    logo: '+'https://fleet.linuxserver.io'+ app_example_logo[0].attrs['src']+'\n'
            else:
                app_example = str(_app_example[0].contents[0]).replace('---\n','').replace("\\'", '').replace('\\t', '')
            if _app['name'] not in _ignored_apps:
                example_list.append(app_example)
            else:
                continue
        else:
            continue
print("* Formatting Template")
f = open('lsio_template.yaml', 'w')
_formatted_example_list = yaml.safe_load_all(yaml.safe_dump(example_list))


master_app_list = list(_formatted_example_list)

final_template = []
for _app in master_app_list:
    for __app in _app:
        app = yaml.safe_load(str(__app).replace("\t",''))
        app['type'] = app.pop('version')
        for _service in app['services']:
            app['image'] = app['services'][_service]['image']
            app['name'] = app['services'][_service]['container_name']
            app['title'] = str(app['services'][_service]['container_name']).capitalize()
            app['platform'] = 'linux'
            print("  - "+app['name'])
            app['restart_policy'] = 'unless-stopped'

            if 'logo' in app['services'][_service].keys():
                app['logo'] = app['services'][_service]['logo']

            if 'environment' in app['services'][_service].keys():
                env_list = []
                for _environment in app['services'][_service]['environment']:
                    if '=' in _environment:
                        environment = _environment.split('=')
                        _name = environment[0]
                        environment[1] = '!'+environment[0]
                        _default = environment[1]
                        env_list.append({'name': _name, 'label': _name, 'default': _default})
                    elif _environment == 'TZ':
                        _default = '!TZ'
                        env_list.append({'name': _environment, 'default': _default})
                    else:
                        env_list.append({'name':_environment, 'label': _environment})
                app['env'] = env_list

            if 'volumes' in app['services'][_service].keys():
                volume_list = []
                for _volume in app['services'][_service]['volumes']:
                    volume = _volume.split(':')
                    container = volume[1]
                    bind = '!'+volume[1].replace('/','')
                    volume_list.append({'container': container, 'bind': bind})
                app['volumes'] = volume_list

            if 'ports' in app['services'][_service].keys():
                port_list = []
                for _port in app['services'][_service]['ports']:
                    port_list.append(_port)
                app['ports'] = port_list

            del app['services']

            final_template.append(app)


f.write(yaml.safe_dump(final_template))
print('done')
