from flask import Flask, render_template, request

from gensim.models.keyedvectors import KeyedVectors

from slt.parser import Parser, W2V_MODEL_PATH

_w2v = None


def create_app():
    global _w2v
    app_ = Flask(__name__)
    _w2v = KeyedVectors.load_word2vec_format(W2V_MODEL_PATH, binary=True)
    return app_

app = create_app()

@app.route("/")
def index():
    parser = Parser.load(w2v=_w2v)
    sentence_info = None
    sentence = request.args.get("sentence")
    if sentence:
        new_tokens, old_tokens = parser.process_sentence(sentence)
        sentence_info = format_sentences(new_tokens, old_tokens)
    return render_template("index.html", sentence=sentence, sentence_info=sentence_info)


def format_sentences(new_tokens, old_tokens):
    new_tokens_with_meta = []
    old_tokens_with_meta = []
    for new_token, old_token in zip(new_tokens, old_tokens):
        changed = new_token != old_token
        new_tokens_with_meta.append({"token": new_token, "status": "added" if changed else "unchanged"})
        old_tokens_with_meta.append({"token": old_token, "status": "removed" if changed else "unchanged"})
    return {"old_tokens": old_tokens_with_meta, "new_tokens": new_tokens_with_meta}
