document.addEventListener('DOMContentLoaded', () => {

    // --- MAP INITIALIZATION ---
    // Centered on Navi Mumbai (project context)
    const map = L.map('donor-map').setView([19.0330, 73.0297], 12);

    // Stylish grayscale tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 19
    }).addTo(map);

    // --- MOCK DATA (replace with backend API in production) ---
    const donors = [
        {lat: 19.0213, lng: 73.0165, name: "John Doe", bloodType: "A+"},
        {lat: 19.0667, lng: 73.0076, name: "Priya Sharma", bloodType: "O-"},
        {lat: 19.0728, lng: 73.0028, name: "Rahul Kumar", bloodType: "B+"},
        {lat: 19.038, lng: 73.035, name: "Anjali Singh", bloodType: "AB+"}
    ];

    const hospitals = [
        {lat: 19.0213, lng: 73.0175, name: "Apollo Hospital", inventory: "O+: 5, A-: 2"},
        {lat: 19.065, lng: 73.0086, name: "MGM Hospital", inventory: "A+: 10, O-: 3"},
        {lat: 19.073, lng: 73.0038, name: "Fortis Hiranandani", inventory: "B-: 1, O+: 12"}
    ];

    // --- CUSTOM ICONS ---
    const donorIcon = L.divIcon({
        html: '<i class="fas fa-user"></i>',
        className: 'custom-div-icon donor-div-icon',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    const hospitalIcon = L.divIcon({
        html: '<i class="fas fa-hospital"></i>',
        className: 'custom-div-icon hospital-div-icon',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    // --- DONOR MARKERS (with clustering) ---
    const donorClusterGroup = L.markerClusterGroup();
    donors.forEach(donor => {
        const marker = L.marker([donor.lat, donor.lng], {icon: donorIcon})
            .bindPopup(`<strong>${donor.name}</strong><br>Blood Type: ${donor.bloodType}`);
        donorClusterGroup.addLayer(marker);
    });

    // --- HOSPITAL MARKERS ---
    const hospitalLayerGroup = L.layerGroup();
    hospitals.forEach(hospital => {
        L.marker([hospital.lat, hospital.lng], {icon: hospitalIcon})
            .bindPopup(`<strong>${hospital.name}</strong><br><small>Available: ${hospital.inventory} units</small>`)
            .addTo(hospitalLayerGroup);
    });

    // Add layers to the map
    map.addLayer(donorClusterGroup);
    map.addLayer(hospitalLayerGroup);

    // --- LAYER CONTROL ---
    L.control.layers(null, {
        "Donors": donorClusterGroup,
        "Hospitals": hospitalLayerGroup
    }, {collapsed: false}).addTo(map);

    // --- FIT MAP BOUNDS TO ALL MARKERS ---
    const allPoints = donors.concat(hospitals).map(p => [p.lat, p.lng]);
    if (allPoints.length > 0) {
        map.fitBounds(allPoints, {padding: [50, 50]});
    }

});
