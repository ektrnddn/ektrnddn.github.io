// @ts-check
import { defineConfig } from 'astro/config';

// User site: served at the root of https://ektrnddn.github.io
export default defineConfig({
  site: 'https://ektrnddn.github.io',
  trailingSlash: 'ignore',
});
