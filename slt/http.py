from flask import Flask, render_template, request
from gensim.models.keyedvectors import KeyedVectors

from slt import settings
from slt.processor import Processor


processor: Processor = None


def create_app():
    global processor  # pylint: disable=global-statement, invalid-name
    app_ = Flask(__name__)
    w2v = KeyedVectors.load_word2vec_format(settings.W2V_MODEL_PATH, binary=True)
    processor = Processor.load(w2v=w2v)
    return app_


app = create_app()


@app.route("/")
def index():
    sentence = request.args.get("sentence")
    kwargs = {"sentence": sentence}
    if sentence:
        result = processor.process_sentence(sentence)
        kwargs["new_sentence"], kwargs["old_sentence"] = result
    return render_template("index.html", **kwargs)
