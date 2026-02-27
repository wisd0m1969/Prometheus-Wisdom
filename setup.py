from setuptools import setup, find_packages

setup(
    name="prometheus-wisdom",
    version="1.0.0",
    description="AI Companion for Humanity — Open Source, Multilingual, Free",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Project PROMETHEUS",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "langchain>=0.3.0",
        "langchain-community>=0.3.0",
        "langchain-google-genai>=2.0.0",
        "langchain-ollama>=0.2.0",
        "chromadb>=0.5.0",
        "neo4j>=5.0.0",
        "streamlit>=1.40.0",
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.32.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
        "plotly>=5.24.0",
    ],
    entry_points={
        "console_scripts": [
            "wisdom=wisdom.body.app:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
