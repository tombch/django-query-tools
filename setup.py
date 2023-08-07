import setuptools
from pathlib import Path

directory = Path(__file__).parent
long_description = (directory / "README.md").read_text()

exec(open("django_query_tools/version.py").read())

setuptools.setup(
    name="django_query_tools",
    author="Thomas Brier",
    version=__version__,  # type: ignore
    packages=setuptools.find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
)
