// Loads the YAML content files at build time. Import from here, never from the .yaml directly.
import yaml from 'js-yaml';
import profileRaw from './profile.yaml?raw';
import publicationsRaw from './publications.yaml?raw';
import talksRaw from './talks.yaml?raw';
import educationRaw from './education.yaml?raw';
import grantsRaw from './grants.yaml?raw';
import experienceRaw from './experience.yaml?raw';
import awardsRaw from './awards.yaml?raw';

function load<T>(raw: string): T {
  return yaml.load(raw) as T;
}

export interface Profile {
  name: string; short_name: string; title: string; affiliation: string; location: string;
  email: string; tagline: string; bio: string; advisors: string[];
  collaborations: { name: string; role: string; since: number }[];
  links: Record<string, string>; skills: string[]; hobbies: string[];
}
export interface Publication {
  id: string; title: string; authors: string; year: number; venue: string;
  arxiv?: string; doi?: string; url?: string; project?: string;
  first_author: boolean; selected: boolean; extras?: { label: string; url: string }[];
}
export interface Talk { year: number; kind: string; event: string; place: string }
export interface Education { degree: string; institution: string; place: string; start: number; end: number | string; note?: string }
export interface Grant { name: string; body: string; years: string; note?: string }
export interface Experience { role: string; org: string; place: string; start: string | number; end: string | number; bullets?: string[] }
export interface Award { year: number | string; title: string; place?: string }

export const profile = load<Profile>(profileRaw);
export const publications = load<Publication[]>(publicationsRaw);
export const talks = load<Talk[]>(talksRaw);
export const education = load<Education[]>(educationRaw);
export const grants = load<Grant[]>(grantsRaw);
export const experience = load<Experience[]>(experienceRaw);
export const awards = load<Award[]>(awardsRaw);

export function pubLink(p: Publication): { label: string; url: string } | null {
  if (p.arxiv) return { label: `arXiv:${p.arxiv}`, url: `https://arxiv.org/abs/${p.arxiv}` };
  if (p.doi) return { label: 'DOI', url: `https://doi.org/${p.doi}` };
  if (p.url) return { label: 'PDF', url: p.url };
  return null;
}
