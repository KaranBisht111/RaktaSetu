document.addEventListener('DOMContentLoaded', () => {

    const canvasElement = document.getElementById('bloodChart');
    if (!canvasElement) return; // Stop if canvas doesn't exist on page

    const ctx = canvasElement.getContext('2d');

    // Chart Data
    const bloodData = {
        labels: ['January', 'February', 'March', 'April', 'May', 'June'],
        datasets: [
            { label: 'A+', data: [50, 45, 40, 48, 52, 50], borderColor: 'rgba(178,0,0,1)', borderWidth: 2, fill: true, tension: 0.4, pointBackgroundColor: 'rgba(178,0,0,1)', pointRadius: 5 },
            { label: 'O+', data: [30, 28, 35, 33, 32, 30], borderColor: 'rgba(204,0,0,1)', borderWidth: 2, fill: true, tension: 0.4, pointBackgroundColor: 'rgba(204,0,0,1)', pointRadius: 5 },
            { label: 'B+', data: [20, 25, 22, 24, 23, 20], borderColor: 'rgba(255,99,132,1)', borderWidth: 2, fill: true, tension: 0.4, pointBackgroundColor: 'rgba(255,99,132,1)', pointRadius: 5 }
        ]
    };

    // Gradient background under lines
    bloodData.datasets.forEach(dataset => {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, dataset.borderColor.replace('1)', '0.4)'));
        gradient.addColorStop(1, dataset.borderColor.replace('1)', '0.05)'));
        dataset.backgroundColor = gradient;
    });

    // Chart Configuration
    const config = {
        type: 'line',
        data: bloodData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { color: '#8b0000', font: { weight: '600' } } },
                tooltip: { backgroundColor: 'rgba(139,0,0,0.9)', titleColor: '#fff', bodyColor: '#fff', cornerRadius: 6, padding: 10 },
                title: { display: true, text: 'Blood Units Trend (Last 6 Months)', color: '#8b0000', font: { size: 18, weight: '600' } }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Units Available', color: '#8b0000', font: { size: 14, weight: '600' } }, ticks: { stepSize: 10 }, grid: { color: 'rgba(139,0,0,0.1)' } },
                x: { title: { display: true, text: 'Month', color: '#8b0000', font: { size: 14, weight: '600' } }, grid: { display: false } }
            }
        }
    };

    new Chart(ctx, config); // Render chart
});
