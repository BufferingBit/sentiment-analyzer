<script lang="ts">
	import { onMount, tick } from 'svelte';
	import Chart from 'chart.js/auto';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

    let darkMode = $state(false);
        $effect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    });

	interface SentimentData {
		sentiment: Record<string, number>;
		insight: string;
		common_keywords: string[];
	}

	interface AnalysisResult {
		insights: Record<string, SentimentData>;
	}

	let reviewsText = $state('');
	let result = $state<AnalysisResult | null>(null);
	let error = $state('');
	let isLoading = $state(false);
	let selectedChartType = $state<'pie' | 'bar' | 'doughnut' | 'polarArea'>('pie');
	let selectedAspect = $state<string | undefined>(undefined);

	let canvas = $state<HTMLCanvasElement | null>(null);
	let chartInstance: Chart | null = null;

	// Enhanced color palette
	const chartColors = [
		'#4CAF50',
		'#FF9800',
		'#F44336',
		'#2196F3',
		'#9C27B0',
		'#FFEB3B',
		'#00BCD4',
		'#795548',
		'#8BC34A',
		'#FFC107',
		'#E91E63',
		'#3F51B5'
	];

	async function analyze() {
		error = '';
		result = null;
		isLoading = true;

		const reviews = reviewsText
			.split('\n')
			.map((r) => r.trim())
			.filter((r) => r);

		if (reviews.length === 0) {
			error = 'Please enter at least one review.';
			isLoading = false;
			return;
		}

		try {
			const response = await fetch('http://localhost:5000/analyze', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ reviews })
			});

			if (!response.ok) {
				const err = await response.json();
				error = err.error || 'Something went wrong.';
				return;
			}

			result = await response.json();
             if (result?.insights) {
                Object.values(result.insights).forEach((data: SentimentData) => {
                    data.common_keywords = data.common_keywords.map(keyword => 
                        keyword.replace(/[^a-zA-Z]/g, '') // Remove non-alphabetic characters
                    ).filter(keyword => keyword.length > 0); // Remove empty strings
                });
            }
			selectedAspect = result?.insights ? Object.keys(result.insights)[0] : undefined;
		} catch (err) {
			error = (err as Error).message || 'Request failed.';
		} finally {
			isLoading = false;
		}
	}
	// Standardized sentiment color mapping
	const sentimentColors: Record<string, string> = {
		positive: '#4CAF50', // Green
		neutral: '#FF9800', // Orange
		negative: '#F44336' // Red
		// Add more if your backend returns other sentiment labels
	};

	function renderChart() {
		if (!result || !canvas || !selectedAspect) return;

		const sentimentData = result.insights[selectedAspect].sentiment;
		const labels = Object.keys(sentimentData);
		const data = Object.values(sentimentData);

		if (chartInstance) {
			chartInstance.destroy();
		}
		// Map colors based on sentiment labels
		const backgroundColors = labels.map((label) => {
			// Convert to lowercase to handle case variations
			const lowerLabel = label.toLowerCase();
			return sentimentColors[lowerLabel] || '#2196F3'; // Default blue for unknown sentiments
		});

		chartInstance = new Chart(canvas, {
			type: selectedChartType,
			data: {
				labels,
				datasets: [
					{
						label: 'Sentiment Distribution',
						data,
						backgroundColor: backgroundColors,
						borderColor: '#fff',
						borderWidth: 2
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: selectedChartType === 'bar' ? 'top' : 'right'
					},
					tooltip: {
						callbacks: {
							label: (context) => `${context.label}: ${context.raw}%`
						}
					},
					title: {
						display: true,
						text: `${selectedAspect} Sentiment (${selectedChartType})`,
						font: { size: 16 }
					}
				},
				// Special options for bar charts
				...(selectedChartType === 'bar' && {
					scales: {
						y: {
							beginAtZero: true,
							max: 100,
							ticks: {
								callback: (value) => `${value}%`
							}
						}
					}
				})
			}
		});
	}

	// Solution: Create an explicit dependency object
	let chartDependencies = $derived({
		result,
		selectedAspect,
		selectedChartType,
		canvas
	});

	$effect(() => {
		if (chartDependencies.result) {
			tick().then(renderChart);
		}
	});

	$effect(() => {
		if (result && !selectedAspect) {
			selectedAspect = Object.keys(result.insights)[0] || undefined;
		}
	});
</script>

<div class="app-container">
	<header class="app-header">
		<h1>Sentiment Analysis Dashboard</h1>
		<p class="subtitle">Analyze customer feedback across different aspects</p>
         <button 
        onclick={() => darkMode = !darkMode}
        class="dark-mode-toggle"
        aria-label="Toggle dark mode"
    >
        {#if darkMode}
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
        {:else}
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
        {/if}
    </button>
	</header>

	<main class="main-content">
		<section class="input-section">
			<h2>Enter Reviews <span class="hint">(one per line)</span></h2>
			<textarea
				bind:value={reviewsText}
				rows={8}
				placeholder="Example:&#10;The product quality is excellent but delivery was slow.&#10;Customer service needs improvement..."
				disabled={isLoading}
				class="review-input"
			></textarea>

			<div class="action-bar">
				<button onclick={analyze} disabled={isLoading} class="analyze-btn">
					{isLoading ? 'Analyzing...' : 'Analyze Reviews'}
					{#if isLoading}
						<span class="spinner"></span>
					{/if}
				</button>
			</div>

			{#if error}
				<div class="error-message">
					<svg
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							d="M12 8V12M12 16H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					</svg>
					<span>Error: {error}</span>
				</div>
			{/if}
		</section>

		{#if result}
			<section class="dashboard">
				<div class="controls-panel">
					<!-- <div class="control-group">
                        <label for="chart-type" class="control-label">Chart Type</label>
                        <select id="chart-type" bind:value={selectedChartType} class="styled-select">
                            <option value="pie">Pie Chart</option>
                            <option value="bar">Bar Chart</option>
                            <option value="doughnut">Doughnut Chart</option>
                            <option value="polarArea">Polar Area</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="aspect-select" class="control-label">Aspect</label>
                        <select id="aspect-select" bind:value={selectedAspect} class="styled-select">
                            {#each Object.keys(result.insights) as aspect}
                                <option value={aspect}>{aspect}</option>
                            {/each}
                        </select>
                    </div> -->
					<!-- Chart Type Dropdown -->
					<div class="control-group">
						<label class="control-label" for="chart-type-trigger">Chart Type</label>
						<DropdownMenu.Root>
							<DropdownMenu.Trigger>
								<Button variant="outline" class="w-[150px] justify-start">
									{selectedChartType.charAt(0).toUpperCase() + selectedChartType.slice(1)} Chart
									<svg
										xmlns="http://www.w3.org/2000/svg"
										width="16"
										height="16"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
										class="ml-auto"
									>
										<path d="m6 9 6 6 6-6" />
									</svg>
								</Button>
							</DropdownMenu.Trigger>
							<DropdownMenu.Content class="w-[150px]">
								<DropdownMenu.RadioGroup value={selectedChartType}>
									<DropdownMenu.RadioItem value="pie" onSelect={() => (selectedChartType = 'pie')}>
										Pie Chart
									</DropdownMenu.RadioItem>
									<DropdownMenu.RadioItem value="bar" onSelect={() => (selectedChartType = 'bar')}>
										Bar Chart
									</DropdownMenu.RadioItem>
									<DropdownMenu.RadioItem
										value="doughnut"
										onSelect={() => (selectedChartType = 'doughnut')}
									>
										Doughnut Chart
									</DropdownMenu.RadioItem>
									<DropdownMenu.RadioItem
										value="polarArea"
										onSelect={() => (selectedChartType = 'polarArea')}
									>
										Polar Area
									</DropdownMenu.RadioItem>
								</DropdownMenu.RadioGroup>
							</DropdownMenu.Content>
						</DropdownMenu.Root>
					</div>

					<!-- Aspect Dropdown (only shown when result exists) -->
					{#if result}
						<div class="control-group">
							<label class="control-label" for="aspect-trigger">Aspect</label>
							<DropdownMenu.Root>
								<DropdownMenu.Trigger id="aspect-trigger">
									<Button variant="outline" class="w-[150px] justify-start">
										{selectedAspect || 'Select Aspect'}
										<svg
											xmlns="http://www.w3.org/2000/svg"
											width="16"
											height="16"
											viewBox="0 0 24 24"
											fill="none"
											stroke="currentColor"
											stroke-width="2"
											stroke-linecap="round"
											stroke-linejoin="round"
											class="ml-auto"
										>
											<path d="m6 9 6 6 6-6" />
										</svg>
									</Button>
								</DropdownMenu.Trigger>
								<DropdownMenu.Content class="w-[150px]">
									<DropdownMenu.RadioGroup value={selectedAspect}>
										{#each Object.keys(result.insights) as aspect}
											<DropdownMenu.RadioItem
												value={aspect}
												onSelect={() => (selectedAspect = aspect)}
											>
												{aspect}
											</DropdownMenu.RadioItem>
										{/each}
									</DropdownMenu.RadioGroup>
								</DropdownMenu.Content>
							</DropdownMenu.Root>
						</div>
					{/if}
				</div>

				<div class="visualization-section">
					<div class="chart-container">
						<canvas bind:this={canvas}></canvas>
					</div>

					<div class="insights-panel">
						<h3 class="insights-title">Aspect Insights</h3>
						<div class="aspect-cards">
							{#each Object.entries(result.insights) as [aspect, data]}
								<button
									type="button"
									class="aspect-card {aspect === selectedAspect ? 'selected' : ''}"
									onclick={() => (selectedAspect = aspect)}
								>
									<div class="aspect-header">
										<h4>{aspect}</h4>
										<div class="sentiment-badges">
											{#each Object.entries(data.sentiment) as [label, pct]}
												<span
													class="sentiment-badge"
													style="--badge-color: {sentimentColors[label.toLowerCase()] || '#2196F3'}"
												>
													{label}: {pct}%
												</span>
											{/each}
										</div>
									</div>
									<div class="insight-content">
										<p class="insight-text">{data.insight}</p>
										<div class="keywords-section">
											<span class="keywords-label">Keywords:</span>
											<div class="keywords-container">
												{#each data.common_keywords as keyword}
													<span class="keyword-tag">{keyword}</span>
												{/each}
											</div>
										</div>
									</div>
								</button>
							{/each}
						</div>
					</div>
				</div>
			</section>
		{/if}
	</main>
</div>

<style>
    /* ===== CSS Variables ===== */
    :root {
        /* Light mode colors */
        --bg-color: #f8fafc;
        --text-color: #1e293b;
        --card-bg: white;
        --border-color: #e2e8f0;
        --input-bg: white;
        --button-bg: #3b82f6;
        --button-hover: #2563eb;
        --error-bg: #fee2e2;
        --error-text: #dc2626;
        --keyword-bg: #e2e8f0;
        --keyword-text: #334155;
        --selected-card-bg: #f0f7ff;
        --title-color: #1e40af;
        --subtitle-color: #64748b;
        --shadow-color: rgba(0, 0, 0, 0.1);
    }

    /* Dark mode colors */
    :global(.dark) {
        --bg-color: #0f172a;
        --text-color: #f8fafc;
        --card-bg: #1e293b;
        --border-color: #334155;
        --input-bg: #1e293b;
        --button-bg: #3b82f6;
        --button-hover: #2563eb;
        --error-bg: #7f1d1d;
        --error-text: white;
        --keyword-bg: #334155;
        --keyword-text: #e2e8f0;
        --selected-card-bg: #1e3a8a;
        --title-color: #93c5fd;
        --subtitle-color: #94a3b8;
        --shadow-color: rgba(0, 0, 0, 0.3);
    }

    /* ===== Base Styles ===== */
    :global(body) {
        margin: 0;
        padding: 0;
        font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        transition: background-color 0.3s ease;
    }

    /* ===== Layout Styles ===== */
    .app-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    .app-header {
        text-align: center;
        margin-bottom: 30px;
        position: relative;
    }

    .app-header h1 {
        font-size: 2.2rem;
        color: var(--title-color);
        margin-bottom: 8px;
        transition: color 0.3s ease;
    }

    .subtitle {
        font-size: 1rem;
        color: var(--subtitle-color);
        margin-top: 0;
        transition: color 0.3s ease;
    }

    /* ===== Input Section ===== */
    .input-section {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 6px -1px var(--shadow-color);
        margin-bottom: 30px;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
    }

    .input-section h2 {
        font-size: 1.3rem;
        margin-bottom: 15px;
        color: var(--text-color);
    }

    .hint {
        font-size: 0.9rem;
        color: var(--subtitle-color);
        font-weight: normal;
    }

    .review-input {
        width: 100%;
        padding: 15px;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        font-size: 1rem;
        line-height: 1.5;
        resize: vertical;
        transition: all 0.3s ease;
        background-color: var(--input-bg);
        color: var(--text-color);
    }

    .review-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* ===== Button Styles ===== */
    .action-bar {
        display: flex;
        justify-content: flex-end;
        margin-top: 15px;
    }

    .analyze-btn {
        background-color: var(--button-bg);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.3s ease;
    }

    .analyze-btn:hover {
        background-color: var(--button-hover);
    }

    .analyze-btn:active {
        transform: scale(0.98);
    }

    .analyze-btn:disabled {
        background-color: #94a3b8;
        cursor: not-allowed;
    }

    .spinner {
        width: 18px;
        height: 18px;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s ease-in-out infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    /* ===== Error Message ===== */
    .error-message {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--error-text);
        background-color: var(--error-bg);
        padding: 12px 15px;
        border-radius: 8px;
        margin-top: 15px;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }

    /* ===== Dashboard Styles ===== */
    .dashboard {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 6px -1px var(--shadow-color);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
    }

    .controls-panel {
        display: flex;
        gap: 20px;
        margin-bottom: 25px;
        flex-wrap: wrap;
    }

    .control-group {
        flex: 1;
        min-width: 200px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .control-label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: var(--text-color);
    }

    /* ===== Visualization Section ===== */
    .visualization-section {
        display: grid;
        grid-template-columns: 1.5fr 1fr;
        gap: 25px;
    }

    .chart-container {
        background: var(--card-bg);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px var(--shadow-color);
        height: 400px;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
    }

    /* ===== Insights Panel ===== */
    .insights-panel {
        display: flex;
        flex-direction: column;
    }

    .insights-title {
        font-size: 1.2rem;
        margin-bottom: 15px;
        color: var(--text-color);
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-color);
    }

    .aspect-cards {
        display: flex;
        flex-direction: column;
        gap: 15px;
        max-height: 600px;
        overflow-y: auto;
        padding-right: 10px;
    }

    .aspect-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 18px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 1px 2px var(--shadow-color);
    }

    .aspect-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px var(--shadow-color);
        border-color: #bfdbfe;
    }

    .aspect-card.selected {
        border: 2px solid #3b82f6;
        background-color: var(--selected-card-bg);
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
    }

    .aspect-header {
        margin-bottom: 12px;
    }

    .aspect-header h4 {
        font-size: 1.1rem;
        color: var(--title-color);
        margin: 0 0 8px 0;
    }

    .sentiment-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .sentiment-badge {
        font-size: 0.75rem;
        padding: 4px 8px;
        border-radius: 999px;
        background-color: var(--badge-color);
        color: white;
        font-weight: 500;
    }

    .insight-content {
        font-size: 0.95rem;
        color: var(--text-color);
    }

    .insight-text {
        margin: 0 0 12px 0;
        line-height: 1.5;
    }

    .keywords-section {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .keywords-label {
        font-size: 0.85rem;
        color: var(--subtitle-color);
        font-weight: 500;
    }

    .keywords-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .keyword-tag {
        font-size: 0.8rem;
        padding: 3px 8px;
        background-color: var(--keyword-bg);
        border-radius: 999px;
        color: var(--keyword-text);
        transition: all 0.3s ease;
    }

    /* ===== Dark Mode Toggle ===== */
    .dark-mode-toggle {
        position: absolute;
        top: 20px;
        right: 20px;
        background: transparent;
        border: none;
        cursor: pointer;
        color: currentColor;
        padding: 8px;
        border-radius: 50%;
        transition: all 0.3s ease;
    }

    .dark-mode-toggle:hover {
        background: rgba(255, 255, 255, 0.1);
    }

    :global(.dark) .dark-mode-toggle:hover {
        background: rgba(0, 0, 0, 0.1);
    }

    .dark-mode-toggle svg {
        width: 24px;
        height: 24px;
    }

    /* ===== Responsive Styles ===== */
    @media (max-width: 768px) {
        .visualization-section {
            grid-template-columns: 1fr;
        }

        .controls-panel {
            flex-direction: column;
            gap: 15px;
        }

        .control-group {
            min-width: 100%;
        }

        .chart-container {
            height: 300px;
        }

        .aspect-cards {
            max-height: none;
        }
    }
</style>
