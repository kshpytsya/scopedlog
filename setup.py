from setuptools import setup, find_packages

setup(
    name="scopedlog",
    description="library for scoped logging on top of structlog (or similar sinks)",
    long_description=open("README.md").read(),  # no "with..." will do for setup.py
    long_description_content_type='text/markdown; charset=UTF-8; variant=GFM',
    license="MIT",
    author="Kyrylo Shpytsya",
    author_email="kshpitsa@gmail.com",
    url="https://github.com/kshpytsya/scopedlog",
    setup_requires=["setuptools_scm"],
    extras_require={
        "structlog": ["structlog>=18.1.0,<19"]
    },
    use_scm_version=True,
    python_requires=">=3.6, <=3.7",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
