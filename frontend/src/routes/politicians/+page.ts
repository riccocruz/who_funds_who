import type { PageLoad } from './$types';
import politicians from '$lib/data/politicians.json';

export const load: PageLoad = () => {
	return { politicians };
};
