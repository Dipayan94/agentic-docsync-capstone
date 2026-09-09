# DocSync - API Documentation Generator

DocSync is a CLI tool that generates and updates markdown API documentation from OpenAPI JSON files.

## Features

- Generate markdown documentation from OpenAPI 3.x schemas
- Preserve custom documentation content using marker-based insertion
- Deterministic output with stable sorting
- Support for dry-run mode
- Multiple report formats (markdown and JSON)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Sync Command

```bash
python -m docsync sync --schema <openapi.json> --docs <existing_docs.md> --output <output.md>
```

### Command-Line Options

- `--schema`: Path to OpenAPI JSON schema file (required)
- `--docs`: Path to existing documentation file (required)
- `--output`: Path to output documentation file (required)
- `--dry-run`: Preview changes without writing output file
- `--verbose`: Enable verbose output
- `--format`: Report output format - `markdown` (default) or `json`

### Examples

#### Generate documentation with dry-run

```bash
python -m docsync sync \
  --schema openapi.json \
  --docs docs/api.md \
  --output docs/api.md \
  --dry-run
```

#### Generate documentation with JSON report

```bash
python -m docsync sync \
  --schema openapi.json \
  --docs docs/api.md \
  --output docs/api.md \
  --format json
```

## Marker Policy

DocSync uses HTML comment markers to preserve custom documentation content:

- **Markers**: `<!-- DOCSYNC:BEGIN GENERATED -->` and `<!-- DOCSYNC:END GENERATED -->`
- **Both markers exist**: Content between markers is replaced with new generated content
- **No markers**: Generated content is appended at the end of the file
- **Malformed markers**: Operation fails with exit code 2 (validation failure)

### Example Documentation Structure

```markdown
# My API Documentation

This is my custom introduction that won't be overwritten.

<!-- DOCSYNC:BEGIN GENERATED -->
Generated API documentation will appear here
<!-- DOCSYNC:END GENERATED -->

## Additional Notes

More custom content that will be preserved.
```

## Exit Codes

- `0`: Success
- `1`: Operational error (e.g., file not found, cannot read file)
- `2`: Validation failure (e.g., invalid JSON, malformed markers, missing required fields)

## Testing

Run the test suite:

```bash
python -m pytest -q
```

## Development

This project structure:

```
docsync/
  __init__.py
  __main__.py
  cli.py              # CLI entrypoint
  exceptions.py       # Custom exceptions
  models.py           # Data models
  openapi_parser.py   # OpenAPI parsing logic
  markdown_generator.py  # Markdown generation
  markers.py          # Marker-based merge logic
  reporting.py        # Report generation
tests/
  fixtures/
    sample_openapi.json
  test_openapi_parser.py
  test_markdown_generator.py
  test_markers.py
  test_cli.py
```

---

# Python/FastAPI Tutorial for Visual Studio Code
This sample contains the completed program from the tutorial: [FastAPI in Visual Studio Code](https://code.visualstudio.com/docs/python/tutorial-fastapi). Immediate steps are not included.

## Run the app using GitHub Codespaces
[GitHub Codespaces](https://github.com/features/codespaces) provides cloud-powered development environments that work how and where you want it to. To learn how to set up a GitHub Codespace for this repository, check the [documentation](https://docs.github.com/en/codespaces/developing-in-codespaces/creating-a-codespace-for-a-repository#creating-a-codespace-for-a-repository).

Once you open this repository in GitHub Codespaces, you can press **F5** to start the debugger and run the application.  

Once it's ready, you will see a notification with a button `Open in the Browser`. Clicking the button will open your application on the browser. You can then add `/docs` to the end of the URL to access the Swagger UI and interact with the application!

## Run the app locally in VS Code
 
There are diffent ways you can run this app locally in VS Code depending on your operating system. To get started, first clone this project on your machine and then open it in VS Code (**File** > **Open Folder...**). 

### Windows
To run this app locally in VS Code on Windows, you can use either [WSL](https://learn.microsoft.com/en-us/windows/wsl/) (Windows Subsystem for Linux) or [Docker](https://www.docker.com/products/docker-desktop). 

#### Docker Containers
1. Make sure you have [Docker installed](https://www.docker.com/products/docker-desktop)
1. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) 
1. Open the Command Palette in VS Code (**View** > **Command Palette...**) and run the "Dev Container: Reopen in Container" command.
1. Press **F5** to debug your application!

#### WSL
1. Make sure you have [WSL installed](https://learn.microsoft.com/en-us/windows/wsl/)
1. Install the [WSL extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl) for VS Code
1. Open the Command Palette in VS Code (**View** > **Command Palette...**) and run the "WSL: Reopen Folder in WSL" command
1. Follow the remaining steps for [macOS/Linux](#macos--linux) below.

### macOS / Linux

1. Install the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) for VS Code 
1. Run the "Python: Create Environment" command in the Command Palette
1. Select `Venv`, the latest available version of Python and then the `requirements.txt` file to install the dependencies.
1. Press **F5** to run your application!

## Contributing
Contributions to the sample are welcome!  When submitting changes, also consider submitting matching changes to the tutorial, the source file for which is [tutorial-fastapi.md](https://github.com/Microsoft/vscode-docs/blob/master/docs/python/tutorial-fastapi.md).

Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot automatically determines whether you need to provide a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions provided by the bot. You will only need to do this once across all repos using our CLA.

## Additional details

* This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
* For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
* Contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
