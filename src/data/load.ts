// Loads the YAML content files at build time. Import from here, never from the .yaml directly.
import yaml from 'js-yaml';
import profileRaw from './profile.yaml?raw';
import publicationsRaw from './publications.yaml?raw';
import talksRaw from './talks.yaml?raw';
import educationRaw from './education.yaml?raw';
import grantsRaw from './grants.yaml?raw';
import experienceRaw from './experience.yaml?raw';
import awardsRaw from './awards.yaml?raw';
import factsRaw from './facts.yaml?raw';
import photosRaw from './photos.yaml?raw';
import projectsRaw from './projects.yaml?raw';
import movieRaw from './movie.yaml?raw';
import timelineRaw from './timeline.yaml?raw';

function load<T>(raw: string): T {
  return yaml.load(raw) as T;
}

export interface Profile {
  name: string; short_name: string; title: string; affiliation: string; location: string;
  email: string; tagline: string; bio: string; bio_more?: string; advisors: string[];
  photo?: string; photo_alt?: string; greeting: string; intro: string; intro_more?: string;
  hero: { start: string; emphasis: string; end: string; lede: string; figure: string; figure_alt: string; figure_caption: string };
  research_lede: string;
  collaborations: { name: string; role: string; since: number }[];
  links: Record<string, string>; research_interests: string[]; skills: { area: string; items: string }[]; hobbies: string[];
}
export interface Publication {
  id: string; title: string; authors: string; year: number; venue?: string;
  arxiv?: string; doi?: string; url?: string; project?: string;
  first_author: boolean; selected: boolean; extras?: { label: string; url: string }[];
}
export interface Talk { year: number; kind: string; event: string; place: string }
export interface Education { degree: string; institution: string; place: string; start: number; end: number | string; note?: string }
export interface Grant { name: string; body: string; years: string | number; note?: string }
export interface Experience { role: string; org: string; place: string; start: string | number; end: string | number; bullets?: string[]; links?: { label: string; url: string }[] }
export interface Award { year: number | string; title: string; place?: string }
export interface Fact { icon: string | string[]; text: string }
export interface Photo { src: string; caption?: string; alt?: string }
export interface Project { title: string; figure?: string; figure_alt?: string; link?: string; live?: string; status?: string; description?: string; stage?: string; clip?: string;
  role?: string; year?: number; finding?: string; code?: string; short?: string }
export interface Projects { thesis: Project[]; earlier_text: string; earlier: string[] }
export interface Chapter { name: string; scale: string; at: number; text: string; projects: string[] }
type When = string | number | Date;
export interface Era { at: When; to?: When; title: string; years: string; text: string; kind?: 'collaboration' | 'training' }
export interface TimelinePaper { id?: string; role: string; title: string; venue?: string }
export interface TimelineProject { from: When; to?: When; when: string; w: 1 | 2 | 3; title: string; text?: string; papers?: TimelinePaper[] }
export interface AlongTheWay { at: When; w: 1 | 2 | 3; kind: string; title: string; place?: string }
export interface Timeline { eras: Era[]; projects: TimelineProject[]; along: AlongTheWay[] }

export const profile = load<Profile>(profileRaw);
export const publications = load<Publication[]>(publicationsRaw);
export const talks = load<Talk[]>(talksRaw);
export const education = load<Education[]>(educationRaw);
export const grants = load<Grant[]>(grantsRaw);
export const experience = load<Experience[]>(experienceRaw);
export const awards = load<Award[]>(awardsRaw);
export const facts = load<Fact[]>(factsRaw);
export const photos = (load<Photo[] | null>(photosRaw) ?? []);
export const projects = load<Projects>(projectsRaw);
export const movie = load<{ chapters: Chapter[] }>(movieRaw);
export const timeline = load<Timeline>(timelineRaw);
// A project named in movie.yaml, with its link or status from projects.yaml.
export const projectByTitle = (title: string): Project => projects.thesis.find((p) => p.title === title) ?? { title };

// [label](url) → link. Content comes from our own YAML, so set:html is safe.
export const linkify = (s: string) => s.replace(/\[(.+?)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
// [[text]] → highlighted span. Content comes from our own YAML, so set:html is safe.
export const highlight = (s: string) => s.replace(/\[\[(.+?)\]\]/g, '<strong class="hl">$1</strong>');

// "2016", "2016-05" or "2016-05-08" as a decimal year; a year alone is mid-year, a month alone
// its first day.
export function decimalYear(v: When): number {
  if (v instanceof Date) return v.getUTCFullYear() + (v.getUTCMonth() + (v.getUTCDate() - 1) / 31) / 12;
  const [y, m, d] = String(v).split('-').map(Number);
  if (!m) return y + 0.5;
  return y + (m - 1 + ((d || 1) - 1) / 31) / 12;
}

export function pubLink(p: Publication): { label: string; url: string } | null {
  if (p.arxiv) return { label: `arXiv:${p.arxiv}`, url: `https://arxiv.org/abs/${p.arxiv}` };
  if (p.doi) return { label: 'DOI', url: `https://doi.org/${p.doi}` };
  if (p.url) return { label: 'PDF', url: p.url };
  return null;
}
