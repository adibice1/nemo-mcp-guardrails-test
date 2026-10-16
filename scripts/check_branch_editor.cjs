/* Exercise actual TS/TSX exports and rendered control handlers without a live backend. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {createRequire} = require("node:module");
const root = path.resolve(__dirname, "../frontend");
const frontendRequire = createRequire(path.join(root, "package.json"));
const ts = frontendRequire("typescript");
const loaded = new Map();

function load(relative) {
  const filename = path.join(root, relative);
  if (loaded.has(filename)) return loaded.get(filename);
  const source = ts.transpileModule(fs.readFileSync(filename, "utf8"), {compilerOptions: {
    module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2020,
  }}).outputText;
  const exports = {};
  loaded.set(filename, exports);
  const requireExport = name => name === "@/lib/branch-conditions" ? load("lib/branch-conditions.ts") : frontendRequire(name);
  new Function("exports", "require", source)(exports, requireExport);
  return exports;
}

const {parseBranchConditions, serializeBranchConditions, formatBranchConditions, MERGE_BRANCH_NOTICE} = load("lib/branch-conditions.ts");
const {BranchConditionEditor} = load("components/policies/branch-condition-editor.tsx");

function elements(node) {
  if (!node || typeof node !== "object") return [];
  if (Array.isArray(node)) return node.flatMap(elements);
  return [node, ...elements(node.props?.children)];
}

let value = "";
const render = (merge = false) => BranchConditionEditor({value, merge, onChange: next => { value = next; }});
const controls = () => elements(render());
const checkbox = index => controls().filter(node => node.type === "input" && node.props.type === "checkbox")[index];
const control = label => controls().find(node => node.props?.["aria-label"] === label);

checkbox(0).props.onChange({target: {checked: true}});
assert.equal(value, 'source_branch = ""'); // Intermediate empty input remains editable.
control("source_branch name").props.onChange({target: {value: "staging"}});
control("source_branch comparison").props.onChange({target: {value: "!="}});
checkbox(1).props.onChange({target: {checked: true}});
control("target_branch name").props.onChange({target: {value: "production"}});
assert.equal(value, 'source_branch != "staging" AND target_branch = "production"');
assert.equal(serializeBranchConditions(parseBranchConditions(value)), value);
assert.equal(formatBranchConditions(value),
  'The source branch is not "staging" and the target branch is "production".');
assert.equal(formatBranchConditions('target_branch = "Production"'),
  'The target branch is "Production".');
assert.equal(formatBranchConditions(""), null);
assert.equal(formatBranchConditions('number = 17'), null);
assert.equal(formatBranchConditions('source_branch = ""'),
  'The source branch is (choose a branch).');
assert.equal(control("source_branch name").props.value, "staging");
checkbox(0).props.onChange({target: {checked: false}});
assert.equal(value, 'target_branch = "production"');
assert.equal(parseBranchConditions('source_branch = "release AND ship"')[0].value, "release AND ship");
assert.equal(parseBranchConditions('source_branch = "a" OR target_branch = "b"'), null);
assert.equal(parseBranchConditions('source_branch = "a" AND source_branch = "b"'), null);
assert.equal(parseBranchConditions('source_branch = "a" AND'), null);
value = "legacy condition whose intent must not change";
assert.equal(elements(render()).filter(node => node.type === "input").length, 0);
assert.equal(value, "legacy condition whose intent must not change");
elements(render()).find(node => node.type === "button").props.onClick();
assert.equal(value, 'source_branch = ""');
const markup = frontendRequire("react-dom/server").renderToStaticMarkup(render(true));
assert.ok(markup.includes(MERGE_BRANCH_NOTICE));
assert.ok(markup.includes("aria-label"));
console.log("Branch editor passed: rendered control events, edit round trips, legacy preservation and merge notice.");
