import type { PageLoad } from './$types';
import searchIndex from '$lib/data/search-index.json';

export const load: PageLoad = () => {
	return searchIndex;
};
