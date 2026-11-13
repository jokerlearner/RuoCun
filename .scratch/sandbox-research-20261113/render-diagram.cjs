// Run the diagram skill's converter with the bundled Node and sharp runtime.
const { registerHooks } = require('node:module');
const { pathToFileURL } = require('node:url');
const sharpPath = 'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-611-0_26.1112.611.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/sharp/dist/index.mjs';
registerHooks({
  resolve(specifier, context, nextResolve) {
    return nextResolve(specifier === 'sharp' ? pathToFileURL(sharpPath).href : specifier, context);
  },
});
require('C:/Users/PC/.agents/skills/baoyu-diagram/scripts/main.ts');
