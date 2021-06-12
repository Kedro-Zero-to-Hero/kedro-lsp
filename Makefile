lint:
	isort kedro_lsp
	black kedro_lsp
	pylint -j 0 kedro_lsp
