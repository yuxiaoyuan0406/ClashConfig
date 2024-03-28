import yaml
import argparse

from util import util

def main():
    parser = argparse.ArgumentParser(description="Set clash config filr.")

    # parser.add_argument('--input', help="Directory to input file.", default='config.yaml')
    parser.add_argument('--url', help="Url to get shit from")
    parser.add_argument('--output', help="Directory to output file.", default="output.yaml")
    # parser.add_argument('--update', help='Update from env.CLASH_URL', action='store_true')
    # parser.add_argument('--verbose', help="增加输出的详细程度", action='store_true')

    args = parser.parse_args()

    # input_file = args.input
    # output_file = args.output
    # do_update = args.update

    # edit_config(args.url, args.output)
    data = util.download_config(args.url)
    util.edit_config(data)

    with open(args.output, 'w') as file:
        yaml.dump(data, file)
        file.close()



if __name__ == '__main__':
    main()
