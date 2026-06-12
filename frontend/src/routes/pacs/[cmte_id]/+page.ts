import type { EntryGenerator, PageLoad } from './$types';
import { error } from '@sveltejs/kit';

const pacDataModules = import.meta.glob('/src/lib/data/pacs/*.json');

export const load: PageLoad = async ({ params }) => {
	try {
		const data = await import(`$lib/data/pacs/${params.cmte_id}.json`);
		return data.default;
	} catch {
		error(404, 'PAC not found');
	}
};

export const entries: EntryGenerator = () => {
	return Object.keys(pacDataModules).map((path) => ({
		cmte_id: path.split('/').pop()!.replace('.json', '')
	}));
};
