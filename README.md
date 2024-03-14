# SLT

This is a prototype built for my bachelor thesis: [Same Language Translator
—Reformulating Complex Expressions into Plain Words—](https://github.com/tmicltw/slt-prototype/releases/download/v1.0/bachelor-thesis.pdf)

It takes as input a complex Japanese sentence and transforms it in a simpler one.
A demo is available at the following URL:

https://slt.miyuki.ai/

and the API is exposed at:

https://slt.aimiyuki.me/translate

and can be used as follows:
```
```bash
curl -H "Content-Type: application/json" -d '{"sentence": "本日は友人とお食事した後に、大学に参りました"}' https://slt.aimiyuki.me/translate
```

## Setup

```
pip install -e .[dev]
python -m spacy download ja_core_news_sm
```

## Running webserver

```
flask run # add -h 0.0.0.0 to listen to all interfaces
```
