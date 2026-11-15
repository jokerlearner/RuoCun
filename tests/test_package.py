"""R-15: installed public metadata and packaged resources, independent of the cwd."""

from importlib import metadata, resources

import ruocun


def test_public_version_matches_installed_distribution_metadata():
    assert metadata.version("ruocun") == "0.9.0"
    assert ruocun.__version__ == metadata.version("ruocun")


def test_product_distribution_needs_no_development_runtime_dependencies():
    product = metadata.distribution("ruocun")
    requirements = {item.lower().replace("_", "-").replace(" ", "").replace("'", '"')
                    for item in (product.requires or ())}
    assert {item for item in requirements if ";" not in item} == {
        "prompt-toolkit==3.0.52", "rich==14.1.0", "wcwidth==0.9.4", "mcp==1.30.0", "tree-sitter==0.25.2", "tree-sitter-go==0.25.0", "tree-sitter-java==0.23.5", "tree-sitter-javascript==0.25.0", "tree-sitter-python==0.25.0", "tree-sitter-rust==0.24.0", "tree-sitter-typescript==0.23.2"}
    assert {item for item in requirements if ";" in item} == {
        'opentelemetry-api==1.45.2;extra=="observation"',
        'opentelemetry-sdk==1.45.2;extra=="observation"',
        'opentelemetry-exporter-otlp-proto-http==1.45.2;extra=="observation"',
        'opentelemetry-exporter-http-transport==0.66b2;extra=="observation"',
        'opentelemetry-exporter-otlp-common==0.66b2;extra=="observation"'}
    names = {str(path).replace("\\", "/") for path in product.files}
    assert "ruocun/resources/help.zh-CN.txt" in names
    assert not any(name.startswith(("tests/", "oracle/", "ruocun_acceptance/", ".scratch/"))
                   for name in names)
    assert any(name.endswith("/licenses/LICENSE") for name in names)
    assert any(name.endswith("/licenses/NOTICE.md") for name in names)
    assert any(name.endswith("/licenses/THIRD-PARTY-LICENSES.txt") for name in names)
    help_text = resources.files("ruocun").joinpath("resources/help.zh-CN.txt").read_text("utf-8")
    assert "用法：ruocun [选项] [提示词]" in help_text
