import type { PageLoad } from './$types';
import searchIndex from '$lib/data/search-index.json';

export const prerender = false;

export const load: PageLoad = ({ url }) => {
	return {
		...searchIndex,
		q: url.searchParams.get('q') ?? ''
	};
};
