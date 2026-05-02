document.addEventListener('DOMContentLoaded', function() {

    const canvasElement = document.getElementById('adminInventoryChart');
    if (!canvasElement) return;

    const ctx = canvasElement.getContext('2d');

    // Chart data
    const inventoryData = {
        labels: ['A+', 'O+', 'B+', 'AB+', 'A-', 'O-', 'B-', 'AB-'],
        datasets: [{
            label: 'Total Units in System',
            data: [1200, 1500, 1000, 800, 600, 950, 500, 400],
            backgroundColor: function(context) {
                const gradient = context.chart.ctx.createLinearGradient(0, 0, 0, 400);
                gradient.addColorStop(0, 'rgba(178,0,0,0.8)');
                gradient.addColorStop(1, 'rgba(255,99,132,0.6)');
                return gradient;
            },
            borderColor: 'rgba(178,0,0,1)',
            borderWidth: 1,
            borderRadius: 6,
            hoverBackgroundColor: 'rgba(178,0,0,1)'
        }]
    };

    // Chart configuration
    const config = {
        type: 'bar',
        data: inventoryData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(139,0,0,0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    cornerRadius: 6,
                    padding: 10
                },
                title: {
                    display: true,
                    text: 'System-Wide Inventory by Blood Type',
                    color: '#8b0000',
                    font: { size: 18, weight: '600' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Total Units',
                        color: '#8b0000',
                        font: { size: 14, weight: '600' }
                    },
                    ticks: { stepSize: 500 },
                    grid: { color: 'rgba(178,0,0,0.1)' }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Blood Type',
                        color: '#8b0000',
                        font: { size: 14, weight: '600' }
                    },
                    grid: { display: false }
                }
            }
        }
    };

    // Render chart
    new Chart(ctx, config);

});
