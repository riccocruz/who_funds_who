<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import {
		createGrid,
		ModuleRegistry,
		AllCommunityModule,
		type ColDef,
		type GridOptions
	} from 'ag-grid-community';
	import { myTheme } from '$lib/theme';

	ModuleRegistry.registerModules([AllCommunityModule]);

	type PacDonation = {
		cmte_id: string;
		pac_name: string;
		total_amt: number;
		direct_amt: number;
		ie_amt: number;
	};

	type OppositionPac = {
		cmte_id: string;
		pac_name: string;
		total_amt: number;
	};

	type ServerData = {
		politician: {
			cand_name: string;
			party: string;
			state: string;
			indiv_total: number;
			pac_receipts_summary: number;
		};
		donations: PacDonation[];
		indivStats: { unique_donors: number; oos_donors: number; oos_total: number };
		opposition: OppositionPac[];
	};

	let { data }: { data: ServerData } = $props();

	const pac_tx_total = $derived(data.donations.reduce((sum, d) => sum + (d.total_amt ?? 0), 0));

	const fmt = (v: number | null) => (v != null ? '$' + v.toLocaleString('en-US') : '—');

	const PARTY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
		DEM: { bg: '#172554', text: '#93c5fd', border: '#3b82f6' },
		REP: { bg: '#450a0a', text: '#fca5a5', border: '#ef4444' },
		IND: { bg: '#1a2e1a', text: '#86efac', border: '#22c55e' },
		LIB: { bg: '#2d2100', text: '#fde68a', border: '#f59e0b' },
		GRE: { bg: '#052e16', text: '#6ee7b7', border: '#10b981' }
	};
	const partyColor = $derived(
		PARTY_COLORS[data.politician.party] ?? { bg: '#1f2937', text: '#d1d5db', border: '#6b7280' }
	);

	const colDefs: ColDef<PacDonation>[] = [
		{
			field: 'pac_name',
			headerName: 'Name',
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
	];

	const oppColDefs: ColDef<OppositionPac>[] = [
		{
			field: 'pac_name',
			headerName: 'Name',
			flex: 4,
			filter: 'agTextColumnFilter'
		},
		{
			field: 'total_amt',
			headerName: 'Amount Spent',
			flex: 2,
			type: 'numericColumn',
			sort: 'desc',
			valueFormatter: (p) => fmt(p.value),
			cellStyle: { fontWeight: '600', color: '#dc2626' }
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
	];

	let gridEl: HTMLDivElement;
	let oppGridEl: HTMLDivElement;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let gridApi: any = null;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let oppGridApi: any = null;

	onMount(() => {
		gridApi = createGrid<PacDonation>(gridEl, {
			theme: myTheme,
			columnDefs: colDefs,
			rowData: data.donations,
			defaultColDef: { sortable: true, resizable: true },
			domLayout: 'autoHeight',
			pagination: true,
			paginationPageSize: 20,
			paginationPageSizeSelector: [20, 50, 100],
			rowStyle: { cursor: 'pointer' },
			onRowClicked: (e) => e.data?.cmte_id && goto(`${base}/pacs/${encodeURIComponent(e.data.cmte_id)}`)
		} satisfies GridOptions<PacDonation>);

		oppGridApi = createGrid<OppositionPac>(oppGridEl, {
			theme: myTheme,
			columnDefs: oppColDefs,
			rowData: data.opposition,
			defaultColDef: { sortable: true, resizable: true },
			domLayout: 'autoHeight',
			pagination: true,
			paginationPageSize: 20,
			paginationPageSizeSelector: [20, 50, 100],
			rowStyle: { cursor: 'pointer' },
			onRowClicked: (e) => e.data?.cmte_id && goto(`${base}/pacs/${encodeURIComponent(e.data.cmte_id)}`)
		} satisfies GridOptions<OppositionPac>);

		return () => {
			gridApi?.destroy();
			oppGridApi?.destroy();
		};
	});
</script>

<div class="page">
	<a href={`${base}/politicians`} class="back-link">← All Politicians</a>

	<section class="header-section">
		<div class="meta">
			<h1>{data.politician.cand_name}</h1>
			<span
				class="tag party-tag"
				style="background:{partyColor.bg}; color:{partyColor.text}; border-color:{partyColor.border};"
				>{data.politician.party}</span
			>
			<span class="tag">{data.politician.state}</span>
		</div>
	</section>

	<section class="stats-section">
		<div class="stat-card">
			<div class="stat-label">Unique Individual Donors</div>
			<div class="stat-value">{(data.indivStats.unique_donors ?? 0).toLocaleString('en-US')}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">Total from Individuals</div>
			<div class="stat-value">{fmt(data.politician.indiv_total)}</div>
		</div>

		<br />
		<div class="stat-card">
			<div class="stat-label">PAC Receipts</div>
			<div class="stat-value">{fmt(data.politician.pac_receipts_summary)}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">PAC Transactions</div>
			<div class="stat-value">{fmt(pac_tx_total)}</div>
		</div>

		<br />
		<div class="stat-card">
			<div class="stat-label">Out-of-State Donors</div>
			<div class="stat-value">{(data.indivStats.oos_donors ?? 0).toLocaleString('en-US')}</div>
		</div>
		<div class="stat-card">
			<div class="stat-label">Out-of-State Total</div>
			<div class="stat-value">{fmt(data.indivStats.oos_total)}</div>
		</div>
	</section>
	<p class="stats-note">
		PAC summary and transaction totals may differ. Some filings are earmarked for a future election
		cycle, and others represent spending on a candidate's behalf rather than direct contributions.
	</p>

	<section class="table-section">
		<h2>PAC Donors</h2>
		<p class="subtitle">
			PACs that donated to this candidate, sorted by total amount. Click a name to view the
			committee on FEC.gov.
		</p>
		<div bind:this={gridEl} class="grid"></div>
	</section>

	{#if data.opposition.length > 0}
		<section class="table-section opposition-section">
			<h2>PACs Opposing This Candidate</h2>
			<p class="subtitle">
				PACs that filed independent expenditures (24A) against this candidate. Click a name to view
				the committee on FEC.gov.
			</p>
			<div bind:this={oppGridEl} class="grid" style="width: 50%"></div>
		</section>
	{/if}
</div>

<style>
	.page {
		min-width: 700px;
	}

	.header-section {
		margin-bottom: 1.75rem;
	}

	.meta {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.party-tag {
		border: 1px solid transparent;
		font-weight: 600;
		letter-spacing: 0.04em;
	}

	h1 {
		margin: 0;
		font-size: 1.75rem;
		font-weight: 700;
		color: #f9fafb;
		text-transform: capitalize;
	}

	h2 {
		margin: 0 0 0.25rem;
		font-size: 1.25rem;
		font-weight: 700;
		color: #f9fafb;
	}

	.opposition-section {
		border-left: 3px solid #ef4444;
	}

	.stats-note {
		margin: -0.5rem 0 1rem;
		font-size: 0.8rem;
		color: #6b7280;
	}
</style>
