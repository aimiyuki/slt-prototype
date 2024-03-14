from setuptools import setup, find_packages


setup(
    name="slt",
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "gensim",
        "spacy",
        "flask",
        "romkan",
        "python-dotenv",
        "sklearn",
        "flask-cors",
    ],
    extras_require={
        "dev": [
            "pylint",
            "ipython",
            "black",
        ],
        "deploy": [
            "gunicorn",
        ],
    },
)
