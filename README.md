# Golearn - INFRA BOT

## Install
```bash
$ cp .env.back .env
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r reqs.txt
```

## Run
```bash
echo "TOKEN=''\nCONNECTION_STRING=''\nSUDO=''" > .env
python3 main.py
```