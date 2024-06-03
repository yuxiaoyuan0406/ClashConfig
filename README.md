# Clash配置文件自动设置

![WTFPL](http://www.wtfpl.net/wp-content/uploads/2012/12/wtfpl-badge-4.png)

- [Clash配置文件自动设置](#clash配置文件自动设置)
  - [Install requirements](#install-requirements)
  - [Usage](#usage)

## Install requirements

```bash
pip install -r requirements.txt
```

## Usage

To get clash config from your clash url:

```bash
python main.py --url https://some.url --output output.yaml
```

To run a flask server and edit your clash config:

```bash
python server.py
# get your config from: http://localhost:6789/?url=https://some.url
```

For safty shit, use Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:6789 server:app
```
