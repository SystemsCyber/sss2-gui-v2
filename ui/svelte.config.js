import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// adapter-node: the UI is built and run as a standalone Node server on the
		// Raspberry Pi (the "frontend" systemd service). `npm run build` emits ./build,
		// run with `node build`. PORT/HOST/ORIGIN are read from the environment.
		adapter: adapter()
	}
};

export default config;
