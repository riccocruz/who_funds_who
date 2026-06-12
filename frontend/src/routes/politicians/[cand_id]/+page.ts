import type { EntryGenerator, PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import politiciansList from '$lib/data/politicians.json';

export const load: PageLoad = async ({ params }) => {
	try {
		const data = await import(`$lib/data/politicians/${params.cand_id}.json`);
		return data.default;
	} catch {
		error(404, 'Politician not found');
	}
};

export const entries: EntryGenerator = () => {
	return (politiciansList as { cand_id: string }[]).map((p) => ({ cand_id: p.cand_id }));
};
