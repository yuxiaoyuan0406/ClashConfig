# Clash配置文件自动设置

![WTFPL](http://www.wtfpl.net/wp-content/uploads/2012/12/wtfpl-badge-4.png)

- [Clash配置文件自动设置](#clash配置文件自动设置)
  - [Install requirements](#install-requirements)
  - [Usage](#usage)

## Install requirements

```bash
pip install requirements.txt
```

## Usage

To simply group some shit:

```bash
python3 main.py --input config.yaml
```

To update from link(env.CLASH_URL):

```bash
# export CLASH_URL="http://your.clash.config/url"
python3 main.py --output config.yaml --update
```
