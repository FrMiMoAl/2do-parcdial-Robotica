from setuptools import find_packages, setup

package_name = 'ejercicio3_nav_agent'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='franco',
    maintainer_email='32112849+FrMiMoAl@users.noreply.github.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "simple_agent = ejercicio3_nav_agent.simple_agent:main",
            "q_learning_agent = ejercicio3_nav_agent.q_learning_agent:main",
        ],
    },
)
