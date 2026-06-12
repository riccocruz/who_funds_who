<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import {
		createGrid,
		ModuleRegistry,
		AllCommunityModule,
		type ColDef,
		type GridOptions
	} from 'ag-grid-community';
	import { myTheme } from '$lib/theme';

	ModuleRegistry.registerModules([AllCommunityModule]);

	type Recipient = {
		cand_id: string;
		cand_name: string;
		party: string;
		state: string;
		total_amt: number;
		direct_amt: number;
		ie_amt: number;
		bundled_amt: number;
	};

	type PacTransfer = {
		cmte_id: string;
		pac_name: string;
		total_amt: number;
		tx_count: number;
	};

	type ServerData = {
		pac: {
			name: string;
			committee_type: string;
			total_receipts: number;
			indiv_contrib: number;
			total_spent: number;
			cash_on_hand: number;
		};
		cmte_id: string;
		stats: { candidates_funded: number };
		recipients: Recipient[];
		pacTransfers: PacTransfer[];
	};

	let { data }: { data: ServerData } = $props();

	const fmt = (v: number | null) => (v != null ? '$' + v.toLocaleString('en-US') : '—');

	const colDefs: ColDef<Recipient>[] = [
		{
			field: 'cand_name',
			headerName: 'Candidate',
			flex: 4
		},
		{ field: 'party', headerName: 'Party', flex: 1 },
		{ field: 'state', headerName: 'State', flex: 1 },
		{
			field: 'total_amt',
			headerName: 'Total',
			flex: 2,
			type: 'numericColumn',
			sort: 'desc',
			valueFormatter: (p) => fmt(p.value),
			cellStyle: { fontWeight: '600' }
		},
		{
			field: 'direct_amt',
			headerName: 'Direct Contribution (24K)',
			flex: 2,
			type: 'numericColumn',
			valueFormatter: (p) => fmt(p.value)
		},
		{
			field: 'ie_amt',
			headerName: 'Indep. Expenditure (24E)',
			flex: 2,
			type: 'numericColumn',
			valueFormatter: (p) => fmt(p.value)
		},
		{
			field: 'bundled_amt',
			headerName: 'Bundled Donations',
			flex: 2,
			type: 'numericColumn',
			valueFormatter: (p) => fmt(p.value)
		},
		{
			headerName: 'FEC',
			width: 80,
			sortable: false,
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			cellRenderer: (p: any) => {
				if (!p.data?.cand_id) return '';
				const a = document.createElement('a');
				a.href = `https://www.fec.gov/data/candidate/${p.data.cand_id}/`;
				a.target = '_blank';
				a.rel = 'noopener noreferrer';
				a.textContent = 'FEC ↗';
				a.className = 'pac-link';
				a.addEventListener('click', (e) => e.stopPropagation());
				return a;
			}
		}
	];

	let gridEl: HTMLDivElement;
	let pacGridEl: HTMLDivElement;

	onMount(() => {
		const api = createGrid<Recipient>(gridEl, {
			theme: myTheme,
			columnDefs: colDefs,
			rowData: data.recipients,
			defaultColDef: { sortable: true, resizable: true },
			domLayout: 'autoHeight',
			pagination: true,
			paginationPageSize: 20,
			paginationPageSizeSelector: [20, 50, 100],
			rowStyle: { cursor: 'pointer' },
			onRowClicked: (e) =>
				e.data?.cand_id && goto(resolve(`/politicians/${encodeURIComponent(e.data.cand_id)}`))
		} satisfies GridOptions<Recipient>);

		const pacApi = createGrid<PacTransfer>(pacGridEl, {
			theme: myTheme,
			columnDefs: [
				{
					field: 'pac_name',
					headerName: 'PAC / Committee',
					flex: 4,
					filter: 'agTextColumnFilter'
				},
				{
					field: 'total_amt',
					headerName: 'Amount',
					flex: 2,
					type: 'numericColumn',
					sort: 'desc',
					valueFormatter: (p) => fmt(p.value),
					cellStyle: { fontWeight: '600' }
				},
				{
					field: 'tx_count',
					headerName: 'Transactions',
					flex: 1,
					type: 'numericColumn'
				},
				{
					headerName: 'FEC',
					width: 80,
					sortable: false,
					// eslint-disable-next-line @typescript-eslint/no-explicit-any
					cellRenderer: (p: any) => {
						if (!p.data?.cmte_id) return '';
						const a = document.createElement('a');
						a.href = `https://www.fec.gov/data/committee/${p.data.cmte_id}/`;
						a.target = '_blank';
						a.rel = 'noopener noreferrer';
						a.textContent = 'FEC ↗';
						a.className = 'pac-link';
						a.addEventListener('click', (e) => e.stopPropagation());
						return a;
					}
				}
			] as ColDef<PacTransfer>[],
			rowData: data.pacTransfers,
			defaultColDef: { sortable: true, resizable: true },
			domLayout: 'autoHeight',
			pagination: true,
			paginationPageSize: 20,
			paginationPageSizeSelector: [20, 50, 100],
			rowStyle: { cursor: 'pointer' },
			onRowClicked: (e) => e.data?.cmte_id && goto(resolve(`/pacs/${encodeURIComponent(e.data.cmte_id)}`))
		} satisfies GridOptions<PacTransfer>);

		return () => {
			api.destroy();
			pacApi.destroy();
		};
	});
</script>

<div class="page">
	<a href={resolve('/pacs')} class="back-link">← All PACs</a>

	<section class="header-section">
		<h1>{data.pac.name}</h1>
		<div class="meta">
			<span class="tag">{data.pac.committee_type}</span>
		</div>
	</section>

	<section class="stats-section">
		<div class="stat-card">
			<div class="stat-label">Candidates Funded</div>
			<div class="stat-value">{(data.stats.candidates_funded ?? 0).toLocaleString('en-US')}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">Total Receipts</div>
			<div class="stat-value">{fmt(data.pac.total_receipts)}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">From Individuals</div>
			<div class="stat-value">{fmt(data.pac.indiv_contrib)}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">Total Spent</div>
			<div class="stat-value">{fmt(data.pac.total_spent)}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">Cash on Hand</div>
			<div class="stat-value">{fmt(data.pac.cash_on_hand)}</div>
		</div>
	</section>

	<section class="table-section">
		<h2>Recipients</h2>
		<p class="subtitle">
			Candidates this PAC contributed to or spent on behalf of. Click a row to view the candidate.
		</p>
		<div bind:this={gridEl} class="recipients-grid grid"></div>
	</section>

	{#if data.pacTransfers.length > 0}
		<section class="table-section" style="margin-top: 1.5rem">
			<h2>PAC-to-PAC Transfers</h2>
			<p class="subtitle">
				Other committees this PAC sent money to. Click a name to view the committee on FEC.gov.
			</p>
			<div bind:this={pacGridEl} class="grid"></div>
		</section>
	{/if}
</div>

<style>
	.page {
		min-width: 700px;
	}

	h1 {
		margin: 0 0 0.5rem;
		font-size: 1.75rem;
		font-weight: 700;
		color: #f9fafb;
	}

	h2 {
		margin: 0 0 0.25rem;
		font-size: 1.25rem;
		font-weight: 700;
		color: #f9fafb;
	}

	.recipients-grid {
		height: 550px;
	}
</style>
