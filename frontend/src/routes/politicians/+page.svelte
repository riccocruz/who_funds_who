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

	type PoliticianRow = {
		cand_id: string;
		cand_name: string;
		party: string;
		state: string;
		incumbent_status: string;
		office: string;
		total_raised: number;
		pac_total: number;
		indiv_total: number;
	};

	type ServerData = { politicians: PoliticianRow[] };

	let { data }: { data: ServerData } = $props();

	const OFFICE_LABEL: Record<string, string> = { H: 'House', S: 'Senate', P: 'President' };
	const ICI_LABEL: Record<string, string> = { I: 'Incumbent', C: 'Challenger', O: 'Open Seat' };

	const rows: PoliticianRow[] = $derived(
		data.politicians.map((p: PoliticianRow) => ({
			...p,
			office: OFFICE_LABEL[p.cand_id?.[0]] ?? p.cand_id?.[0] ?? '—',
			incumbent_status: ICI_LABEL[p.incumbent_status] ?? p.incumbent_status ?? '—'
		}))
	);

	const fmt = (v: number | null) => (v != null ? '$' + v.toLocaleString('en-US') : '—');

	const colDefs: ColDef<PoliticianRow>[] = [
		{ field: 'cand_name', headerName: 'Name', flex: 3, filter: 'agTextColumnFilter' },
		{ field: 'party', headerName: 'Party', flex: 1, filter: 'agTextColumnFilter' },
		{ field: 'office', headerName: 'Office', flex: 1, filter: 'agTextColumnFilter' },
		{ field: 'state', headerName: 'State', flex: 1, filter: 'agTextColumnFilter' },
		{ field: 'incumbent_status', headerName: 'Status', flex: 1, filter: 'agTextColumnFilter' },
		{
			field: 'total_raised',
			headerName: 'Total Raised',
			flex: 2,
			type: 'numericColumn',
			sort: 'desc',
			valueFormatter: (p) => fmt(p.value),
			cellStyle: { fontWeight: '600' }
		},
		{
			field: 'pac_total',
			headerName: 'From PACs',
			flex: 2,
			type: 'numericColumn',
			valueFormatter: (p) => fmt(p.value)
		},
		{
			field: 'indiv_total',
			headerName: 'From Individuals',
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
				a.className = 'fec-link';
				a.addEventListener('click', (e) => e.stopPropagation());
				return a;
			}
		}
	];

	let gridEl: HTMLDivElement;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let gridApi: any = null;

	onMount(() => {
		gridApi = createGrid<PoliticianRow>(gridEl, {
			theme: myTheme,
			columnDefs: colDefs,
			rowData: rows,
			defaultColDef: { sortable: true, resizable: true },
			rowStyle: { cursor: 'pointer' },
			onRowClicked: (e) => e.data && goto(resolve(`/politicians/${encodeURIComponent(e.data.cand_id)}`)),
			pagination: true,
			paginationPageSize: 20,
			paginationPageSizeSelector: [20, 50, 100]
		} satisfies GridOptions<PoliticianRow>);

		return () => gridApi?.destroy();
	});
</script>

<div class="page">
	<section class="table-section">
		<h2>Politicians</h2>
		<p class="subtitle">
			All candidates sorted by total raised — click a row to view PAC donors, click a column header
			to re-sort
		</p>
		<div bind:this={gridEl} class="grid"></div>
	</section>
</div>

<style>
	.page {
		min-width: 700px;
	}

	h2 {
		margin: 0 0 0.25rem;
		font-size: 1.25rem;
		font-weight: 700;
		color: #f9fafb;
	}

	.grid {
		height: calc(100vh - 220px);
		min-height: 400px;
	}
</style>
