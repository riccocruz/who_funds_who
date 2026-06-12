<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import {
		Navbar,
		NavBrand,
		NavLi,
		NavUl,
		NavHamburger,
		Search,
		ToolbarButton
	} from 'flowbite-svelte';
	import { SearchOutline } from 'flowbite-svelte-icons';
	import { fade } from 'svelte/transition';

	import { goto } from '$app/navigation';

	let { children } = $props();

	let searchQuery = $state('');

	function handleSearch(e: KeyboardEvent) {
		if (e.key === 'Enter' && searchQuery.trim()) {
			goto(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
		}
	}
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<Navbar>
	{#snippet children({ hidden, toggle })}
		<NavBrand href="/">
			<span class="brand-name">Who Funds Who</span>
		</NavBrand>
		<div class="flex md:order-2">
			<ToolbarButton class="block md:hidden" onclick={toggle}>
				<SearchOutline class="h-5 w-5 text-gray-500 dark:text-gray-400" />
			</ToolbarButton>
			<div class="hidden md:block">
				<Search
					size="md"
					class="ms-auto"
					placeholder="Search..."
					bind:value={searchQuery}
					onkeydown={handleSearch}
				/>
			</div>
			<NavHamburger onclick={toggle} />
		</div>
		{#if !hidden}
			<div class="mt-2 w-full md:hidden" transition:fade>
				<Search
					size="md"
					placeholder="Search..."
					bind:value={searchQuery}
					onkeydown={handleSearch}
				/>
			</div>
		{/if}
		<NavUl>
			<NavLi href="/">Home</NavLi>
			<NavLi href="/politicians">Politicians</NavLi>
			<NavLi href="/pacs">PACs</NavLi>
		</NavUl>
	{/snippet}
</Navbar>

<main>
	{@render children()}
</main>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	:global(nav.navbar) {
		background-color: #1c1c20 !important;
		border-bottom: 1px solid #2d3d52;
	}

	.brand-name {
		font-size: 1.2rem;
		font-weight: 700;
		letter-spacing: -0.01em;
		white-space: nowrap;
	}

	main {
		flex: 1;
	}
</style>
