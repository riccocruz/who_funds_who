<div class="page">
	<h1>Who Funds Who</h1>
	<p></p>
	<p>
		A project to make campaign finance data more accessible and understandable. Data is sourced from
		the Federal Election Commission (FEC) and updated daily. Explore politicians and PACs to see who
		funds who in U.S. elections.
	</p>
	<p>This only works in national elections, and does not cover state and local elections.</p>
	<p>For now, this is only a personal project and only has 2025-2026 data.</p>
	<p>
		Originally, I was going to deploy this using dynamic data, where we: download several datasets
		in the FEC.gov website, process and store them using SQLite, and serve them dynamically.
		However, in order to keep the data static and deploy on Github pages, I changed the approach to
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

	p {
		color: #9ca3af;
		line-height: 1.75;
		margin-bottom: 1rem;
	}
</style>
