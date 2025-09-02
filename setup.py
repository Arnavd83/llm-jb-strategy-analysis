from setuptools import find_packages, setup
import os

def read_requirements():
    """Read requirements from deps/requirements-min.txt"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'deps', 'requirements-min.txt')
    with open(requirements_path, 'r') as f:
        requirements = []
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                requirements.append(line)
        return requirements

setup(
    name='pair',
    packages=find_packages(),
    install_requires=read_requirements(),
)