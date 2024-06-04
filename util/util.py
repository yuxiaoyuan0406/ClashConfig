import yaml

'''
A clash config yaml file contain a dict type data.

The data contains a list of which key is "proxies".
Each item defines a identical proxy server with its link and shit.
Each item in that list has a key "name".

The data contains a list of which key is "proxy-groups".
Here you can group some proxies up for better use.
'''

# default proxy group
default_proxy_switch_group = {
    "name": "default-switch",
    "type": "url-test",
    "url": "http://www.gstatic.com/generate_204",
    "interval": 300,
    "proxies": []
}
default_proxy_select_group = {
    "name": "default-select",
    "type": "select",
    "proxies": []
}

def download_config(url: str) -> dict:
    import os
    import requests
    proxy = {
        # "http": "",
        # "https": "",
    }
    assert str is not None

    # download file without proxy
    session = requests.Session()
    # session.trust_env = False
    session.proxies.update(proxy)

    response = None
    try:
        response = session.get(url, timeout=30)
    except requests.exceptions.Timeout:
        ## timeout exception
        print("Connection timeout.")
    except requests.exceptions.RequestException as e:
        ## other exceptions
        print(f'Request exception: {e}')
    
    if response and response.status_code == 200:
        try:
            config = yaml.safe_load(response.content)
        except yaml.YAMLError as e:
            print(f'YAML load exception: {e}')
            return dict({})
        if type(config) is dict:
            return config
    return dict({})

def edit_config(data: dict)->None:
    assert data
    group_proxy_by_name(data)

    add_rule(data)

    ## change allow lan
    data['allow-lan'] = True
    ## chane log level
    data['log-level'] = 'debug'

def add_rule(data: dict)->None:
    assert 'rules' in data
    rule = 'DOMAIN,s.trojanflare.com,DIRECT'
    data['rules'].insert(0, rule)
   
def group_proxy_by_name(data: dict)->None:
    ### get all names
    proxy_names = [proxy['name'] for proxy in data['proxies']]
    ### split names with '-' to get countries
    proxy_country = [name.split('-')[0] for name in proxy_names]
    ### there is a useless proxy has to be removed
    proxy_country = [s for s in proxy_country if ' ' not in s]
    ### create a set to avoid replica
    proxy_country_set = set(proxy_country)

    ### create a empty proxy select group for auto select
    ### all auto switch group will be insert into this group
    semi_auto_switch_group = dict(default_proxy_select_group)
    semi_auto_switch_group['name'] = 'Semi-Auto'
    
    ### all new group has to be inserted
    assert 'proxy-groups' in data
    assert type(data['proxy-groups']) is list
    # if type(data['proxy-groups']) is dict:
    #     data['proxy-groups'] = [ data['proxy-groups'] ]
    proxy_groups_names = [group['name'] for group in data['proxy-groups']]

    for country in proxy_country_set:
        ## determin name
        group_name = '{}-Auto'.format(country)
        ## filter all proxy
        proxies = [name for name in proxy_names if country in name]
        ## create auto switch group
        group = dict(default_proxy_switch_group)
        ## edit new group
        group['name'] = group_name
        group['proxies'] = proxies
        
        ## insert new group into semi-auto group
        semi_auto_switch_group['proxies'].append(group_name)

        ## insert new group into proxy-groups list
        data['proxy-groups'].append(group)
    
    ## insert semi-auto group to default proxy group
    data['proxy-groups'][0]['proxies'].insert(0, semi_auto_switch_group['name'])
    ## insert semi-auto group
    data['proxy-groups'].insert(0, semi_auto_switch_group)
    
