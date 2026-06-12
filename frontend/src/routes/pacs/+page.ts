import type { PageLoad } from './$types';
import pacs from '$lib/data/pacs.json';

export const load: PageLoad = () => {
	return { pacs };
};
