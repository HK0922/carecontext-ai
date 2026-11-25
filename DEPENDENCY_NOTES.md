# Dependency update notes - 2026-11-24

The following direct dependency versions were verified against official package release listings on PyPI:

| Package | Version | Notes |
|---|---|---|
| FastAPI | 0.165.0 | Python 3.14 and 3.15 classifiers |
| Uvicorn | 0.54.0 | Published support through Python 3.14; test 3.15 via CI |
| HTTPX with SOCKS | 0.28.1 | Stable release; used by API and model adapter |
| Pydantic | 2.14.4 | Python 3.14/3.15 support; platform-specific core wheel resolved by pip |
| pypdf | 7.1.1 | Current major version; text extraction API remains PdfReader; recheck PDFs during CI |
| pytest (dev) | 9.2.0 | Supports Python 3.14 and 3.15 |

`pyproject.toml` pins direct versions. `requirements.txt` installs the package and test extras, and pip selects transitive distributions for the platform rather than imposing Linux-generated wheels on macOS.

The authoring environment could not download new Python versions or install updated dependencies. Functional tests were run against the available Python 3.13 stack. Please use the GitHub Actions matrix to validate clean environment installs on Python 3.11-3.15 before publishing or relying on the refreshed dependency set.
