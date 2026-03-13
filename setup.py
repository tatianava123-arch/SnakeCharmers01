from setuptools import setup, find_packages

setup(
    name="personal-assistant-snakecharmers",  # Назва вашого пакету
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "prompt_toolkit==3.0.52",
        "rich==14.3.3",
    ],
    entry_points={
        'console_scripts': [
            'helper-bot=cli:main',  # Тепер після інсталяції команда 'helper-bot' запустить програму
        ],
    },
    author="SnakeCharmers Team",
    description="CLI Personal Assistant with Address Book and Notebook",
    python_requires='>=3.7',
)