import setuptools

exec(open("django_query_tools/version.py").read())

setuptools.setup(
    name="django_query_tools",
    author="Thomas Brier",
    version=__version__,  # type: ignore
    packages=setuptools.find_packages(),
)