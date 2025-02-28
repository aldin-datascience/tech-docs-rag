from setuptools import setup

setup(
    name='tech-docs-rag',
    install_requires=[
        'requests~=2.32.3',
        'pyvespa==0.34.0',
        'langchain==0.3.15',
        'langchain-community==0.3.15',
        'unstructured==0.16.14',
        'nltk==3.9.1',
        'fastapi==0.115.6',
        'uvicorn==0.34.0',
        'python-multipart==0.0.20',
        'openai==1.60.0',
        'streamlit==1.41.1',
        'python-dotenv==1.0.1',
        'Markdown==3.7'
    ],
)