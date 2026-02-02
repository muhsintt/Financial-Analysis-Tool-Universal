// API Configuration
const API_URL = `${window.location.protocol}//${window.location.host}/api`;
console.log('API_URL:', API_URL);

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
    charts: {},
    sortConfig: {
        field: 'date',
        direction: 'desc'
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOMContentLoaded event fired');
    // Initialize month picker with current month
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    document.getElementById('monthPicker').value = `${year}-${month}`;
    
    console.log('Initializing event listeners...');
    initializeEventListeners();
    console.log('Initializing categories...');
    await initializeCategories();
    console.log('Loading dashboard...');
    await loadDashboard();
    console.log('Page initialized');
});

// Event Listeners
function initializeEventListeners() {
    // Navigation
    console.log('Setting up navigation event listeners...');
    const navLinks = document.querySelectorAll('.nav-link');
    console.log('Found nav links:', navLinks.length);
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            console.log('Nav link clicked:', page);
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

    // Rules
    document.getElementById('addRuleBtn').addEventListener('click', () => {
        document.getElementById('ruleForm').reset();
        delete document.getElementById('ruleForm').dataset.ruleId;
        document.getElementById('ruleModalTitle').textContent = 'Add Categorization Rule';
        openModal('ruleModal');
    });

    document.getElementById('ruleForm').addEventListener('submit', handleRuleSubmit);
    document.getElementById('ruleTestInput').addEventListener('input', testRule);

    // API Status Toggle
    const apiToggle = document.getElementById('apiToggle');
    if (apiToggle) {
        apiToggle.addEventListener('change', handleApiToggle);
    }

    // Filters
    document.getElementById('typeFilter').addEventListener('change', loadTransactions);
    document.getElementById('categoryFilter').addEventListener('change', loadTransactions);
    document.getElementById('statusFilter').addEventListener('change', loadTransactions);
    document.getElementById('budgetTypeFilter').addEventListener('change', loadBudgets);

    // Search
    document.getElementById('searchInput').addEventListener('input', filterTransactions);

    // Bulk delete by selection
    document.getElementById('bulkDeleteFileBtn').addEventListener('click', () => {
        document.getElementById('bulkDeleteFile').click();
    });

    document.getElementById('bulkDeleteFile').addEventListener('change', handleBulkDeleteFileUpload);

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
    console.log('Navigating to:', page);
    
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
        'rules': 'Categorization Rules',
        'upload': 'Upload Bank Statement',
        'settings': 'Settings'
    };
    document.getElementById('pageTitle').textContent = titles[page] || 'Dashboard';

    // Show/hide pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const pageElement = document.getElementById(page);
    if (pageElement) {
        pageElement.classList.add('active');
        console.log('Page element found and activated:', page);
    } else {
        console.error('Page element not found:', page);
        return;
    }

    state.currentPage = page;

    // Load page content
    switch(page) {
        case 'transactions':
            loadTransactions();
            break;
        case 'budgets':
            loadBudgets();
            break;
        case 'rules':
            loadRules();
            break;
        case 'reports':
            loadReports();
            break;
        case 'settings':
            loadApiStatus();
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

        // Update category breakdown tables
        updateCategoryBreakdown(expenseData, incomeData);

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

// Update Category Breakdown Tables
function updateCategoryBreakdown(expenseData, incomeData) {
    // Update Income by Category table
    const incomeBody = document.getElementById('incomeByCategory');
    if (incomeBody && incomeData.categories.length > 0) {
        const totalIncome = incomeData.categories.reduce((sum, cat) => sum + cat.amount, 0);
        incomeBody.innerHTML = incomeData.categories.map(cat => `
            <tr>
                <td>${cat.category}</td>
                <td>${formatCurrency(cat.amount)}</td>
                <td>${cat.count}</td>
                <td>${((cat.amount / totalIncome) * 100).toFixed(1)}%</td>
            </tr>
        `).join('');
    }

    // Update Expenses by Category table
    const expenseBody = document.getElementById('expenseByCategory');
    if (expenseBody && expenseData.categories.length > 0) {
        const totalExpense = expenseData.categories.reduce((sum, cat) => sum + cat.amount, 0);
        expenseBody.innerHTML = expenseData.categories.map(cat => `
            <tr>
                <td>${cat.category}</td>
                <td>${formatCurrency(cat.amount)}</td>
                <td>${cat.count}</td>
                <td>${((cat.amount / totalExpense) * 100).toFixed(1)}%</td>
                <td>${formatCurrency(cat.amount / cat.count)}</td>
            </tr>
        `).join('');
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
        // Apply current sort configuration
        sortTransactions(state.sortConfig.field);
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

// Display Transactions
function displayTransactions(transactions) {
    const tbody = document.getElementById('transactionsBody');
    tbody.innerHTML = transactions.map(t => `
        <tr class="transaction-row" data-id="${t.id}">
            <td class="checkbox-col">
                <input type="checkbox" class="transaction-checkbox" value="${t.id}" onchange="updateBulkDeleteToolbar()">
            </td>
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

// Sort Transactions
function sortTransactions(field) {
    // Toggle direction if clicking the same field
    if (state.sortConfig.field === field) {
        state.sortConfig.direction = state.sortConfig.direction === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortConfig.field = field;
        state.sortConfig.direction = 'asc';
    }
    
    // Sort the transactions
    const sorted = [...state.transactions].sort((a, b) => {
        let valueA, valueB;
        
        switch(field) {
            case 'date':
                valueA = new Date(a.date);
                valueB = new Date(b.date);
                break;
            case 'description':
                valueA = a.description.toLowerCase();
                valueB = b.description.toLowerCase();
                break;
            case 'category':
                valueA = a.category_name.toLowerCase();
                valueB = b.category_name.toLowerCase();
                break;
            case 'type':
                valueA = a.type.toLowerCase();
                valueB = b.type.toLowerCase();
                break;
            case 'amount':
                valueA = a.amount;
                valueB = b.amount;
                break;
            case 'status':
                valueA = a.is_excluded ? 1 : 0;
                valueB = b.is_excluded ? 1 : 0;
                break;
            default:
                return 0;
        }
        
        if (valueA < valueB) return state.sortConfig.direction === 'asc' ? -1 : 1;
        if (valueA > valueB) return state.sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    // Update UI indicators
    document.querySelectorAll('table th.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (th.dataset.sortField === field) {
            th.classList.add(`sort-${state.sortConfig.direction}`);
        }
    });
    
    // Display sorted transactions
    displayTransactions(sorted);
}

// Filter Transactions
function filterTransactions() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filtered = state.transactions.filter(t => 
        t.description.toLowerCase().includes(searchTerm) ||
        t.category_name.toLowerCase().includes(searchTerm)
    );
    
    // Apply current sort to filtered results
    const sorted = [...filtered].sort((a, b) => {
        let valueA, valueB;
        
        switch(state.sortConfig.field) {
            case 'date':
                valueA = new Date(a.date);
                valueB = new Date(b.date);
                break;
            case 'description':
                valueA = a.description.toLowerCase();
                valueB = b.description.toLowerCase();
                break;
            case 'category':
                valueA = a.category_name.toLowerCase();
                valueB = b.category_name.toLowerCase();
                break;
            case 'type':
                valueA = a.type.toLowerCase();
                valueB = b.type.toLowerCase();
                break;
            case 'amount':
                valueA = a.amount;
                valueB = b.amount;
                break;
            case 'status':
                valueA = a.is_excluded ? 1 : 0;
                valueB = b.is_excluded ? 1 : 0;
                break;
            default:
                return 0;
        }
        
        if (valueA < valueB) return state.sortConfig.direction === 'asc' ? -1 : 1;
        if (valueA > valueB) return state.sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    displayTransactions(sorted);
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

// Toggle Select All checkbox
function toggleSelectAll(checked) {
    document.querySelectorAll('.transaction-checkbox').forEach(checkbox => {
        checkbox.checked = checked;
    });
    updateBulkDeleteToolbar();
}

// Update bulk delete toolbar visibility and count
function updateBulkDeleteToolbar() {
    const checkedBoxes = document.querySelectorAll('.transaction-checkbox:checked');
    const toolbar = document.getElementById('bulkDeleteToolbar');
    const count = checkedBoxes.length;
    
    if (count > 0) {
        toolbar.style.display = 'flex';
        document.getElementById('selectionCount').textContent = `${count} selected`;
        // Update select all checkbox state
        const allBoxes = document.querySelectorAll('.transaction-checkbox');
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');
        selectAllCheckbox.checked = checkedBoxes.length === allBoxes.length;
    } else {
        toolbar.style.display = 'none';
        document.getElementById('selectAllCheckbox').checked = false;
    }
}

// Bulk delete selected transactions
async function bulkDeleteSelected() {
    const checkedBoxes = document.querySelectorAll('.transaction-checkbox:checked');
    const ids = Array.from(checkedBoxes).map(cb => parseInt(cb.value));
    
    if (ids.length === 0) {
        alert('Please select transactions to delete');
        return;
    }
    
    const confirmed = confirm(`Are you sure you want to delete ${ids.length} transaction(s)? This cannot be undone.`);
    if (!confirmed) return;
    
    try {
        const response = await fetch(`${API_URL}/transactions/bulk-delete/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                transaction_ids: ids
            })
        });

        if (!response.ok) throw new Error('Failed to delete transactions');

        alert(`Successfully deleted ${ids.length} transaction(s)`);
        clearSelection();
        loadTransactions();
    } catch (error) {
        console.error('Error deleting transactions:', error);
        alert('Error deleting transactions');
    }
}

// Clear selection
function clearSelection() {
    document.querySelectorAll('.transaction-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    updateBulkDeleteToolbar();
}

// Handle file upload for bulk delete
async function handleBulkDeleteFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    try {
        const formData = new FormData();
        formData.append('file', file);

        // First, get a preview of transactions to be deleted
        const previewResponse = await fetch(`${API_URL}/transactions/bulk-delete-preview/`, {
            method: 'POST',
            body: formData
        });

        if (!previewResponse.ok) {
            const error = await previewResponse.json();
            throw new Error(error.error || 'Failed to preview transactions to delete');
        }

        const previewData = await previewResponse.json();
        
        // Store file for later confirmation
        window.pendingDeleteFile = file;
        window.pendingDeleteTransactions = previewData.transactions;
        
        // Show preview modal
        showBulkDeletePreview(previewData.transactions);
        
    } catch (error) {
        console.error('Error previewing transactions:', error);
        alert(`Error: ${error.message}`);
    } finally {
        // Reset file input
        document.getElementById('bulkDeleteFile').value = '';
    }
}

// Show bulk delete preview in modal
function showBulkDeletePreview(transactions) {
    const count = transactions.length;
    document.getElementById('previewCount').textContent = `${count} transaction(s) will be deleted:`;
    
    const previewDiv = document.getElementById('previewTransactions');
    previewDiv.innerHTML = transactions.map(t => `
        <div style="padding: 10px; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <div style="font-weight: 600;">${t.description}</div>
                <div style="font-size: 12px; color: #666;">
                    ${formatDate(t.date)} • ${t.category_name}
                </div>
            </div>
            <div style="text-align: right; font-weight: 600; color: ${t.type === 'income' ? 'var(--income)' : 'var(--expense)'};">
                ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
            </div>
        </div>
    `).join('');
    
    openModal('bulkDeletePreviewModal');
}

// Confirm bulk delete from file
async function confirmBulkDeleteFromFile() {
    if (!window.pendingDeleteFile) {
        alert('No file pending deletion');
        return;
    }
    
    const confirmed = confirm(`Are you sure you want to permanently delete ${window.pendingDeleteTransactions.length} transaction(s)? This cannot be undone.`);
    if (!confirmed) return;
    
    try {
        const formData = new FormData();
        formData.append('file', window.pendingDeleteFile);
        
        const response = await fetch(`${API_URL}/transactions/bulk-delete-by-file/`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete transactions from file');
        }

        const result = await response.json();
        alert(`Successfully deleted ${result.deleted_count} transaction(s) from file`);
        
        // Clear pending data
        window.pendingDeleteFile = null;
        window.pendingDeleteTransactions = null;
        
        // Close modal and reload
        closeModal('bulkDeletePreviewModal');
        loadTransactions();
    } catch (error) {
        console.error('Error deleting transactions from file:', error);
        alert(`Error: ${error.message}`);
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

// ============ CATEGORIZATION RULES ============

// Load Rules
async function loadRules() {
    if (state.currentPage !== 'rules') return;
    
    try {
        const response = await fetch(`${API_URL}/rules/`);
        if (!response.ok) throw new Error('Failed to load rules');
        
        const rules = await response.json();
        displayRules(rules);
    } catch (error) {
        console.error('Error loading rules:', error);
    }
}

// Display Rules
function displayRules(rules) {
    const tbody = document.getElementById('rulesBody');
    tbody.innerHTML = rules.map(r => `
        <tr>
            <td><strong>${r.name}</strong></td>
            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">${r.keywords}</td>
            <td>${r.category_name}</td>
            <td>${r.priority}</td>
            <td>
                <span class="rule-status ${r.is_active ? 'active' : 'inactive'}">
                    ${r.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <div class="actions">
                    <button class="btn-icon edit" title="Edit" onclick="editRule(${r.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon delete" title="Delete" onclick="deleteRule(${r.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Edit Rule
async function editRule(id) {
    try {
        const response = await fetch(`${API_URL}/rules/${id}`);
        if (!response.ok) throw new Error('Failed to load rule');
        
        const rule = await response.json();
        
        // Populate form
        document.getElementById('ruleName').value = rule.name;
        document.getElementById('ruleKeywords').value = rule.keywords;
        document.getElementById('ruleCategory').value = rule.category_id;
        document.getElementById('rulePriority').value = rule.priority;
        document.getElementById('ruleActive').checked = rule.is_active;
        
        // Update form to edit mode
        document.getElementById('ruleModalTitle').textContent = 'Edit Categorization Rule';
        document.getElementById('ruleForm').dataset.ruleId = id;
        
        openModal('ruleModal');
    } catch (error) {
        console.error('Error loading rule:', error);
        alert('Failed to load rule');
    }
}

// Delete Rule
async function deleteRule(id) {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    
    try {
        const response = await fetch(`${API_URL}/rules/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete rule');
        
        loadRules();
    } catch (error) {
        console.error('Error deleting rule:', error);
        alert('Failed to delete rule');
    }
}

// Handle Rule Submit
async function handleRuleSubmit(e) {
    e.preventDefault();
    
    const name = document.getElementById('ruleName').value.trim();
    const keywords = document.getElementById('ruleKeywords').value.trim();
    const category_id = parseInt(document.getElementById('ruleCategory').value);
    const priority = parseInt(document.getElementById('rulePriority').value);
    const is_active = document.getElementById('ruleActive').checked;
    const ruleId = document.getElementById('ruleForm').dataset.ruleId;
    
    if (!name || !keywords || !category_id) {
        alert('Please fill all required fields');
        return;
    }
    
    try {
        const url = ruleId ? 
            `${API_URL}/rules/${ruleId}` :
            `${API_URL}/rules/`;
        
        const method = ruleId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                keywords,
                category_id,
                priority,
                is_active
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save rule');
        }
        
        closeModal('ruleModal');
        delete document.getElementById('ruleForm').dataset.ruleId;
        document.getElementById('ruleForm').reset();
        document.getElementById('ruleModalTitle').textContent = 'Add Categorization Rule';
        
        loadRules();
    } catch (error) {
        console.error('Error saving rule:', error);
        alert(error.message);
    }
}

// Test Rule
async function testRule() {
    const testInput = document.getElementById('ruleTestInput').value.trim();
    if (!testInput) return;
    
    try {
        const response = await fetch(`${API_URL}/rules/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: testInput
            })
        });
        
        if (!response.ok) throw new Error('Test failed');
        
        const result = await response.json();
        const resultDiv = document.getElementById('ruleTestResult');
        
        if (result.primary_match) {
            resultDiv.innerHTML = `
                <div style="padding: 10px; background: #d4edda; border-radius: 4px; color: #155724;">
                    <strong>Match Found!</strong><br>
                    Rule: ${result.primary_match.rule_name}<br>
                    Category: ${result.primary_match.category_name}<br>
                    Priority: ${result.primary_match.priority}
                </div>

// API Status Management
async function loadApiStatus() {
    try {
        const response = await fetch(`${API_URL}/status/`);
        if (!response.ok) throw new Error('Failed to load API status');
        
        const status = await response.json();
        updateApiStatusDisplay(status);
        
        // Set up auto-refresh every 5 seconds
        if (window.statusRefreshInterval) {
            clearInterval(window.statusRefreshInterval);
        }
        window.statusRefreshInterval = setInterval(async () => {
            const refreshResponse = await fetch(`${API_URL}/status/`);
            if (refreshResponse.ok) {
                const refreshStatus = await refreshResponse.json();
                updateApiStatusDisplay(refreshStatus);
            }
        }, 5000);
    } catch (error) {
        console.error('Error loading API status:', error);
        document.getElementById('statusBadge').textContent = 'Error loading status';
    }
}

function updateApiStatusDisplay(status) {
    const statusBadge = document.getElementById('statusBadge');
    const apiToggle = document.getElementById('apiToggle');
    const statusDetails = document.getElementById('statusDetails');
    
    const isOnline = status.status === 'Online';
    
    // Update badge
    statusBadge.innerHTML = `<span class="status-badge ${isOnline ? 'online' : 'offline'}">${status.status}</span>`;
    
    // Update toggle
    apiToggle.checked = isOnline;
    
    // Update details
    const lastToggled = status.last_toggled 
        ? new Date(status.last_toggled).toLocaleString() 
        : 'Never';
    const toggledBy = status.toggled_by || 'System';
    
    statusDetails.innerHTML = `
        <div class="detail-row">
            <label>Status:</label>
            <span class="status-value">${status.status}</span>
        </div>
        <div class="detail-row">
            <label>Last Toggled:</label>
            <span class="status-value">${lastToggled}</span>
        </div>
        <div class="detail-row">
            <label>Toggled By:</label>
            <span class="status-value">${toggledBy}</span>
        </div>
    `;
}

async function handleApiToggle(event) {
    const isChecked = event.target.checked;
    const newStatus = isChecked ? 'online' : 'offline';
    const messageDiv = document.getElementById('toggleMessage');
    
    try {
        const response = await fetch(`${API_URL}/status/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                toggled_by: 'User'
            })
        });
        
        if (!response.ok) throw new Error('Failed to toggle API status');
        
        const result = await response.json();
        
        // Show success message
        messageDiv.innerHTML = `
            <div class="status-message success">
                API has been turned ${newStatus.toUpperCase()}
            </div>
        `;
        
        setTimeout(() => {
            messageDiv.innerHTML = '';
        }, 3000);
        
        // Reload status
        await loadApiStatus();
    } catch (error) {
        console.error('Error toggling API:', error);
        messageDiv.innerHTML = `
            <div class="status-message error">
                Failed to toggle API status
            </div>
        `;
    }
}
            `;
        } else {
            resultDiv.innerHTML = `
                <div style="padding: 10px; background: #f8d7da; border-radius: 4px; color: #721c24;">
                    No matching rules found. Would use default category.
                </div>
            `;
        }
        
        resultDiv.style.display = 'block';
    } catch (error) {
        console.error('Error testing rule:', error);
    }
}
