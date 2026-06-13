<div class="page">
	<h1>Who Funds Who</h1>
	<p>
		A project to make campaign finance data more accessible and understandable. Data is sourced from
		the Federal Election Commission (FEC). Explore politicians and PACs to see who funds who in U.S.
		elections.
	</p>

	<h2>Limitations</h2>
	<ul>
		<li>This only works for national elections and does not cover state and local elections.</li>
		<li>For now, this is only a personal project and only has 2025–2026 data.</li>
	</ul>

	<h2>Architecture</h2>
	<p>
		Originally, I was going to deploy this using dynamic data, where we download several datasets
		from the FEC.gov website, process and store them using SQLite, and serve them dynamically.
	</p>
	<p>
		However, in order to keep the data static and deploy on GitHub Pages, I changed the approach to
		pre-processing the data and embedding it in the frontend as JSON files.
	</p>
</div>

<style>
	.page {
		max-width: 720px;
	}

	h1 {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 1rem;
		color: #f9fafb;
	}

	h2 {
		font-size: 1.25rem;
		font-weight: 700;
		color: #f9fafb;
		margin-top: 1.5rem;
		margin-bottom: 0.75rem;
	}

	p {
		color: #9ca3af;
		line-height: 1.75;
		margin-bottom: 1rem;
	}

	ul {
		color: #9ca3af;
		line-height: 1.75;
		margin-bottom: 1rem;
		padding-left: 1.5rem;
	}

	li {
		margin-bottom: 0.5rem;
	}
</style>
