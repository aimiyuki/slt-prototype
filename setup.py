from setuptools import setup, find_packages

setup(
    name="slt",
    packages=find_packages(),
    install_requires=[
        "gensim",
        "spacy",
        "flask",
    ],
    extras_require={
        "dev": [
            "pylint",
            "ipython",
            "python-dotenv",
        ],
        "deploy": [
            "gunicorn",
        ]
    }
)
