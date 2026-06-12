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

	type PacRow = {
		cmte_id: string;
		name: string;
		committee_type: string;
		total_receipts: number;
		indiv_contrib: number;
		total_spent: number;
		cash_on_hand: number;
	};

	type ServerData = { pacs: PacRow[] };
	let { data }: { data: ServerData } = $props();

	const fmt = (v: number | null) => (v != null ? '$' + v.toLocaleString('en-US') : '—');

	const colDefs: ColDef<PacRow>[] = [
		{ field: 'name', headerName: 'Name', flex: 3, filter: 'agTextColumnFilter' },
		{
			field: 'total_receipts',
			headerName: 'Total',
			flex: 2,
			type: 'numericColumn',
			sort: 'desc',
			valueFormatter: (p) => fmt(p.value),
			cellStyle: { fontWeight: '600' }
		},
		{
			field: 'indiv_contrib',
			headerName: 'Individuals',
			flex: 2,
			type: 'numericColumn',
			valueFormatter: (p) => fmt(p.value)
		},
		{
			field: 'total_spent',
			headerName: 'Total Spent',
			flex: 2,
			type: 'numericColumn',
			valueFormatter: (p) => fmt(p.value)
		},
		{
			field: 'cash_on_hand',
			headerName: 'Cash on Hand',
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

	let gridEl: HTMLDivElement;

	onMount(() => {
		const api = createGrid<PacRow>(gridEl, {
			theme: myTheme,
			columnDefs: colDefs,
			rowData: data.pacs,
			defaultColDef: { sortable: true, resizable: true },
			pagination: true,
			paginationPageSize: 20,
			paginationPageSizeSelector: [20, 50, 100],
			rowStyle: { cursor: 'pointer' },
			onRowClicked: (e) => e.data?.cmte_id && goto(resolve(`/pacs/${encodeURIComponent(e.data.cmte_id)}`))
		} satisfies GridOptions<PacRow>);

		return () => api.destroy();
	});
</script>

<div class="page">
	<section class="table-section">
		<h2>PACs</h2>
		<p class="subtitle">
			All committees sorted by total receipts — click a column header to re-sort
		</p>
		<div bind:this={gridEl} class="grid"></div>
	</section>
</div>

<style>
	.page {
		min-width: 1300px;
	}

	h2 {
		margin: 0 0 0.25rem;
		font-size: 1.25rem;
		font-weight: 700;
		color: #f9fafb;
	}

	.grid {
		height: calc(100vh - 250px);
		min-height: 400px;
	}
</style>
