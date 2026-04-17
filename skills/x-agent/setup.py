from setuptools import find_packages, setup

setup(
    name="x-agent",
    version="1.0.0",
    description="Multi-platform trend research & AI content generation for X/Twitter",
    author="sheldon010507-collab",
    packages=find_packages(),
    py_modules=["main"],
    install_requires=[
        "anthropic>=0.20.0",
        "openai>=1.0.0",
        "aiohttp>=3.9.0",
        "python-dotenv>=1.0.0",
        "playwright>=1.40.0",
        "playwright-stealth>=1.0.6",
    ],
    extras_require={
        "full": [
            "praw>=7.7.0",
            "pytrends>=4.9.0",
            "groq>=0.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "x-agent=main:main",
        ],
    },
    python_requires=">=3.11",
    license="MIT",
)
