import {copyFile, mkdir} from 'node:fs/promises';
import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import {dirname, resolve} from 'node:path';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const vendor = resolve(root, 'src/vendor');
const sipEntry = resolve(root, 'node_modules/sip.js/lib/index.js');

await mkdir(vendor, {recursive: true});
await build({
  entryPoints: [sipEntry],
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: ['es2020'],
  minify: true,
  legalComments: 'inline',
  outfile: resolve(vendor, 'sip.js'),
});
await copyFile(resolve(root, 'node_modules/sip.js/LICENSE.md'),
               resolve(vendor, 'SIP-JS-LICENSE.md'));
