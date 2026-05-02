$(document).ready(function() {
    // --- Configuration & Security ---
    const token = localStorage.getItem('token');
    const backendUrl = 'http://127.0.0.1:5000';
    let userRole = null; // To store the user's role
    let currentInventoryId = null; // To track which item is being requested

    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    // --- API Fetch Utility ---
    async function fetchData(url, options = {}) {
        const response = await fetch(`${backendUrl}${url}`, {
            ...options,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        if (response.status === 401) {
            localStorage.removeItem('token');
            window.location.href = 'login.html';
            throw new Error('Unauthorized');
        }
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        return data;
    }

    // --- Toast Notification Utility ---
    function showToast(title, message, type = 'info') {
        const toastHtml = `<div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="5000"><div class="toast-header"><strong class="mr-auto text-${type}">${title}</strong><button type="button" class="ml-2 mb-1 close" data-dismiss="toast">&times;</button></div><div class="toast-body">${message}</div></div>`;
        $('.toast-container').append(toastHtml);
        $('.toast:last').toast('show').on('hidden.bs.toast', function () { $(this).remove(); });
    }

    // --- Load All Initial Data ---
    async function loadInitialData() {
        try {
            // Fetch all data in parallel for speed
            const [profileData, marketData, transactionData] = await Promise.all([
                fetchData('/api/users/profile'),
                fetchData('/api/marketplace/'),
                fetchData('/api/transactions/')
            ]);

            // 1. Populate Profile & Stats
            $('#my-credits').text(profileData.credits || 0);
            $('#profile-name').text(profileData.name || 'N/A');
            $('#profile-credits-modal').text(profileData.credits || 0);
            userRole = profileData.role;
            setDashboardLink(userRole);

            // 2. Populate Marketplace Table
            renderMarketplaceTable(marketData);

            // 3. Populate Transactions Table
            renderTransactionTable(transactionData);

            // 4. Populate other stats (Mocked for now, as we need a request-fetching endpoint)
            $('#my-open-requests').text(0); // This would be from '/api/requests'

        } catch (error) {
            console.error('Error loading data:', error);
            showToast('Error', 'Failed to load page data. Please refresh.', 'danger');
        }
    }

    // --- Render Functions ---
    function renderMarketplaceTable(listings) {
        const tableBody = $('#market-table tbody');
        tableBody.empty();
        let totalUnits = 0;

        if (listings && listings.length > 0) {
            listings.forEach(item => {
                const row = `<tr>
                    <td>${item.bank_name}</td>
                    <td>${item.blood_type}</td>
                    <td>${item.available_units}</td>
                    <td>${item.credits_per_unit}</td>
                    <td><button class="btn btn-sm btn-success btn-request" 
                                data-toggle="modal" 
                                data-target="#requestConfirmModal" 
                                data-inventory-id="${item.inventory_id}" 
                                data-bank="${item.bank_name}" 
                                data-blood="${item.blood_type}" 
                                data-units="${item.available_units}" 
                                data-credits="${item.credits_per_unit}">
                            Request
                        </button>
                    </td>
                </tr>`;
                tableBody.append(row);
                totalUnits += item.available_units;
            });
        } else {
            tableBody.append('<tr><td colspan="5" class="text-center p-3 text-muted">No blood units currently available on the marketplace.</td></tr>');
        }
        $('#market-total-units').text(totalUnits);
    }

    function renderTransactionTable(transactions) {
        const tableBody = $('#transactions-tbody');
        tableBody.empty();
        if (transactions && transactions.length > 0) {
            transactions.forEach(tx => {
                const txDate = new Date(tx.date).toLocaleDateString('en-GB');
                const fromClass = tx.from === "My Bank" ? "text-danger font-weight-bold" : "";
                const toClass = tx.to === "My Bank" ? "text-success font-weight-bold" : "";
                const row = `<tr>
                    <td class="${fromClass}">${tx.from}</td>
                    <td class="${toClass}">${tx.to}</td>
                    <td>${tx.type}</td>
                    <td>${tx.units}</td>
                    <td>${tx.credits}</td>
                    <td>${txDate}</td>
                </tr>`;
                tableBody.append(row);
            });
        } else {
            tableBody.append('<tr><td colspan="6" class="text-center p-3 text-muted">No transactions found.</td></tr>');
        }
    }

    // --- Helper to set the "Back to Dashboard" link ---
    function setDashboardLink(role) {
        let link = 'login.html'; // Default fallback
        if (role === 'hospital') link = 'hospital.html';
        else if (role === 'bank') link = 'bank.html';
        else if (role === 'admin') link = 'admin.html';
        $('#back-to-dashboard').attr('href', link);
    }

    // --- EVENT LISTENERS ---

    // Logout
    $('#logout-btn').on('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        showToast('Logged Out', 'You have been logged out successfully.', 'info');
        setTimeout(() => window.location.href = 'login.html', 1500);
    });

    // Marketplace Filters
    function filterMarketplace() {
        const bankName = $('#filter-bank-name').val().toLowerCase();
        const bloodType = $('#filter-blood-type').val();
        $("#market-table tbody tr").filter(function() {
            const rowBank = $(this).children('td:first').text().toLowerCase();
            const rowBlood = $(this).children('td:nth-child(2)').text();
            const bankMatch = rowBank.indexOf(bankName) > -1;
            const bloodMatch = bloodType === "" || rowBlood === bloodType;
            $(this).toggle(bankMatch && bloodMatch);
        });
    }
    $('#filter-bank-name').on("keyup", filterMarketplace);
    $('#filter-blood-type').on("change", filterMarketplace);

    // "Post Offer" form
    $('#post-offer-btn').on('click', async function() {
        const bloodType = $('#offer-blood-type').val();
        const units = parseInt($('#offer-units').val());
        const credits = parseInt($('#offer-credits').val());

        if (!units || units <= 0 || !credits || credits <= 0) {
            showToast('Error', 'Please enter valid units and credits.', 'danger');
            return;
        }

        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> Posting...');
        
        try {
            // This API call adds/updates the bank's own inventory
            const data = await fetchData('/api/inventory/', {
                method: 'POST',
                body: JSON.stringify({ blood_type: bloodType, quantity: units })
            });
            showToast('Success', data.message, 'success');
            $('#offer-form')[0].reset();
            loadInitialData(); // Refresh all data on the page
        } catch (error) {
            showToast('Error', `Failed to post offer: ${error.message}`, 'danger');
        } finally {
            $(this).prop('disabled', false).html('Post Offer');
        }
    });

    // "Request" button in table (to open modal)
    $('#requestConfirmModal').on('show.bs.modal', function(event) {
        const button = $(event.relatedTarget);
        const bank = button.data('bank');
        const blood = button.data('blood');
        const maxUnits = button.data('units');
        const credits = button.data('credits');
        
        currentInventoryId = button.data('inventory-id'); // Store which item we are requesting

        const modal = $(this);
        modal.find('#modal-request-text').html(`Requesting <b>${blood}</b> from <b>${bank}</b>.<br>Credits per unit: <b>${credits}</b>.`);
        modal.find('#request-units').attr('max', maxUnits).val(1);
    });

    // "Confirm Request" button in modal
    $('#confirm-request-btn').on('click', async function() {
        const qty = parseInt($('#request-units').val());

        if (isNaN(qty) || qty <= 0) {
            showToast("Error", "Invalid quantity!", "danger");
            return;
        }
        
        $(this).prop('disabled', true).html('<span class="spinner-border spinner-border-sm"></span> Processing...');

        try {
            const data = await fetchData('/api/marketplace/request', {
                method: 'POST',
                body: JSON.stringify({ inventory_id: currentInventoryId, quantity: qty })
            });
            
            showToast("Success", data.message, "success");
            $('#requestConfirmModal').modal('hide');
            loadInitialData(); // Refresh all data on the page
            
        } catch (error) {
            showToast("Error", `Request failed: ${error.message}`, "danger");
        } finally {
            $(this).prop('disabled', false).html('Confirm Request');
        }
    });

    // --- INITIAL PAGE LOAD ---
    loadInitialData();
});