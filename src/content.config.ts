import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// One markdown file per research project in src/content/research/.
const research = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/research' }),
  schema: z.object({
    title: z.string(),
    slug: z.string().optional(),
    order: z.number(),
    scale: z.string(),
    status: z.string(),
    summary: z.string(),
    figure: z.string().optional(),
    figure_caption: z.string().optional(),
    publications: z.array(z.string()).default([]),
    explorer: z.string().url().optional(),
    internal_results: z.string().url().optional(),
  }),
});

export const collections = { research };
