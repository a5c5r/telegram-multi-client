from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="telegram-multi-client",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Telegram Multi-Client Library with Arabic Commands",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/telegram-multi-client",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "telethon>=1.28.5",
        "aiohttp>=3.8.0",
    ],
)
