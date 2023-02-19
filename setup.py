import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lywsd03mmc",
    version="0.2.1",
    author="Duncan Barclay",
    author_email="duncan@duncanbarclay.uk",
    description="Xiaomi Mijia LYWSD03MMC sensor library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/uduncanu/lywsd03mmc",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.6',
    install_requires=['lywsd02==0.0.9'],
    scripts=['scripts/lywsd03mmc', 'scripts/lywsd03mmc2csv'],
)
