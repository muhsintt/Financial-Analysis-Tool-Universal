// API Configuration
const API_URL = 'http://localhost:5000/api';

// State Management
const state = {
    currentPage: 'dashboard',
    period: 'monthly',
    transactions: [],
    categories: [],
    budgets: [],
    filters: {
        category: null,
        type: null
    },
    currentTransaction: null,
    charts: {}
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize month picker with current month
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    document.getElementById('monthPicker').value = `${year}-${month}`;
    
    initializeEventListeners();
    await initializeCategories();
    await loadDashboard();
});

// Event Listeners
function initializeEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            navigateTo(page);
        });
    });

    // Period selector
    document.getElementById('periodSelect').addEventListener('change', (e) => {
        state.period = e.target.value;
        loadDashboard();
    });

    document.getElementById('monthPicker').addEventListener('change', (e) => {
        loadDashboard();
    });

    // Transaction modal
    document.getElementById('addTransBtn').addEventListener('click', () => {
        state.currentTransaction = null;
        openModal('transactionModal');
    });

    document.getElementById('transactionForm').addEventListener('submit', handleTransactionSubmit);

    // Budget modal
    document.getElementById('addBudgetBtn').addEventListener('click', () => {
        openModal('budgetModal');
    });

    document.getElementById('budgetForm').addEventListener('submit', handleBudgetSubmit);

    // Filters
    document.getElementById('typeFilter').addEventListener('change', loadTransactions);
    document.getElementById('categoryFilter').addEventListener('change', loadTransactions);
    document.getElementById('statusFilter').addEventListener('change', loadTransactions);
    document.getElementById('budgetTypeFilter').addEventListener('change', loadBudgets);

    // Search
    document.getElementById('searchInput').addEventListener('input', filterTransactions);

    // Upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#27ae60';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#3498db';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        handleFileSelect(e.dataTransfer.files);
    });

    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => handleFileSelect(e.target.files));

    document.getElementById('confirmUploadBtn').addEventListener('click', confirmUpload);
    document.getElementById('cancelUploadBtn').addEventListener('click', () => {
        document.getElementById('uploadPreview').style.display = 'none';
        fileInput.value = '';
    });

    // Modal close buttons
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.modal').classList.remove('show');
        });
    });

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('show');
        }
    });

    // Menu toggle
    document.getElementById('menuToggle').addEventListener('click', () => {
        document.querySelector('.sidebar').classList.toggle('show');
    });
}

// Navigation
function navigateTo(page) {
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === page) {
            link.classList.add('active');
        }
    });

    // Update page title
    const titles = {
        'dashboard': 'Dashboard',
        'transactions': 'Transactions',
        'budgets': 'Budgets',
        'reports': 'Reports',
        'upload': 'Upload Bank Statement'
    };
    document.getElementById('pageTitle').textContent = titles[page] || 'Dashboard';

    // Show/hide pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(page).classList.add('active');

    state.currentPage = page;

    // Load page content
    switch(page) {
        case 'transactions':
            loadTransactions();
            break;
        case 'budgets':
            loadBudgets();
            break;
        case 'reports':
            loadReports();
            break;
    }
}

// Initialize Categories
async function initializeCategories() {
    try {
        const response = await fetch(`${API_URL}/categories/init`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to initialize categories');
        
        await loadCategories();
    } catch (error) {
        console.error('Error initializing categories:', error);
    }
}

// Load Categories
async function loadCategories() {
    try {
        const response = await fetch(`${API_URL}/categories/`);
        if (!response.ok) throw new Error('Failed to load categories');
        
        state.categories = await response.json();
        
        // Update category filters
        const categoryFilters = ['categoryFilter', 'transCategory', 'budgetCategory', 'budgetTypeFilter'];
        categoryFilters.forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                const currentValue = filter.value;
                filter.innerHTML = '<option value="">Select...</option>';
                
                const categories = filterId.includes('Budget') ? 
                    state.categories.filter(c => c.type === 'expense') : 
                    state.categories;
                
                categories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.id;
                    option.textContent = cat.name;
                    filter.appendChild(option);
                });
                
                filter.value = currentValue;
            }
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Load Dashboard
async function loadDashboard() {
    if (state.currentPage !== 'dashboard') return;

    try {
        const period = state.period;
        const params = new URLSearchParams({ period, include_excluded: false });
        
        // Add year and month if period is monthly
        if (period === 'monthly') {
            const monthPicker = document.getElementById('monthPicker');
            if (monthPicker && monthPicker.value) {
                const [year, month] = monthPicker.value.split('-');
                params.append('year', year);
                params.append('month', month);
            }
        }
        
        // Load summary
        const summaryResponse = await fetch(`${API_URL}/reports/summary?${params}`);
        const summary = await summaryResponse.json();

        document.getElementById('totalIncome').textContent = formatCurrency(summary.total_income);
        document.getElementById('totalExpense').textContent = formatCurrency(summary.total_expense);
        document.getElementById('netBalance').textContent = formatCurrency(summary.net);

        // Load category breakdowns
        const [expenseResponse, incomeResponse] = await Promise.all([
            fetch(`${API_URL}/reports/by-category?${params}&type=expense`),
            fetch(`${API_URL}/reports/by-category?${params}&type=income`)
        ]);

        const expenseData = await expenseResponse.json();
        const incomeData = await incomeResponse.json();

        // Update charts
        updateCategoryCharts(expenseData, incomeData);

        // Load recent transactions
        const transResponse = await fetch(`${API_URL}/transactions/?include_excluded=false`);
        const transactions = await transResponse.json();
        
        const recentList = document.getElementById('recentTransList');
        recentList.innerHTML = transactions.slice(0, 5).map(t => `
            <div class="transaction-item ${t.type}">
                <div class="trans-info">
                    <div class="trans-desc">${t.description}</div>
                    <div class="trans-cat">${t.category_name} • ${formatDate(t.date)}</div>
                </div>
                <div class="trans-amount ${t.type}">
                    ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Update Category Charts
function updateCategoryCharts(expenseData, incomeData) {
    const chartColors = ['#3498db', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22'];

    // Destroy existing charts
    if (state.charts.expense) state.charts.expense.destroy();
    if (state.charts.income) state.charts.income.destroy();

    // Expense Chart
    const expenseCtx = document.getElementById('expenseChart');
    if (expenseCtx && expenseData.categories.length > 0) {
        state.charts.expense = new Chart(expenseCtx, {
            type: 'doughnut',
            data: {
                labels: expenseData.categories.map(c => c.category),
                datasets: [{
                    data: expenseData.categories.map(c => c.amount),
                    backgroundColor: chartColors,
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Income Chart
    const incomeCtx = document.getElementById('incomeChart');
    if (incomeCtx && incomeData.categories.length > 0) {
        state.charts.income = new Chart(incomeCtx, {
            type: 'doughnut',
            data: {
                labels: incomeData.categories.map(c => c.category),
                datasets: [{
                    data: incomeData.categories.map(c => c.amount),
                    backgroundColor: chartColors,
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Load Transactions
async function loadTransactions() {
    try {
        const typeFilter = document.getElementById('typeFilter').value;
        const categoryFilter = document.getElementById('categoryFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;

        const params = new URLSearchParams({
            include_excluded: true
        });

        if (typeFilter) params.append('type', typeFilter);
        if (categoryFilter) params.append('category_id', categoryFilter);

        const response = await fetch(`${API_URL}/transactions/?${params}`);
        if (!response.ok) throw new Error('Failed to load transactions');

        let transactions = await response.json();
        
        // Filter by status (included/excluded)
        if (statusFilter === 'included') {
            transactions = transactions.filter(t => !t.is_excluded);
        } else if (statusFilter === 'excluded') {
            transactions = transactions.filter(t => t.is_excluded);
        }
        
        state.transactions = transactions;
        displayTransactions(state.transactions);
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

// Display Transactions
function displayTransactions(transactions) {
    const tbody = document.getElementById('transactionsBody');
    tbody.innerHTML = transactions.map(t => `
        <tr>
            <td>${formatDate(t.date)}</td>
            <td>${t.description}</td>
            <td>${t.category_name}</td>
            <td><span class="tag ${t.type}">${t.type}</span></td>
            <td class="trans-amount ${t.type}">${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}</td>
            <td>
                <select class="status-select" onchange="updateTransactionStatus(${t.id}, this.value)">
                    <option value="false" ${!t.is_excluded ? 'selected' : ''}>Included</option>
                    <option value="true" ${t.is_excluded ? 'selected' : ''}>Excluded</option>
                </select>
            </td>
            <td>
                <div class="actions">
                    <button class="btn-icon edit" title="Edit" onclick="editTransaction(${t.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon delete" title="Delete" onclick="deleteTransaction(${t.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Filter Transactions
function filterTransactions() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filtered = state.transactions.filter(t => 
        t.description.toLowerCase().includes(searchTerm) ||
        t.category_name.toLowerCase().includes(searchTerm)
    );
    displayTransactions(filtered);
}

// Handle Transaction Submit
async function handleTransactionSubmit(e) {
    e.preventDefault();

    const date = document.getElementById('transDate').value;
    const description = document.getElementById('transDesc').value;
    const type = document.getElementById('transType').value;
    const categoryId = parseInt(document.getElementById('transCategory').value);
    const amount = parseFloat(document.getElementById('transAmount').value);
    const notes = document.getElementById('transNotes').value;

    if (!date || !description || !type || !categoryId || !amount) {
        alert('Please fill all required fields');
        return;
    }

    try {
        const url = state.currentTransaction ? 
            `${API_URL}/transactions/${state.currentTransaction.id}` :
            `${API_URL}/transactions/`;
        
        const method = state.currentTransaction ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date,
                description,
                type,
                category_id: categoryId,
                amount,
                notes
            })
        });

        if (!response.ok) throw new Error('Failed to save transaction');

        // Check if category changed on edit and prompt to apply to similar transactions
        if (state.currentTransaction && state.currentTransaction.category_id !== categoryId) {
            const similarTransactions = findSimilarTransactions(description, state.currentTransaction.id, categoryId);
            if (similarTransactions.length > 0) {
                const applyToAll = confirm(
                    `Found ${similarTransactions.length} similar transaction(s) with the same merchant.\n\n` +
                    `Would you like to apply this category to all of them?`
                );
                
                if (applyToAll) {
                    await applyBulkCategoryUpdate(similarTransactions.map(t => t.id), categoryId);
                }
            }
        }

        alert(state.currentTransaction ? 'Transaction updated!' : 'Transaction added!');
        document.getElementById('transactionModal').classList.remove('show');
        document.getElementById('transactionForm').reset();
        loadTransactions();
    } catch (error) {
        console.error('Error saving transaction:', error);
        alert('Error saving transaction');
    }
}

// Edit Transaction
async function editTransaction(id) {
    const trans = state.transactions.find(t => t.id === id);
    if (!trans) return;

    state.currentTransaction = trans;
    document.getElementById('modalTitle').textContent = 'Edit Transaction';
    document.getElementById('transDate').value = trans.date;
    document.getElementById('transDesc').value = trans.description;
    document.getElementById('transType').value = trans.type;
    document.getElementById('transCategory').value = trans.category_id;
    document.getElementById('transAmount').value = trans.amount;
    document.getElementById('transNotes').value = trans.notes || '';

    openModal('transactionModal');
}

// Delete Transaction
async function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) return;

    try {
        const response = await fetch(`${API_URL}/transactions/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete transaction');

        alert('Transaction deleted!');
        loadTransactions();
    } catch (error) {
        console.error('Error deleting transaction:', error);
        alert('Error deleting transaction');
    }
}

// Update Transaction Status (from dropdown)
async function updateTransactionStatus(id, status) {
    const isExcluded = status === 'true';
    try {
        const response = await fetch(`${API_URL}/transactions/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_excluded: isExcluded
            })
        });

        if (!response.ok) throw new Error('Failed to update transaction status');

        loadTransactions();
    } catch (error) {
        console.error('Error updating status:', error);
        alert('Error updating transaction status');
    }
}

// Find similar transactions by merchant/description
function findSimilarTransactions(description, excludeId, categoryId) {
    const normalizedDesc = description.toLowerCase().trim();
    const merchantName = extractMerchantName(normalizedDesc);
    
    return state.transactions.filter(t => {
        // Exclude the current transaction being edited
        if (t.id === excludeId) return false;
        
        // Only include transactions that don't already have this category
        if (t.category_id === categoryId) return false;
        
        // Match by merchant name
        const tMerchant = extractMerchantName(t.description.toLowerCase().trim());
        return tMerchant === merchantName && tMerchant.length > 0;
    });
}

// Extract merchant name from description (first word or meaningful part)
function extractMerchantName(description) {
    // Remove common prefixes like "DEBIT", "TRANSFER", "PAYMENT"
    const cleanDesc = description
        .replace(/^(debit|transfer|payment|check|ach|wire|atm|pos|purchase|transaction|ref:|memo:)\s*/gi, '')
        .trim();
    
    // Get first word or first meaningful part
    const words = cleanDesc.split(/[\s\-\/]/);
    const firstWord = words[0];
    
    // Return first word if it's substantial (not a number/date)
    if (firstWord && firstWord.length > 2 && !/^\d+$/.test(firstWord)) {
        return firstWord;
    }
    return '';
}

// Apply category to multiple transactions
async function applyBulkCategoryUpdate(transactionIds, categoryId) {
    try {
        const response = await fetch(`${API_URL}/transactions/bulk-update/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                transaction_ids: transactionIds,
                category_id: categoryId
            })
        });

        if (!response.ok) throw new Error('Failed to apply category to similar transactions');

        loadTransactions();
        alert(`Applied category to ${transactionIds.length} transaction(s)`);
    } catch (error) {
        console.error('Error applying bulk category update:', error);
        // Don't alert here since main transaction was already saved
    }
}

// Load Budgets
async function loadBudgets() {
    try {
        const response = await fetch(`${API_URL}/budgets/`);
        if (!response.ok) throw new Error('Failed to load budgets');

        state.budgets = await response.json();

        const grid = document.getElementById('budgetsGrid');
        if (state.budgets.length === 0) {
            grid.innerHTML = '<p>No budgets created yet. Create one to get started!</p>';
            return;
        }

        grid.innerHTML = state.budgets.map(b => `
            <div class="budget-card">
                <h4>${b.category_name}</h4>
                <div class="budget-info">
                    <div class="budget-row">
                        <label>Period:</label>
                        <span class="value">${b.period}</span>
                    </div>
                    <div class="budget-row">
                        <label>Budget:</label>
                        <span class="value">${formatCurrency(b.amount)}</span>
                    </div>
                    <div class="budget-row">
                        <label>Status:</label>
                        <span class="value">${b.for_excluded ? 'Excluded Only' : 'All Expenses'}</span>
                    </div>
                </div>
                <div class="budget-actions">
                    <button class="btn btn-secondary" onclick="editBudget(${b.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-danger" onclick="deleteBudget(${b.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading budgets:', error);
    }
}

// Handle Budget Submit
async function handleBudgetSubmit(e) {
    e.preventDefault();

    const categoryId = parseInt(document.getElementById('budgetCategory').value);
    const amount = parseFloat(document.getElementById('budgetAmount').value);
    const period = document.getElementById('budgetPeriod').value;
    const forExcluded = document.getElementById('budgetExcluded').checked;

    if (!categoryId || !amount || !period) {
        alert('Please fill all required fields');
        return;
    }

    try {
        const today = new Date();
        const response = await fetch(`${API_URL}/budgets/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category_id: categoryId,
                amount,
                period,
                year: today.getFullYear(),
                month: today.getMonth() + 1,
                for_excluded: forExcluded
            })
        });

        if (!response.ok) throw new Error('Failed to create budget');

        alert('Budget created!');
        document.getElementById('budgetModal').classList.remove('show');
        document.getElementById('budgetForm').reset();
        loadBudgets();
    } catch (error) {
        console.error('Error creating budget:', error);
        alert('Error creating budget');
    }
}

// Delete Budget
async function deleteBudget(id) {
    if (!confirm('Are you sure you want to delete this budget?')) return;

    try {
        const response = await fetch(`${API_URL}/budgets/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete budget');

        alert('Budget deleted!');
        loadBudgets();
    } catch (error) {
        console.error('Error deleting budget:', error);
    }
}

// Load Reports
async function loadReports() {
    try {
        const params = new URLSearchParams({
            period: state.period,
            include_excluded: false
        });

        // Load trending data
        const trendingResponse = await fetch(`${API_URL}/reports/trending?months=6&type=expense`);
        const trending = await trendingResponse.json();

        updateTrendingChart(trending);

        // Load budget analysis
        const budgetResponse = await fetch(`${API_URL}/reports/budget-analysis?${params}`);
        const budgetAnalysis = await budgetResponse.json();

        displayBudgetAnalysis(budgetAnalysis);

        // Load category breakdown
        const categoryResponse = await fetch(`${API_URL}/reports/by-category?${params}&type=expense`);
        const categoryData = await categoryResponse.json();

        displayCategoryBreakdown(categoryData);
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

// Update Trending Chart
function updateTrendingChart(data) {
    if (state.charts.trending) state.charts.trending.destroy();

    const ctx = document.getElementById('trendingChart');
    state.charts.trending = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.data.map(d => d.month),
            datasets: [{
                label: 'Monthly Expenses',
                data: data.data.map(d => d.amount),
                borderColor: '#e74c3c',
                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Display Budget Analysis
function displayBudgetAnalysis(data) {
    const container = document.getElementById('budgetAnalysisContainer');
    if (!data.budgets || data.budgets.length === 0) {
        container.innerHTML = '<p>No budgets to analyze</p>';
        return;
    }

    container.innerHTML = data.budgets.map(b => `
        <div class="category-row">
            <div>
                <div class="name">${b.category}</div>
                <div class="percent">${formatCurrency(b.actual)} / ${formatCurrency(b.budgeted)}</div>
            </div>
            <div style="flex: 1;">
                <div class="budget-progress">
                    <div class="progress-bar ${b.status === 'over' ? 'over' : ''}" style="width: ${Math.min(b.percentage, 100)}%"></div>
                </div>
            </div>
            <div class="amount" style="text-align: right;">
                <span class="tag ${b.status === 'over' ? 'expense' : ''}">${b.status === 'over' ? 'Over' : 'Under'}</span>
            </div>
        </div>
    `).join('');
}

// Display Category Breakdown
function displayCategoryBreakdown(data) {
    const container = document.getElementById('categoryBreakdown');
    if (!data.categories || data.categories.length === 0) {
        container.innerHTML = '<p>No expenses to display</p>';
        return;
    }

    container.innerHTML = data.categories.map(c => `
        <div class="category-row">
            <div class="name">${c.category}</div>
            <div>
                <span class="amount">${formatCurrency(c.amount)}</span>
                <span class="percent">(${c.percentage}%)</span>
            </div>
        </div>
    `).join('');
}

// File Upload Handling
let selectedFile = null;

async function handleFileSelect(files) {
    if (!files || files.length === 0) return;

    selectedFile = files[0];
    
    const allowedTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                          'application/vnd.ms-excel'];
    
    if (!allowedTypes.includes(selectedFile.type) && !selectedFile.name.endsWith('.csv') && 
        !selectedFile.name.endsWith('.xlsx') && !selectedFile.name.endsWith('.xls')) {
        alert('Please select a valid file (CSV, XLSX, or XLS)');
        return;
    }

    // Preview file
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch(`${API_URL}/uploads/preview`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Failed to preview file');

        const result = await response.json();
        displayPreview(result.preview);
        document.getElementById('uploadPreview').style.display = 'block';
    } catch (error) {
        console.error('Error previewing file:', error);
        alert('Error previewing file: ' + error.message);
    }
}

function displayPreview(data) {
    const tbody = document.getElementById('previewBody');
    tbody.innerHTML = data.map(row => `
        <tr>
            <td>${row.date}</td>
            <td>${row.description}</td>
            <td>${formatCurrency(row.amount)}</td>
            <td><span class="tag ${row.type}">${row.type}</span></td>
            <td>${row.category}</td>
        </tr>
    `).join('');
}

async function confirmUpload() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const statusDiv = document.getElementById('uploadStatus');
        statusDiv.className = 'upload-status loading';
        statusDiv.textContent = 'Uploading and processing...';
        statusDiv.style.display = 'block';

        const response = await fetch(`${API_URL}/uploads/upload`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Upload failed');
        }
        
        statusDiv.className = 'upload-status success';
        statusDiv.innerHTML = `
            <strong>Success!</strong><br>
            ${result.transactions_created} transactions imported successfully.
        `;

        document.getElementById('uploadPreview').style.display = 'none';
        document.getElementById('fileInput').value = '';
        selectedFile = null;

        setTimeout(() => {
            navigateTo('transactions');
            loadTransactions();
        }, 2000);
    } catch (error) {
        console.error('Error uploading file:', error);
        const statusDiv = document.getElementById('uploadStatus');
        statusDiv.className = 'upload-status error';
        statusDiv.textContent = 'Error uploading file: ' + error.message;
    }
}

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function openModal(modalId) {
    document.getElementById(modalId).classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}
