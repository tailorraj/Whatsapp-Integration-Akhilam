from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in whatsapp_integration/__init__.py
from whatsapp_integration import __version__ as version

setup(
	name="whatsapp_integration",
	version=version,
	description="Whatsapp Automation",
	author="Raaj Tailor",
	author_email="raaj@akhilaminc.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
