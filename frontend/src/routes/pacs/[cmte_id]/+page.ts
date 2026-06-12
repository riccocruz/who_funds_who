import type { EntryGenerator, PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import pacsList from '$lib/data/pacs.json';

export const load: PageLoad = async ({ params }) => {
	try {
		const data = await import(`$lib/data/pacs/${params.cmte_id}.json`);
		return data.default;
	} catch {
		error(404, 'PAC not found');
	}
};

export const entries: EntryGenerator = () => {
	return (pacsList as { cmte_id: string }[]).map((p) => ({ cmte_id: p.cmte_id }));
};
