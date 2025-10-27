from setuptools import setup

setup(
    name="todo-client-mcp",
    version="1.0.0",
    description="Python MCP client for todo-mcp server",
    author="scottseo.tech",
    py_modules=["todoclientmcp"],
    install_requires=[
        "requests>=2.31.0",
        "sseclient-py>=1.8.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
