import type { PageLoad } from './$types';
import searchIndex from '$lib/data/search-index.json';

export const prerender = false;
export const ssr = false;

export const load: PageLoad = () => {
	return searchIndex;
};
