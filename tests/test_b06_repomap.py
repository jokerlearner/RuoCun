"""Frozen repomap extraction/graph/render/index public-source expectations."""

import asyncio

import pytest


def test_source_typescript_definitions_imports_and_non_function_constants(tmp_path):
    from ruocun.repomap.extract import extractFile
    from ruocun.repomap.languages import langForFile

    file = tmp_path / "a.ts"
    file.write_text('''
import { foo } from "./other";
export interface Config { a: number; }
export class Service {
  method(arg: string): void {}
}
export function standalone(a: number): boolean { return true; }
const arrow = (n: number) => n + 1;
const plain = 123;
enum Color { Red }
''', encoding="utf-8")
    result = asyncio.run(extractFile(file, langForFile(file.name)))
    assert result is not None
    names = {symbol.name for symbol in result.defs}
    assert {"Config", "Service", "method", "standalone", "arrow", "Color"} <= names
    assert "plain" not in names and "foo" in result.refs and "./other" in result.importSources


def test_source_graph_import_edges_rank_and_render_budget():
    from ruocun.repomap.extract import FileExtract, SymbolDef
    from ruocun.repomap.graph import FileEntry, buildGraph
    from ruocun.repomap.render import RenderedFile, renderRepoMap

    def entry(path, names, refs=(), sources=()):
        return FileEntry(path, FileExtract([SymbolDef(name, "function_declaration", 1, f"function {name}() {{}}")
                                            for name in names], list(refs), list(sources)))
    graph = buildGraph([entry("core.ts", ["coreFn"]), entry("b.ts", ["bFn"], ["coreFn"]),
                        entry("a.ts", [], ["coreFn", "bFn"]), entry("c.ts", [], ["coreFn"]),
                        entry("lonely.ts", ["lonely"])])
    assert graph.ranks["core.ts"] > graph.ranks["b.ts"] > graph.ranks["lonely.ts"] > 0
    assert abs(sum(graph.ranks.values()) - 1) < 0.00001
    graph = buildGraph([entry("src/sub/inner.ts", [], sources=[".././api"]), entry("src/api/index.ts", ["apiFn"])])
    assert "src/api/index.ts" in graph.edges["src/sub/inner.ts"]
    assert not buildGraph([entry("a.ts", ["selfRef"], ["selfRef"])]).edges
    assert buildGraph([]).ranks == {}
    files = [RenderedFile(name, [SymbolDef("f", "function", 1, "x" * 300)]) for name in ("a.ts", "b.ts", "c.ts")]
    rendered = renderRepoMap(files, 380)
    assert "a.ts:" in rendered and "b.ts:" in rendered and "c.ts:" not in rendered
    assert "⋮...\n│" in rendered and renderRepoMap([], 2000) == ""


@pytest.mark.parametrize("file,source,names,reference", [
    ("a.py", "import os.path\nfrom typing import List\nclass Dog:\n def bark(self):\n  print('woof')\ndef add(a,b):\n return a+b\n", {"Dog", "bark", "add"}, "List"),
    ("a.go", 'package main\nimport "github.com/x/y/util"\ntype Server struct {Port int}\nfunc NewServer() *Server {return nil}\nfunc (s *Server) Run() error {return nil}\n', {"Server", "NewServer", "Run"}, "util"),
    ("a.rs", "use std::collections::HashMap;\npub struct Cache {inner: HashMap<String,String>}\npub trait Store {fn get(&self,k:&str)->Option<String>;}\nimpl Cache {pub fn new()->Self {todo!()}}\npub fn build()->Cache {todo!()}\n", {"Cache", "Store", "new", "build"}, "HashMap"),
    ("A.java", "import java.util.List;\npublic class Sample {public void run() {}}\ninterface Listener {void onEvent(int x);}\nenum Status {OK}\n", {"Sample", "run", "Listener", "Status"}, "List"),
    ("a.tsx", "export function App(props: {title:string}) {return null;}\n", {"App"}, None),
    ("a.js", "export function example() {return 1;}\n", {"example"}, None),
])
def test_source_language_fixtures_and_native_grammar_binding(file, source, names, reference, tmp_path):
    from ruocun.repomap.extract import extractFile
    from ruocun.repomap.languages import langForFile

    path = tmp_path / file
    path.write_text(source, encoding="utf-8")
    result = asyncio.run(extractFile(path, langForFile(file)))
    assert result is not None and names <= {definition.name for definition in result.defs}
    if reference:
        assert reference in result.refs


def test_source_map_build_rank_cache_budget_and_notice(tmp_path):
    from ruocun.repomap.index import buildRepoMap, repoMapTokenBudget, wrapRepoMapNotice

    files = {"core.ts": "export interface Config {a:number;}\nexport class Engine {start():void {}}\n",
             "app.ts": 'import {Config,Engine} from "./core";\nexport function main(c:Config):Engine {return new Engine();}\n',
             "util.ts": 'import {Engine} from "./core";\nexport class Helper {wrap(e:Engine):Engine {return e;}}\n',
             "unrelated.ts": "export function lonelyThing():void {}\n", "README.md": "# readme",
             "bundle.min.js": "function a(){}"}
    for file, text in files.items():
        (tmp_path / file).write_text(text, encoding="utf-8")
    first = asyncio.run(buildRepoMap(tmp_path, 4096))
    assert first.fileCount == 4 and not first.truncated
    assert "README" not in first.text and "bundle.min.js" not in first.text
    assert first.text.index("core.ts:") < first.text.index("app.ts:")
    assert "class Engine" in first.text
    assert asyncio.run(buildRepoMap(tmp_path, 4096)).text == first.text
    assert "core.ts:" in asyncio.run(buildRepoMap(tmp_path, 300)).text
    for values, expected in [({}, 2048), ({"RUOCUN_REPO_MAP_TOKENS": "4096"}, 4096),
                             ({"RUOCUN_REPO_MAP_TOKENS": "0"}, 0), ({"RUOCUN_REPO_MAP_TOKENS": "abc"}, 2048)]:
        assert repoMapTokenBudget(values) == expected
    assert "已扫描 42 个文件" in wrapRepoMapNotice("map", False, 42)
    assert "</codebase-map>" in wrapRepoMapNotice("map", True, 42)
    assert wrapRepoMapNotice("", False, 0) == ""
