from setuptools import setup

setup(
    name="my_policy_node",
    version="0.0.1",
    packages=["my_policy_node"],
    package_dir={"my_policy_node": "my_policy_node"},
    install_requires=[
        "numpy",
        "opencv-python-headless",
        "tqdm",
        "pyyaml",
    ],
    zip_safe=False,

    entry_points={
        'console_scripts': [
            'my_policy_node = my_policy_node.my_policy_node:main', # Your existing node
            'simple_insertion = my_policy_node.simple_insertion:main', # Add this line
        ],
    },


)
