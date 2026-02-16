import { defineConfig } from 'orval';

export default defineConfig({
  harmony: {
    output: {
      mode: 'tags-split',
      target: 'src/lib/api/',
      schemas: 'src/lib/api/model',
      client: 'fetch',
      prettier: true,

      override: {
        mutator: {
          path: './src/lib/utils/injection.ts',
          name: 'inject',
        },
      },
    },

    input: {
      target: './openapi.json', 
    },
  },
});