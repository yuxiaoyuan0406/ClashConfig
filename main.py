import yaml
import argparse

  

def main():
    parser = argparse.ArgumentParser(description="Set clash config filr.")

    parser.add_argument('--input', help="Directory to input file.", default='config.yaml')
    parser.add_argument('--output', help="Directory to output file.", default="output.yaml")
    # parser.add_argument('--verbose', help="增加输出的详细程度", action='store_true')

    args = parser.parse_args()

    input_file = args.input
    output_file = args.output

    # read from YAML file
    with open(input_file, 'r') as file:
        data = yaml.safe_load(file)

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
    
    US_proxy_group = default_proxy_group
    US_proxy_group['name'] = 'US-Auto'
    US_proxy_group['proxies'] = US_proxy_names
    data['proxy-groups'].append(US_proxy_group)
    ## change allow lan
    data['allow-lan'] = True
    ## chane log level
    data['log-level'] = 'debug'
    
    # 将修改后的数据写回文件
    with open(output_file, 'w') as file:
        yaml.dump(data, file)

main()
