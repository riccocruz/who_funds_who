<script lang="ts">
	import { page } from '$app/state';
	import { resolve } from '$app/paths';

	const q = $derived(page.url.searchParams.get('q') ?? '');

	type Politician = {
		cand_id: string;
		cand_name: string;
		party: string;
		state: string;
		office_code: string;
	};
	type Pac = { cmte_id: string; name: string; committee_type: string };
	type ServerData = { politicians: Politician[]; pacs: Pac[] };

	let { data }: { data: ServerData } = $props();

	const OFFICE_LABEL: Record<string, string> = { H: 'House', S: 'Senate', P: 'President' };
	const CMTE_TYPE_LABEL: Record<string, string> = {
		N: 'PAC',
		Q: 'PAC',
		O: 'Super PAC',
		D: 'Leadership PAC',
		I: 'Independent Expenditure',
		W: 'Super PAC',
		E: 'Electioneering'
	};
	const PARTY_COLOR: Record<string, string> = { D: '#2563eb', R: '#dc2626', I: '#6b7280' };

	const filteredPoliticians = $derived(
		q
			? data.politicians
					.filter((p) => p.cand_name.toLowerCase().includes(q.toLowerCase()))
					.slice(0, 20)
			: []
	);

	const filteredPacs = $derived(
		q
			? data.pacs.filter((p) => p.name.toLowerCase().includes(q.toLowerCase())).slice(0, 20)
			: []
	);
</script>

<div class="page">
	{#if !q}
		<p class="query-label">Please enter a search query.</p>
	{:else if filteredPoliticians.length === 0 && filteredPacs.length === 0}
		<p class="query-label">No results found for <strong>"{q}"</strong>.</p>
	{/if}

	{#if filteredPoliticians.length > 0 || filteredPacs.length > 0}
		<p class="query-label">
			Search results for <strong>"{q}"</strong>:
		</p>
	{/if}

	<section class="result-section">
		<h2>Politicians</h2>
		{#if filteredPoliticians.length === 0}
			<p class="empty">No politicians found.</p>
		{:else}
			<ul class="result-list">
				{#each filteredPoliticians as c}
					<li>
						<a href={resolve(`/politicians/${encodeURIComponent(c.cand_id)}`)} class="result-item">
							<span class="result-name">{c.cand_name}</span>
							<span class="result-meta">
								<span class="party" style="color: {PARTY_COLOR[c.party] ?? '#6b7280'}"
									>{c.party}</span
								>
								&middot; {c.state} &middot; {OFFICE_LABEL[c.office_code] ?? c.office_code}
							</span>
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</section>

	<section class="result-section">
		<h2>PACs</h2>
		{#if filteredPacs.length === 0}
			<p class="empty">No PACs found.</p>
		{:else}
			<ul class="result-list">
				{#each filteredPacs as p}
					<li>
						<a href={resolve(`/pacs/${encodeURIComponent(p.cmte_id)}`)} class="result-item">
							<span class="result-name">{p.name}</span>
							<span class="result-meta"
								>{CMTE_TYPE_LABEL[p.committee_type] ?? p.committee_type}</span
							>
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</section>
</div>

<style>
	.page {
		max-width: 720px;
	}

	h2 {
		font-size: 1rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #6b7280;
		margin: 0 0 0.75rem;
	}
</style>
