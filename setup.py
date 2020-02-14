import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cci_tiger_json",
    version="0.0.1",
    author="Richard Smith",
    author_email="richard.d.smith@stfc.ac.uk",
    description="description",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cedadev/cci_tagger_json.git",
    packages=setuptools.find_packages(),
    package_data={
           'LICENSE',
    },
    python_requires='>=3.6',
)
