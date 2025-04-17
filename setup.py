from setuptools import setup, find_packages

setup(
    name="koelingo",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pyaudio",
        "numpy",
    ],
    description="KoeLingo - Japanese speech-to-text and translation tool",
    author="KoeLingo Team",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: C++",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
)