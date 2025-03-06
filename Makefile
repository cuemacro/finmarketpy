.DEFAULT_GOAL := help

venv:
	@curl -LsSf https://astral.sh/uv/install.sh | sh
	@uv venv --python '3.9'


.PHONY: install
install: venv ## Install a virtual environment
	@uv pip install --upgrade pip
	@uv sync -vv --frozen

	#@uv pip install -r requirements.txt


.PHONY: fmt
fmt: venv ## Run autoformatting and linting
	@uv pip install pre-commit
	@uv run pre-commit install
	@uv run pre-commit run --all-files


.PHONY: clean
clean:  ## Clean up caches and build artifacts
	@git clean -X -d -f


.PHONY: help
help:  ## Display this help screen
	@echo -e "\033[1mAvailable commands:\033[0m"
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' | sort


#.PHONY: marimo
#marimo: install ## Install Marimo
#	@uv pip install marimo
#	@uv run marimo edit book/marimo


.PHONY: test
test: install  ## Run pytests
	@uv pip install pytest
	@uv run pytest tests
