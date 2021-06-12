lint:
	black --line-length=120 kedro_lsp
	pylint -j 0 kedro_lsp
