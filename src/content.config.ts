import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// One markdown file per research project in src/content/research/.
// The four thesis steps carry `step` (01–04); other entries are listed under earlier work.
const research = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/research' }),
  schema: z.object({
    title: z.string(),
    order: z.number(),
    step: z.string().optional(),
    stage: z.string().optional(),
    scale: z.string(),
    data: z.string().optional(),
    with: z.string().optional(),
    status: z.string(),
    status_kind: z.enum(['published', 'review', 'progress', 'planned']).default('published'),
    summary: z.string(),
    hook: z.string().optional(),
    key: z.object({ value: z.string(), label: z.string() }).optional(),
    sep: z.number().min(0).max(1).default(1),
    sep_label: z.string().optional(),
    figure: z.string().optional(),
    figure_caption: z.string().optional(),
    publications: z.array(z.string()).default([]),
    explorer: z.string().url().optional(),
    internal_results: z.string().url().optional(),
  }),
});

export const collections = { research };
