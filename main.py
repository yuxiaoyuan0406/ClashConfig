import yaml
import argparse

def get_config():
    import os
    import requests
    proxy = {
        "http": None,
        "https": None,
    }
    url = os.environ.get('CLASH_URL')
    if url is None:
        print("Env para `CLASH_URL` not set")
        return {}

    # download file without proxy
    session = requests.Session()
    session.trust_env = False
    response = session.get(url)
    
    if response.status_code == 200:
        config = yaml.safe_load(response.content)
        if type(config) is dict:
            return config
    return {}


def main():
    parser = argparse.ArgumentParser(description="Set clash config filr.")

    parser.add_argument('--input', help="Directory to input file.", default='config.yaml')
    parser.add_argument('--output', help="Directory to output file.", default="output.yaml")
    parser.add_argument('--update', help='Update from env.CLASH_URL', action='store_true')
    # parser.add_argument('--verbose', help="增加输出的详细程度", action='store_true')

    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    do_update = args.update
    
    if do_update:
        data = get_config()
        if data:
            pass
        else:
            print('Update fail, check internet connection or config link.')
            raise ConnectionError(f"Connection error or invalid link.")
            # return
    else:
        # read from YAML file
        with open(input_file, 'r') as file:
            data = yaml.safe_load(file)
            file.close()

    # default proxy group
    default_proxy_group = {
        "name": "default",
        "type": "url-test",
        "url": "http://www.gstatic.com/generate_204",
        "interval": 300,
        "proxies": []
    }

    # edit data
    ## create a auto switch group for United States proxies
    proxy_names = [proxy['name'] for proxy in data['proxies']]
    US_proxy_names = [name for name in proxy_names if 'UnitedStates' in name]
    
    US_proxy_group = dict(default_proxy_group)
    US_group_name = 'US-Auto'
    US_proxy_group['name'] = US_group_name
    US_proxy_group['proxies'] = US_proxy_names

    assert 'proxy-groups' in data
    assert type(data['proxy-groups']) is list
    # if type(data['proxy-groups']) is dict:
    #     data['proxy-groups'] = [ data['proxy-groups'] ]
    proxy_groups_names = [group['name'] for group in data['proxy-groups']]

    try:
        i = proxy_groups_names.index('Proxy')
        data['proxy-groups'][i]['proxies'].append(US_group_name)
    except ValueError:
        select_proxy_group = dict(default_proxy_group)
        select_proxy_group['name'] = 'Proxy'
        select_proxy_group['type'] = 'select'
        select_proxy_group.pop('url', None)
        select_proxy_group.pop('interval', None)
        select_proxy_group['proxies'] = proxy_groups_names
        select_proxy_group['proxies'].append(US_group_name)
        data['proxy-groups'].append(select_proxy_group)

    try:
        i = proxy_groups_names.index(US_group_name)
        data['proxy-groups'][i] = US_proxy_group
    except ValueError:
        data['proxy-groups'].append(US_proxy_group)

    ## change allow lan
    data['allow-lan'] = True
    ## chane log level
    data['log-level'] = 'debug'
    
    # 将修改后的数据写回文件
    with open(output_file, 'w') as file:
        yaml.dump(data, file)
        file.close()

main()
