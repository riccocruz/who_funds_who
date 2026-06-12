import type { EntryGenerator, PageLoad } from './$types';
import { error } from '@sveltejs/kit';

const politicianDataModules = import.meta.glob('/src/lib/data/politicians/*.json');

export const load: PageLoad = async ({ params }) => {
	try {
		const data = await import(`$lib/data/politicians/${params.cand_id}.json`);
		return data.default;
	} catch {
		error(404, 'Politician not found');
	}
};

export const entries: EntryGenerator = () => {
	return Object.keys(politicianDataModules).map((path) => ({
		cand_id: path.split('/').pop()!.replace('.json', '')
	}));
};
